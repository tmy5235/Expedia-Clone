"""Thin routes for the shared local classroom assistant (separate from accounts)."""
from uuid import UUID

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.controllers.chat import ChatController, ChatError


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None

    @field_validator('question')
    @classmethod
    def nonempty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Enter a hotel question.')
        return value.strip()


def chat_router(controller: ChatController) -> APIRouter:
    router = APIRouter(prefix='/api/chat', tags=['Hotel assistant'])

    @router.get('/status')
    def status(response: Response) -> dict:
        response.headers['Cache-Control'] = 'no-store'
        return {'configured': controller.model.configured, 'model': controller.model.model,
                'mode': controller.model.mode, 'prompt_version': controller.version}

    @router.get('/catalog')
    def catalog(response: Response) -> dict:
        response.headers['Cache-Control'] = 'no-store'
        return controller.store.catalog()

    @router.get('/conversations')
    def conversations(response: Response) -> list[dict]:
        response.headers['Cache-Control'] = 'no-store'
        return controller.store.list()

    @router.get('/conversations/{conversation_id}')
    def history(conversation_id: UUID, response: Response) -> dict:
        response.headers['Cache-Control'] = 'no-store'
        return {'conversation_id': str(conversation_id), 'messages': controller.store.history(str(conversation_id))}

    @router.post('')
    def ask(body: ChatRequest, response: Response):
        response.headers['Cache-Control'] = 'no-store'
        try:
            return controller.ask(body.question, str(body.conversation_id) if body.conversation_id else None)
        except ChatError as error:
            return JSONResponse(status_code=error.status, headers={'Cache-Control': 'no-store'},
                content={'detail': str(error), 'conversation_id': getattr(error, 'conversation_id', None)})

    return router
