"""Additive migration: existing users and booking references keep their IDs."""
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
