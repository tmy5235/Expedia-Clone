"""Versioned migrations; callers supply the transaction and foreign-key checks."""
import sqlite3


def migrate_accounts(db: sqlite3.Connection) -> None:
    db.execute("ALTER TABLE users ADD COLUMN username TEXT")
    db.execute("ALTER TABLE users ADD COLUMN password TEXT")
    for row in db.execute("SELECT user_id FROM users").fetchall():
        db.execute("UPDATE users SET username = ?, password = ? WHERE user_id = ?",
                   (f"traveler{int(row['user_id'][1:])}", "classroom-demo", row['user_id']))
    db.execute("CREATE UNIQUE INDEX users_username ON users(username)")
    db.execute("""CREATE TABLE sessions (
        token TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id))""")
    db.execute("""CREATE TABLE search_history (
        search_id INTEGER PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id),
        query TEXT NOT NULL, searched_at TEXT NOT NULL, search_day TEXT NOT NULL,
        search_count INTEGER NOT NULL CHECK(search_count > 0))""")
    db.execute("CREATE INDEX history_user_query_day ON search_history(user_id, query, search_day)")
    db.execute("ALTER TABLE bookings ADD COLUMN total_cents INTEGER CHECK(total_cents >= 0)")
    db.execute("""UPDATE bookings SET total_cents = (
        SELECT CAST(julianday(t.check_out) - julianday(t.check_in) AS INTEGER)
            * h.nightly_rate_cents FROM trips t JOIN hotels h ON h.hotel_id = t.hotel_id
        WHERE t.trip_id = bookings.trip_id)""")
    db.execute("PRAGMA user_version = 2")


def migrate_saved_hotels(db: sqlite3.Connection) -> None:
    """Version 3: external places and fictional daily inventory, without seeding.

    Discovery hotels[].place_id maps verbatim to hotel_id. The API fields name,
    address, latitude and longitude map to identically named columns. Demo night
    defaults are classroom values, never Geoapify rates or availability.
    """
    db.execute("""CREATE TABLE saved_hotels (
        hotel_id TEXT NOT NULL PRIMARY KEY COLLATE BINARY,
        name TEXT,
        address TEXT,
        latitude REAL NOT NULL CHECK(
            typeof(latitude) IN ('integer', 'real') AND latitude BETWEEN -90 AND 90),
        longitude REAL NOT NULL CHECK(
            typeof(longitude) IN ('integer', 'real') AND longitude BETWEEN -180 AND 180)
    )""")
    db.execute("""CREATE TABLE demo_hotel_nights (
        hotel_id TEXT NOT NULL REFERENCES saved_hotels(hotel_id),
        stay_date TEXT NOT NULL CHECK(
            stay_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
            AND stay_date BETWEEN '0001-01-01' AND '9999-12-31'
            AND date(stay_date, '+0 days') IS NOT NULL
            AND date(stay_date, '+0 days') = stay_date),
        nightly_rate_cents INTEGER NOT NULL DEFAULT 10000 CHECK(
            typeof(nightly_rate_cents) = 'integer' AND nightly_rate_cents >= 0),
        rooms_available INTEGER NOT NULL DEFAULT 20 CHECK(
            typeof(rooms_available) = 'integer' AND rooms_available >= 0),
        PRIMARY KEY (hotel_id, stay_date)
    )""")
    db.execute("PRAGMA user_version = 3")


def migrate_saved_hotel_locations(db: sqlite3.Connection) -> None:
    """Version 4: retain a ZIP search center separately from a hotel's address."""
    db.execute("""CREATE TABLE saved_search_locations (
        postcode TEXT NOT NULL PRIMARY KEY CHECK(postcode GLOB '[0-9][0-9][0-9][0-9][0-9]'),
        country_code TEXT NOT NULL CHECK(country_code = 'us'),
        locality TEXT,
        latitude REAL NOT NULL CHECK(typeof(latitude) IN ('real', 'integer') AND latitude BETWEEN -90 AND 90),
        longitude REAL NOT NULL CHECK(typeof(longitude) IN ('real', 'integer') AND longitude BETWEEN -180 AND 180)
    )""")
    db.execute("""CREATE TABLE saved_hotel_zips (
        hotel_id TEXT NOT NULL REFERENCES saved_hotels(hotel_id),
        postcode TEXT NOT NULL REFERENCES saved_search_locations(postcode),
        PRIMARY KEY (hotel_id, postcode)
    )""")
    db.execute('CREATE INDEX saved_hotel_zips_postcode ON saved_hotel_zips(postcode)')
    db.execute('PRAGMA user_version = 4')


def migrate_chat(db: sqlite3.Connection) -> None:
    """Version 5: additive classroom chat history; no changes to saved records."""
    db.execute('''CREATE TABLE IF NOT EXISTS chat_conversations (
        conversation_id TEXT PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
        message_id INTEGER PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES chat_conversations(conversation_id),
        turn_id TEXT NOT NULL, timestamp TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant', 'tool')),
        stage TEXT NOT NULL, content TEXT NOT NULL, prompt_version TEXT NOT NULL)''')
    db.execute('CREATE INDEX IF NOT EXISTS chat_messages_conversation ON chat_messages(conversation_id, message_id)')
    db.execute('PRAGMA user_version=5')
