"""Explicit isolated MOCK server. Never imported by the normal application."""
from contextlib import asynccontextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import time

import httpx

from app.controllers import locations
from app.controllers.chat import ChatError
from app.database import Database
from app.local_hotel_schemas import SaveLocalHotel
from app.main import create_app
from app.saved_hotels import SavedHotelStore
from tests.test_chat import FakeModel, PLAN

path = Path(os.environ['EXPEDIA_DB_PATH']).resolve()
if not str(path).startswith(('/tmp/', '/private/tmp/')):
    raise RuntimeError('The fixture server requires an explicit temporary database.')


def no_network(*args, **kwargs):
    raise AssertionError('Live provider traffic is disabled in the MOCK server')


httpx.HTTPTransport = no_network


def unavailable(*args, **kwargs):
    raise locations.GeoapifyRequestError()


locations.request_geoapify = unavailable


class BrowserModel(FakeModel):
    def complete(self, messages, *, json_output=False):
        if json_output:
            time.sleep(1)
            question = messages[-1]['content'].lower()
            self.plan = deepcopy(PLAN)
            if 'rate limit' in question:
                raise ChatError('MOCK provider rate limit. Try another question.', 429)
            if 'delete' in question:
                self.plan['sql'] = 'DELETE FROM saved_hotels'
            if 'no match' in question or '00501' in question:
                self.plan['postcode'] = self.plan['params']['postcode'] = '00501'
            elif re.search(r'\b12\b', question) and not re.search(r'\b13\b', question):
                self.plan['check_in'] = self.plan['params']['check_in'] = '2026-10-12'
            elif not re.search(r'\b13\b', question):
                self.plan['check_out'] = self.plan['params']['check_out'] = '2026-10-12'
        return super().complete(messages, json_output=json_output)


app = create_app(path)
original_lifespan = app.router.lifespan_context


@asynccontextmanager
async def lifespan(application):
    async with original_lifespan(application):
        database = Database(path)
        store = SavedHotelStore(database)
        with database.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS fixture_initialized (id INTEGER PRIMARY KEY)')
            initialized = db.execute('SELECT 1 FROM fixture_initialized').fetchone()
        if not initialized:
            fixture = json.loads((Path(__file__).resolve().parents[2]/'docs/evidence/assignment2-rag/fixed-hotels.json').read_text())
            for item in fixture['hotels']:
                payload = SaveLocalHotel.model_validate({'hotel':item['hotel'],'center':fixture['center']})
                store.save(payload.hotel, payload.center, ())
                with database.connect() as db:
                    db.executemany('INSERT INTO demo_hotel_nights VALUES (?, ?, ?, ?)', [
                        (payload.hotel.place_id,n['stay_date'],n['nightly_rate_cents'],n['rooms_available'])
                        for n in item['demo_nights']])
            with database.connect() as db:
                db.execute('INSERT INTO fixture_initialized VALUES (1)')
        application.state.chat.model = BrowserModel()
        yield


app.router.lifespan_context = lifespan
