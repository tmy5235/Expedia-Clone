"""Controller: two-stage LLM retrieval with safe provider failures and audit steps."""
from datetime import date, datetime
import hashlib
import json
import os
import re
from pathlib import Path
from threading import Lock
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from dotenv import load_dotenv

from app.chat_store import ChatStore, QueryRejected

ROOT = Path(__file__).resolve().parents[3]


class ChatError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


class Proposal(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    sql: str | None = Field(max_length=8000)
    params: dict[str, str | int | float | None] = Field(default_factory=dict, max_length=20)
    postcode: str | None = Field(default=None, pattern=r'^[0-9]{5}$')
    check_in: str | None = None
    check_out: str | None = None
    clarification: str | None = Field(default=None, max_length=1000)

    def stay(self) -> tuple[str, str, str, int]:
        try:
            start, end = date.fromisoformat(self.check_in), date.fromisoformat(self.check_out)
        except (TypeError, ValueError):
            raise QueryRejected('The model must specify valid check-in and checkout dates.') from None
        nights = (end - start).days
        if (not self.postcode or not 1 <= nights <= 14 or start.isoformat() != self.check_in
                or end.isoformat() != self.check_out):
            raise QueryRejected('Specify a five-digit ZIP and a stay of 1–14 nights.')
        for field in ('postcode', 'check_in', 'check_out'):
            if self.params.get(field) != getattr(self, field):
                raise QueryRejected('Query parameters must match the resolved ZIP and dates.')
        return self.postcode, self.check_in, self.check_out, nights


class OpenAIModel:
    def __init__(self):
        load_dotenv(ROOT / '.env', override=False)
        self.key = os.environ.get('OPENAI_API_KEY', '').strip() or os.environ.get('OPEN_AI', '').strip()
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4.1-mini').strip()
        self.mode = 'live OpenAI'

    @property
    def configured(self) -> bool:
        return bool(self.key and self.model)

    def complete(self, messages: list[dict], *, json_output: bool = False) -> str:
        if not self.configured:
            raise ChatError('Chat is not configured. Add OPENAI_API_KEY and OPENAI_MODEL to the project-root .env, then restart the backend.', 503)
        payload = {'model': self.model, 'messages': messages, 'max_completion_tokens': 2200,
                   'store': False}
        if json_output:
            payload['response_format'] = {'type': 'json_object'}
        try:
            with httpx.Client(timeout=httpx.Timeout(40, connect=10), follow_redirects=False) as client:
                response = client.post('https://api.openai.com/v1/chat/completions',
                    headers={'Authorization': f'Bearer {self.key}'}, json=payload)
            if response.status_code == 429:
                raise ChatError('The model provider rate or credit limit was reached. Check API credit or try later.', 429)
            if response.status_code in (401, 403):
                raise ChatError('The model provider rejected the backend credentials. Check the API key and model access.', 503)
            if not response.is_success:
                raise ChatError('The model provider request failed. Check the backend model setting and try again.')
            choice = response.json()['choices'][0]
            answer = choice['message']['content']
            if choice.get('finish_reason') != 'stop' or not isinstance(answer, str) or not answer.strip() or len(answer) > 16000:
                raise ChatError('The model returned an incomplete or invalid reply. Try a more focused question.')
            return answer.strip()
        except httpx.TimeoutException:
            raise ChatError('The model request timed out. Please try again.', 504) from None
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            raise ChatError('The model provider is unavailable or returned an invalid response.') from None


class ChatController:
    def __init__(self, store: ChatStore):
        self.store = store
        self.lock = Lock()  # Bound simultaneous paid calls in this classroom process.

    def start(self, model=None) -> None:
        self.prompt = (ROOT / 'prompts' / 'hotel-assistant.md').read_text()
        shared, query_and_answer = self.prompt.split('QUERY STAGE:', 1)
        query, answer = query_and_answer.split('ANSWER STAGE:', 1)
        self.query_prompt = shared + 'QUERY STAGE:' + query
        self.answer_prompt = shared + 'ANSWER STAGE:' + answer
        self.version = hashlib.sha256(self.prompt.encode()).hexdigest()[:16]
        self.model = model or OpenAIModel()

    def ask(self, question: str, conversation_id: str | None) -> dict:
        if not self.lock.acquire(blocking=False):
            raise ChatError('Another question is still processing. Please try again shortly.', 409)
        try:
            return self._ask(question, conversation_id)
        finally:
            self.lock.release()

    def _ask(self, question: str, conversation_id: str | None) -> dict:
        history = self.store.history(conversation_id) if conversation_id else []
        conversation_id = conversation_id or self.store.create(question)
        turn_id = str(uuid4())

        def record(role, stage, content):
            self.store.record(conversation_id, turn_id, role, stage, content, self.version)

        record('system', 'instructions', {'prompt': self.prompt, 'model': self.model.model,
                                         'mode': self.model.mode})
        record('user', 'question', question)

        def guidance(status: str, answer: str) -> dict:
            record('tool', 'preflight', {'status': status, 'model_requests': 0})
            record('assistant', 'answer', answer)
            return {'conversation_id': conversation_id, 'turn_id': turn_id, 'answer': answer,
                    'status': status, 'model': self.model.model, 'mode': 'local guidance — no model call',
                    'proposed_sql': None, 'executed_sql': None, 'params': {}, 'rows': [],
                    'records': [], 'prompt_version': self.version}

        catalog = self.store.catalog()
        if not catalog['hotel_count']:
            return guidance('needs_saved_hotels', 'No hotels have been saved yet.\n\n'
                '1. Enter a ZIP in Find hotels above.\n2. Choose Add to Local on the hotels you want to compare.\n'
                '3. Ask about those saved hotels with a ZIP and stay dates.\n\n'
                'The assistant compares your saved collection; '
                'the ZIP search above discovers nearby hotels.')
        # A date in the prompt examples or a previous assistant guess is not user consent.
        user_context = '\n'.join([row['content'] for row in history
            if row['stage'] == 'question'][-12:] + [question])
        months = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        date_terms = (r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[-/]\d{1,2}(?:[-/]\d{2}(?:\d{2})?)?|today|tomorrow|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
                      + rf'|\b{months}\.?\s+\d{{1,2}}\b|\b\d{{1,2}}\s+{months}\b')
        if not re.search(date_terms, user_context, re.I):
            return guidance('clarification', 'Which night or check-in and checkout dates should I compare? '
                'Please include the year and ZIP.\n\n'
                'Use one of the suggested questions below; its ZIP and dates come from your saved hotels. '
                'For nearby hotels, use Find hotels above.')
        try:
            context = [{'role': row['role'], 'content': row['content']} for row in history
                       if row['stage'] in ('question', 'answer')][-12:]
            messages = [{'role': 'system', 'content': self.query_prompt + '\nCurrent date in America/New_York: '
                         + datetime.now(ZoneInfo('America/New_York')).date().isoformat()},
                        *context, {'role': 'user', 'content': question}]
            record('system', 'query_request', {'messages': messages})
            raw = self.model.complete(messages, json_output=True)
            record('assistant', 'proposed_sql', raw)
            proposal = Proposal.model_validate_json(raw)
            if proposal.sql is None:
                if not proposal.clarification:
                    raise QueryRejected('The model did not provide a query or clarification.')
                records, rows, executed = [], [], None
                record('tool', 'clarification_needed', proposal.clarification)
            else:
                stay = proposal.stay()
                executed, rows, records = self.store.retrieve(proposal.sql, proposal.params, *stay)
                record('tool', 'executed_sql', {'sql': executed, 'params': proposal.params})
                record('tool', 'retrieval_result', {'rows': rows, 'records': records})
            evidence = {'question': question, 'resolved': proposal.model_dump(exclude={'sql', 'params'}),
                        'records': records, 'simulated_course_data': True}
            answer_messages = [{'role': 'system', 'content': self.answer_prompt},
                               {'role': 'user', 'content': json.dumps(evidence, ensure_ascii=False)}]
            record('system', 'answer_request', {'messages': answer_messages})
            answer = self.model.complete(answer_messages)
            try:
                unexpected = json.loads(answer)
            except ValueError:
                unexpected = None
            if isinstance(unexpected, dict) and 'sql' in unexpected:
                raise ChatError('The model returned a query instead of an answer. Please try again.')
            record('assistant', 'answer', answer)
            return {'conversation_id': conversation_id, 'turn_id': turn_id, 'answer': answer,
                    'status': 'clarification' if executed is None else 'matches' if records else 'no_matches',
                    'model': self.model.model, 'mode': self.model.mode,
                    'proposed_sql': proposal.sql, 'executed_sql': executed, 'params': proposal.params,
                    'rows': rows, 'records': records, 'prompt_version': self.version}
        except (QueryRejected, ValidationError) as error:
            detail = str(error) if isinstance(error, QueryRejected) else 'The model returned an invalid query proposal.'
            record('tool', 'validation_error', detail)
            feedback = 'I couldn’t complete that comparison. Try a suggested question with a saved ZIP and exact stay dates. Your saved hotels have not changed.'
            record('tool', 'error', feedback)
            raise ChatTurnError(feedback, 422, conversation_id) from None
        except ChatError as error:
            record('tool', 'error', str(error))
            raise ChatTurnError(str(error), error.status, conversation_id) from None


class ChatTurnError(ChatError):
    def __init__(self, message: str, status: int, conversation_id: str):
        super().__init__(message, status)
        self.conversation_id = conversation_id
