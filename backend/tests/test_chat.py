"""RAG tests: all SQLite data and provider responses are isolated fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import httpx
import pytest

from app.chat_store import ChatStore, QueryRejected
from app.controllers.chat import ChatError, OpenAIModel
from app.database import Database
from app.main import create_app

SQL = '''SELECT h.hotel_id, SUM(n.nightly_rate_cents) AS total_cents
FROM saved_hotels h JOIN saved_hotel_zips z ON h.hotel_id=z.hotel_id
JOIN demo_hotel_nights n ON h.hotel_id=n.hotel_id
WHERE z.postcode=:postcode AND n.stay_date>=:check_in AND n.stay_date<:check_out
GROUP BY h.hotel_id
HAVING COUNT(*)=julianday(:check_out)-julianday(:check_in) AND MIN(n.rooms_available)>=1
ORDER BY total_cents, h.hotel_id LIMIT 3'''
PLAN = {'sql': SQL, 'params': {'postcode': '16803', 'check_in': '2026-10-11', 'check_out': '2026-10-13'},
        'postcode': '16803', 'check_in': '2026-10-11', 'check_out': '2026-10-13', 'clarification': None}


class FakeModel:
    configured = True
    model = 'fixture-model-no-network'
    mode = 'MOCK — no live model calls'

    def __init__(self, plan=None, failure=None):
        self.plan = deepcopy(PLAN if plan is None else plan)
        self.failure = failure
        self.calls = []

    def complete(self, messages, *, json_output=False):
        self.calls.append(deepcopy(messages))
        if self.failure:
            raise self.failure
        if json_output:
            return json.dumps(self.plan)
        evidence = json.loads(messages[-1]['content'])
        if evidence['resolved'].get('clarification'):
            return 'Please provide the ZIP and dates. Simulated course data only.'
        records = evidence['records']
        if not records:
            return 'No matching complete available stay was found in the saved subset. Simulated course data only.'
        return 'MOCK ANSWER — Simulated course data. ' + '; '.join(
            f"{r['name'] or 'Name not provided'}: {r['check_in']} to {r['check_out']} (checkout excluded), "
            f"${r['total_cents']/100:.2f} total for {r['nights']} nights; "
            f"minimum {min(d['rooms_available'] for d in r['demo_nights'])} rooms. "
            + ', '.join(f"{d['stay_date']}: ${d['nightly_rate_cents']/100:.2f}" for d in r['demo_nights'])
            for r in records) + '. Cheapest complete stay first; these are not live offers.'


def seed_fixture(client, database):
    center = {'postcode': '16803', 'country_code': 'us', 'locality': 'Fictional Test Center',
              'latitude': 40.8, 'longitude': -77.86}
    for i, name in enumerate(['Fictional Pine Inn', 'Fictional Brook Hotel', 'Fictional Missing Night', 'Fictional Sold Out']):
        assert client.post('/api/local-hotels', json={'center': center,
            'hotel': {'place_id': f'fixture-{i}', 'name': name, 'address': 'Fictional test address',
                      'latitude': 40.801+i*.001, 'longitude': -77.86}}).status_code == 200
    with database.connect() as db:
        db.execute("UPDATE demo_hotel_nights SET nightly_rate_cents=8000 WHERE hotel_id='fixture-0'")
        db.execute("UPDATE demo_hotel_nights SET nightly_rate_cents=12000 WHERE hotel_id='fixture-0' AND stay_date='2026-10-12'")
        db.execute("UPDATE demo_hotel_nights SET nightly_rate_cents=9000 WHERE hotel_id='fixture-1'")
        db.execute("DELETE FROM demo_hotel_nights WHERE hotel_id='fixture-2' AND stay_date='2026-10-12'")
        db.execute("UPDATE demo_hotel_nights SET rooms_available=0 WHERE hotel_id='fixture-3' AND stay_date='2026-10-12'")


@pytest.fixture
def setup(tmp_path):
    database = Database(tmp_path/'rag.sqlite3')
    app = create_app(database.path)
    with TestClient(app) as client:
        model = FakeModel()
        app.state.chat.model = model
        seed_fixture(client, database)
        yield client, database, model, app


def snapshot(database):
    with database.connect() as db:
        return {name: [tuple(row) for row in db.execute(f'SELECT * FROM {name} ORDER BY rowid')]
                for name in ('hotels', 'trips', 'users', 'bookings', 'saved_hotels', 'saved_hotel_zips', 'demo_hotel_nights')}


def test_full_two_call_workflow_followup_and_persistence(setup):
    client, database, model, app = setup
    before = snapshot(database)
    result = client.post('/api/chat', json={'question': 'Three cheapest near 16803, October 11–13, 2026.'})
    assert result.status_code == 200, result.text
    reply = result.json()
    assert reply['status'] == 'matches'
    assert [row['total_cents'] for row in reply['records']] == [18000, 20000]
    assert [row['name'] for row in reply['records']] == ['Fictional Brook Hotel', 'Fictional Pine Inn']
    assert '$180.00' in reply['answer'] and '$200.00' in reply['answer']
    assert len(model.calls) == 2
    assert json.loads(model.calls[1][-1]['content'])['records'] == reply['records']
    conversation_id = reply['conversation_id']
    history = client.get(f'/api/chat/conversations/{conversation_id}').json()['messages']
    assert [m['stage'] for m in history] == ['instructions', 'question', 'query_request', 'proposed_sql',
        'executed_sql', 'retrieval_result', 'answer_request', 'answer']
    assert all(m['timestamp'] and m['prompt_version'] and m['turn_id'] for m in history)
    with TestClient(create_app(database.path)) as restarted:
        assert restarted.get(f'/api/chat/conversations/{conversation_id}').json()['messages'] == history
    follow = client.post('/api/chat', json={'question': 'What about that same stay? for October 11–13, 2026 near 16803', 'conversation_id': conversation_id})
    assert follow.status_code == 200
    assert any(m['content'] == reply['answer'] for m in model.calls[2])
    assert snapshot(database) == before


def test_no_matches_and_leading_zero_isolation(setup):
    client, _, model, _ = setup
    model.plan['postcode'] = model.plan['params']['postcode'] = '00501'
    reply = client.post('/api/chat', json={'question': 'Anything near 00501 October 11–13, 2026?'}).json()
    assert reply['status'] == 'no_matches' and reply['records'] == []
    assert len(model.calls) == 2 and 'No matching' in reply['answer']
    assert reply['params']['postcode'] == '00501'


def test_checkout_excluded_and_missing_nights_not_available(setup):
    client, _, model, _ = setup
    model.plan['check_out'] = model.plan['params']['check_out'] = '2026-10-12'
    reply = client.post('/api/chat', json={'question': 'One night October 11, 2026 near 16803?'}).json()
    assert reply['rows'][0]['total_cents'] == 8000
    assert all(len(r['demo_nights']) == 1 for r in reply['records'])
    model.plan['check_out'] = model.plan['params']['check_out'] = '2026-10-16'
    reply = client.post('/api/chat', json={'question': 'Stay through October 16?'}).json()
    assert reply['records'] == []


@pytest.mark.parametrize('sql', [
    'DELETE FROM saved_hotels', 'DROP TABLE saved_hotels', 'PRAGMA user_version',
    'ATTACH DATABASE "/tmp/evil.sqlite3" AS evil',
    'SELECT * FROM users', 'SELECT * FROM chat_messages', 'SELECT * FROM sqlite_master',
    'SELECT * FROM pragma_table_info("users")', 'SELECT load_extension("anything")',
    'SELECT readfile(".env")', 'SELECT randomblob(1000000000)',
    SQL+'; DELETE FROM saved_hotels', SQL+' --comment',
    'WITH RECURSIVE t(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM t) SELECT * FROM t',
    SQL.replace('h.hotel_id, SUM', '(SELECT password FROM users LIMIT 1) AS hotel_id, SUM'),
])
def test_disallowed_queries_cannot_read_private_data_or_write(setup, sql):
    client, database, model, _ = setup
    before = snapshot(database)
    model.plan['sql'] = sql
    reply = client.post('/api/chat', json={'question': 'Fixture malicious model proposal for October 11–13, 2026 near 16803'})
    assert reply.status_code == 422, reply.text
    assert len(model.calls) == 1  # No answer fabricated after failed retrieval.
    history = client.get('/api/chat/conversations/'+reply.json()['conversation_id']).json()['messages']
    assert history[-1]['stage'] == 'error'
    assert not any(m['stage'] == 'answer' for m in history)
    assert snapshot(database) == before


@pytest.mark.parametrize('replacement', ['SUM(n.nightly_rate_cents)+1', '0'])
def test_invented_totals_rejected(setup, replacement):
    client, _, model, _ = setup
    model.plan['sql'] = SQL.replace('SUM(n.nightly_rate_cents)', replacement)
    assert client.post('/api/chat', json={'question': 'Fixture incorrect total for October 11–13, 2026 near 16803'}).status_code == 422


def test_incomplete_and_wrong_zip_queries_rejected(setup):
    client, _, model, _ = setup
    model.plan['sql'] = SQL.replace('LIMIT 3', 'LIMIT 30').replace(
        'HAVING COUNT(*)=julianday(:check_out)-julianday(:check_in) AND MIN(n.rooms_available)>=1', '')
    assert client.post('/api/chat', json={'question': 'Fixture missing-night inclusion for October 11–13, 2026 near 16803'}).status_code == 422
    model.plan = deepcopy(PLAN)
    model.plan['postcode'] = model.plan['params']['postcode'] = '00501'
    model.plan['sql'] = SQL.replace('z.postcode=:postcode', "z.postcode='16803'")
    assert client.post('/api/chat', json={'question': 'Fixture wrong ZIP inclusion for October 11–13, 2026 near 16803'}).status_code == 422


def test_row_and_work_limits(setup):
    _, database, _, _ = setup
    store = ChatStore(database)
    repeat = ' UNION ALL '.join([SQL.replace('ORDER BY total_cents, h.hotel_id LIMIT 3', '')]*9)
    with pytest.raises(QueryRejected):
        store.retrieve(repeat, PLAN['params'], '16803', '2026-10-11', '2026-10-13', 2)
    expensive = '''SELECT h.hotel_id, sum(n.nightly_rate_cents) AS total_cents
        FROM saved_hotels h, saved_hotel_zips z, demo_hotel_nights n,
        demo_hotel_nights a, demo_hotel_nights b, demo_hotel_nights c, demo_hotel_nights d
        GROUP BY h.hotel_id'''
    with pytest.raises(QueryRejected):
        store.retrieve(expensive, {}, '16803', '2026-10-11', '2026-10-13', 2)


def test_invalid_inputs_clarification_and_failed_provider_saved(setup):
    client, _, model, _ = setup
    for question in ['', '  ', 'x'*2001]:
        assert client.post('/api/chat', json={'question': question}).status_code == 422
    model.plan = {'sql': None, 'params': {}, 'clarification': 'Which ZIP and dates?'}
    reply = client.post('/api/chat', json={'question': 'Hello for October 11–13, 2026 near 16803'}).json()
    assert reply['status'] == 'clarification' and reply['executed_sql'] is None
    model.failure = ChatError('Fixture quota exceeded', 429)
    reply = client.post('/api/chat', json={'question': 'Try again for October 11–13, 2026 near 16803'})
    assert reply.status_code == 429
    history = client.get('/api/chat/conversations/'+reply.json()['conversation_id']).json()['messages']
    assert history[-1]['stage'] == 'error'
    assert client.get('/api/chat/conversations/00000000-0000-0000-0000-000000000000').status_code == 404


def test_migration_v4_preserves_all_existing_records(setup):
    _, database, _, _ = setup
    before = snapshot(database)
    with database.connect() as db:
        db.execute('DROP TABLE chat_messages')
        db.execute('DROP TABLE chat_conversations')
        db.execute('PRAGMA user_version=4')
    database.initialize()
    database.initialize()
    assert snapshot(database) == before
    with database.connect() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 5
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('code,expected', [(401,503), (403,503), (429,429), (500,502), (400,502)])
def test_provider_failures_are_safe(monkeypatch, code, expected):
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-secret-never-expose')
    monkeypatch.setattr(httpx.Client, 'post', lambda *a, **k: httpx.Response(code, text='fixture-secret-never-expose'))
    model = OpenAIModel()
    with pytest.raises(ChatError) as result:
        model.complete([{'role': 'user', 'content': 'test'}])
    assert result.value.status == expected and 'fixture-secret' not in str(result.value)


def test_provider_contract_json_timeout_and_malformed(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-secret')
    calls = []
    def post(*args, **kwargs):
        calls.append(kwargs)
        return httpx.Response(200, json={'choices':[{'finish_reason':'stop','message':{'content':'{"sql":null}'}}]})
    monkeypatch.setattr(httpx.Client, 'post', post)
    model = OpenAIModel()
    assert model.complete([{'role':'user','content':'test'}], json_output=True) == '{"sql":null}'
    assert calls[0]['json']['response_format'] == {'type':'json_object'}
    assert calls[0]['json']['store'] is False
    def timeout(*args, **kwargs):
        raise httpx.ReadTimeout('fixture-secret')
    monkeypatch.setattr(httpx.Client, 'post', timeout)
    with pytest.raises(ChatError, match='timed out'):
        model.complete([])
    monkeypatch.setattr(httpx.Client, 'post', lambda *a, **k: httpx.Response(200, json={}))
    with pytest.raises(ChatError, match='invalid response'):
        model.complete([])


def test_more_than_thirty_rows_rejected(setup):
    _, database, _, _ = setup
    query = '''SELECT h.hotel_id, n.nightly_rate_cents AS total_cents
        FROM saved_hotels h CROSS JOIN saved_hotel_zips z CROSS JOIN demo_hotel_nights n
        WHERE z.hotel_id=h.hotel_id'''
    with pytest.raises(QueryRejected, match='at most 30'):
        ChatStore(database).retrieve(query, {}, '16803', '2026-10-11', '2026-10-12', 1)


def test_bad_plan_and_second_call_failure_do_not_fabricate_answer(setup):
    client, _, model, app = setup
    model.plan['params']['check_in'] = '2026-10-09'
    assert client.post('/api/chat', json={'question': 'Mismatched parameters for October 11–13, 2026 near 16803'}).status_code == 422
    model.plan = {'sql': SQL, 'params': {}, 'check_in': '2026-02-30', 'check_out': '2026-03-01', 'postcode':'16803'}
    assert client.post('/api/chat', json={'question': 'Invalid date for October 11–13, 2026 near 16803'}).status_code == 422
    original = FakeModel()
    def fail_answer(messages, *, json_output=False):
        if not json_output:
            raise ChatError('Fixture second call timeout', 504)
        return original.complete(messages, json_output=True)
    app.state.chat.model.complete = fail_answer
    response = client.post('/api/chat', json={'question': 'Valid question; failed answer for October 11–13, 2026 near 16803'})
    assert response.status_code == 504
    history = client.get('/api/chat/conversations/'+response.json()['conversation_id']).json()['messages']
    assert any(m['stage']=='retrieval_result' for m in history)
    assert history[-1]['stage']=='error'
    assert not any(m['stage']=='answer' for m in history)


def test_missing_configuration_does_not_expose_secrets(monkeypatch):
    monkeypatch.setattr('app.controllers.chat.load_dotenv', lambda *a, **k: None)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('OPEN_AI', raising=False)
    model = OpenAIModel()
    assert not model.configured
    with pytest.raises(ChatError, match='not configured'):
        model.complete([])
    monkeypatch.setenv('OPEN_AI', 'fictional-key')
    assert OpenAIModel().configured


def test_stages_have_distinct_instructions_and_query_instead_of_answer_is_error(setup):
    client, _, model, app = setup
    result = client.post('/api/chat', json={'question': 'Compare saved hotels for two nights for October 11–13, 2026 near 16803'})
    assert result.status_code == 200
    query_prompt = model.calls[0][0]['content']
    answer_prompt = model.calls[1][0]['content']
    assert 'QUERY STAGE:' in query_prompt and 'ANSWER STAGE:' not in query_prompt
    assert 'ANSWER STAGE:' in answer_prompt and 'QUERY STAGE:' not in answer_prompt
    assert 'return ONLY a JSON object' not in answer_prompt
    app.state.chat.model.complete = lambda *args, **kwargs: json.dumps(PLAN)
    result = client.post('/api/chat', json={'question': 'Fixture model returns SQL twice for October 11–13, 2026 near 16803'})
    assert result.status_code == 502
    assert 'instead of an answer' in result.json()['detail']
    history = client.get('/api/chat/conversations/'+result.json()['conversation_id']).json()['messages']
    assert history[-1]['stage'] == 'error'
    assert not any(m['stage']=='answer' for m in history)


def test_projection_rejection_releases_read_lock_before_error_is_saved(setup):
    client, _, model, _ = setup
    model.plan['sql'] = SQL.replace('AS total_cents', 'AS invalid_total').replace('ORDER BY total_cents', 'ORDER BY invalid_total')
    result = client.post('/api/chat', json={'question': 'Fixture unsupported projection for October 11–13, 2026 near 16803'})
    assert result.status_code == 422, result.text
    history = client.get('/api/chat/conversations/'+result.json()['conversation_id']).json()['messages']
    assert history[-1]['stage'] == 'error'
    assert 'hotel_id and total_cents' in history[-2]['content']
    assert 'suggested question' in history[-1]['content']


def test_single_night_accepts_verified_nightly_column_without_total_alias(setup):
    client, _, model, _ = setup
    model.plan['check_out'] = model.plan['params']['check_out'] = '2026-10-12'
    model.plan['sql'] = '''SELECT h.hotel_id, n.nightly_rate_cents FROM saved_hotels h
        JOIN saved_hotel_zips z ON h.hotel_id=z.hotel_id JOIN demo_hotel_nights n ON h.hotel_id=n.hotel_id
        WHERE z.postcode=:postcode AND n.stay_date>=:check_in AND n.stay_date<:check_out
        AND n.rooms_available>=1 ORDER BY n.nightly_rate_cents, h.hotel_id LIMIT 3'''
    response = client.post('/api/chat', json={'question': 'One night for October 11–13, 2026 near 16803'})
    assert response.status_code == 200
    assert response.json()['records'][0]['total_cents'] == 8000


def test_empty_collection_explains_save_workflow_without_paid_calls(tmp_path):
    app = create_app(tmp_path/'empty.sqlite3')
    with TestClient(app) as client:
        model = FakeModel()
        app.state.chat.model = model
        response = client.post('/api/chat', json={'question': 'Show me all hotels near 16803'})
        assert response.status_code == 200
        assert response.json()['status'] == 'needs_saved_hotels'
        assert 'Add to Local' in response.json()['answer']
        assert 'course' not in response.json()['answer'].lower()
        assert response.json()['executed_sql'] is None
        assert model.calls == []
        assert client.get('/api/chat/catalog').json() == {'hotel_count': 0, 'zips': []}


def test_no_user_date_never_inherits_example_or_assistant_guess(setup):
    client, _, model, app = setup
    question = 'Show me hotels that are the cheapest near 16803'
    response = client.post('/api/chat', json={'question': question})
    assert response.json()['status'] == 'clarification'
    assert 'course' not in response.json()['answer'].lower()
    assert model.calls == []
    cid = response.json()['conversation_id']
    app.state.chat.store.record(cid, 'prior-bad-answer', 'assistant', 'answer',
                                'I assumed October 12, 2026.', app.state.chat.version)
    follow = client.post('/api/chat', json={'question': 'May I see all the hotels?', 'conversation_id': cid})
    assert follow.json()['status'] == 'clarification'
    assert model.calls == []


def test_catalog_uses_saved_zips_and_recorded_dates_and_updates_after_remove(setup):
    client, database, _, _ = setup
    catalog = client.get('/api/chat/catalog')
    assert catalog.headers['cache-control'] == 'no-store'
    assert catalog.json() == {'hotel_count': 4, 'zips': [{'postcode':'16803','hotel_count':4,
        'nights':[f'2026-10-{day}' for day in range(10,15)]}]}
    for hotel_id in ['fixture-0','fixture-1','fixture-2','fixture-3']:
        client.delete('/api/local-hotels',params={'hotel_id':hotel_id})
    assert client.get('/api/chat/catalog').json()['hotel_count'] == 0
    with TestClient(create_app(database.path)) as restarted:
        assert restarted.get('/api/chat/catalog').json()['hotel_count'] == 0


@pytest.mark.parametrize('column', ['available_rooms', 'rooms_available'])
def test_room_projection_is_verified_and_reaches_second_model_call(setup, column):
    client, database, model, _ = setup
    before = snapshot(database)
    model.plan['sql'] = SQL.replace('AS total_cents\n', f'AS total_cents, MIN(n.rooms_available) AS {column}\n')
    response = client.post('/api/chat', json={'question': 'Compare saved hotels near 16803 for October 11–13, 2026 with available rooms.'})
    assert response.status_code == 200, response.text
    assert [row['total_cents'] for row in response.json()['records']] == [18000, 20000]
    assert all(row[column] == 20 for row in response.json()['rows'])
    assert len(model.calls) == 2
    assert snapshot(database) == before
    model.plan['sql'] = model.plan['sql'].replace('MIN(n.rooms_available) AS', '999 AS')
    response = client.post('/api/chat', json={'question': 'Compare rooms near 16803 October 11–13, 2026'})
    assert response.status_code == 422
    assert len(model.calls) == 3
    assert snapshot(database) == before


def test_single_night_budget_with_rooms_and_reordered_columns(setup):
    client, _, model, _ = setup
    model.plan['check_out'] = model.plan['params']['check_out'] = '2026-10-12'
    model.plan['sql'] = '''SELECT n.rooms_available, n.nightly_rate_cents AS total_cents, h.hotel_id
        FROM saved_hotels h JOIN saved_hotel_zips z ON h.hotel_id=z.hotel_id
        JOIN demo_hotel_nights n ON h.hotel_id=n.hotel_id
        WHERE z.postcode=:postcode AND n.stay_date=:check_in
        AND n.nightly_rate_cents<=9000 AND n.rooms_available>=1
        ORDER BY total_cents, h.hotel_id LIMIT 3'''
    response = client.post('/api/chat', json={'question': 'Which saved hotels near ZIP 16803 cost $90 or less for the night of Oct 11, 2026, with at least one room available?'})
    assert response.status_code == 200, response.text
    assert [r['total_cents'] for r in response.json()['records']] == [8000, 9000]
    assert len(model.calls) == 2


@pytest.mark.parametrize('date_text', ['10-20-26', '10-20-2026', '10/20/26', '2026-10-20'])
def test_numeric_dates_reach_model_and_return_no_matches_for_missing_nights(setup, date_text):
    client, _, model, _ = setup
    model.plan['check_in'] = model.plan['params']['check_in'] = '2026-10-20'
    model.plan['check_out'] = model.plan['params']['check_out'] = '2026-10-22'
    response = client.post('/api/chat', json={'question': f'{date_text} check-in, 10-22-26 check-out 16803'})
    assert response.status_code == 200
    assert response.json()['status'] == 'no_matches'
    assert response.json()['records'] == []
    assert len(model.calls) == 2
