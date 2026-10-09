"""Model: durable conversation traces and sandboxed, read-only hotel retrieval."""
from datetime import datetime, timezone
import json
import re
import sqlite3
import time
from uuid import uuid4

from app.database import Database, RecordNotFound


class QueryRejected(ValueError):
    pass


TABLES = {'saved_hotels', 'saved_hotel_zips', 'demo_hotel_nights'}
FUNCTIONS = {'count', 'sum', 'min', 'max', 'avg', 'round', 'coalesce', 'nullif',
             'julianday', 'date', 'lower', 'upper', 'abs'}


class ChatStore:
    def __init__(self, database: Database):
        self.database = database

    def catalog(self) -> dict:
        """Only public saved-place counts and recorded dates; no account data."""
        with self.database.connect() as db:
            db.execute('BEGIN')
            count = db.execute('SELECT count(*) FROM saved_hotels').fetchone()[0]
            zips = []
            for row in db.execute('SELECT postcode, count(*) AS hotel_count FROM saved_hotel_zips GROUP BY postcode ORDER BY postcode'):
                nights = [day[0] for day in db.execute('''SELECT DISTINCT n.stay_date
                    FROM demo_hotel_nights n JOIN saved_hotel_zips z USING(hotel_id)
                    WHERE z.postcode=? ORDER BY n.stay_date''', (row['postcode'],))]
                zips.append({**dict(row), 'nights': nights})
            return {'hotel_count': count, 'zips': zips}

    def create(self, title: str) -> str:
        conversation_id = str(uuid4())
        with self.database.connect() as db:
            db.execute('INSERT INTO chat_conversations VALUES (?, ?, ?)',
                       (conversation_id, title[:100], datetime.now(timezone.utc).isoformat()))
        return conversation_id

    def list(self) -> list[dict]:
        with self.database.connect() as db:
            return [dict(row) for row in db.execute(
                'SELECT * FROM chat_conversations ORDER BY created_at DESC LIMIT 100')]

    def history(self, conversation_id: str) -> list[dict]:
        with self.database.connect() as db:
            if not db.execute('SELECT 1 FROM chat_conversations WHERE conversation_id=?',
                              (conversation_id,)).fetchone():
                raise RecordNotFound('Conversation not found.')
            return [dict(row) for row in db.execute('''SELECT * FROM (
                SELECT * FROM chat_messages WHERE conversation_id=? ORDER BY message_id DESC LIMIT 500
                ) ORDER BY message_id''', (conversation_id,))]

    def record(self, conversation_id: str, turn_id: str, role: str, stage: str,
               content: str | dict | list, prompt_version: str) -> None:
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        with self.database.connect() as db:
            db.execute('''INSERT INTO chat_messages
                (conversation_id, turn_id, timestamp, role, stage, content, prompt_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)''', (conversation_id, turn_id,
                datetime.now(timezone.utc).isoformat(), role, stage, text, prompt_version))

    def retrieve(self, sql: str, params: dict, postcode: str, check_in: str,
                 check_out: str, nights: int) -> tuple[str, list[dict], list[dict]]:
        """SQLite authorizer is the security boundary, not the prefix check.

        Raw proposals select IDs/totals; trusted parameterized queries on the SAME
        read transaction verify every night and attach the actual supporting data.
        """
        query = sql.strip()
        if (len(query) > 8000 or not re.match(r'^SELECT\b', query, re.I)
                or any(token in query for token in (';', '--', '/*', '\x00'))):
            raise QueryRejected('Only one bounded SELECT without comments is allowed.')
        executed = f'SELECT * FROM ({query}) AS hotel_matches LIMIT 31'
        db = sqlite3.connect(self.database.path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)
        db.row_factory = sqlite3.Row
        cursor = None
        try:
            db.execute('PRAGMA query_only=ON')
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN')
            db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 100_000)
            db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 10_000)
            db.setlimit(sqlite3.SQLITE_LIMIT_EXPR_DEPTH, 50)
            db.setlimit(sqlite3.SQLITE_LIMIT_COMPOUND_SELECT, 10)
            reads = set()

            def authorize(action, first, second, schema, _trigger):
                if action == sqlite3.SQLITE_SELECT:
                    return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_READ and schema == 'main' and first in TABLES:
                    reads.add(first)
                    return sqlite3.SQLITE_OK
                if action == sqlite3.SQLITE_FUNCTION and (second or '').lower() in FUNCTIONS:
                    return sqlite3.SQLITE_OK
                return sqlite3.SQLITE_DENY

            deadline = time.monotonic() + 0.5
            steps = 0

            def progress():
                nonlocal steps
                steps += 1000
                return int(steps > 200_000 or time.monotonic() > deadline)

            db.set_authorizer(authorize)
            db.set_progress_handler(progress, 1000)
            cursor = db.execute(executed, params)
            columns = [column[0] for column in cursor.description]
            # Column order and optional room counts are presentation choices, not
            # security boundaries. Verify every accepted value against this snapshot.
            room_columns = {'rooms_available', 'available_rooms'}
            total_column = 'total_cents' if 'total_cents' in columns else 'nightly_rate_cents'
            allowed = {'hotel_id', total_column} | room_columns
            if (not {'hotel_id', total_column}.issubset(columns)
                    or (total_column == 'nightly_rate_cents' and nights != 1)
                    or len(columns) != len(set(columns)) or not set(columns) <= allowed):
                raise QueryRejected('The query must return hotel_id and total_cents, with optional room counts.')
            raw = [dict(row) for row in cursor.fetchall()]
            if reads != TABLES or len(raw) > 30:
                raise QueryRejected('Use all three hotel tables and return at most 30 hotels.')
            if len({row['hotel_id'] for row in raw}) != len(raw):
                raise QueryRejected('The query must return one row per hotel.')
            # Authorizer remains active; only these tables/functions remain allowed.
            records = []
            for row in raw:
                hotel = db.execute('''SELECT h.* FROM saved_hotels h JOIN saved_hotel_zips z
                    ON h.hotel_id=z.hotel_id WHERE h.hotel_id=? AND z.postcode=?''',
                    (row['hotel_id'], postcode)).fetchone()
                days = [dict(day) for day in db.execute('''SELECT stay_date, nightly_rate_cents,
                    rooms_available FROM demo_hotel_nights WHERE hotel_id=?
                    AND stay_date>=? AND stay_date<? ORDER BY stay_date''',
                    (row['hotel_id'], check_in, check_out))]
                total = sum(day['nightly_rate_cents'] for day in days)
                proposed_total = row.get('total_cents', row.get('nightly_rate_cents'))
                if (hotel is None or len(days) != nights or any(day['rooms_available'] < 1 for day in days)
                        or type(proposed_total) is not int or proposed_total != total):
                    raise QueryRejected('The query returned an incomplete stay, unavailable room, wrong ZIP or incorrect total.')
                minimum_rooms = min(day['rooms_available'] for day in days)
                if any(type(row[column]) is not int or row[column] != minimum_rooms
                       for column in room_columns.intersection(row)):
                    raise QueryRejected('The query returned an incorrect available room count.')
                records.append({**dict(hotel), 'postcode': postcode, 'check_in': check_in,
                                'check_out': check_out, 'nights': nights, 'total_cents': total,
                                'demo_nights': days, 'simulated': True})
            return executed, raw, records
        except sqlite3.Error as error:
            raise QueryRejected('Query rejected: use only permitted hotel data within the read-only query limits.') from error
        finally:
            # Close the active statement before the connection. Otherwise an early
            # projection rejection can retain a read lock through its traceback.
            if cursor is not None:
                cursor.close()
            db.close()
