# Part 2 SQLite CRUD

## Selected instruction

> Start Part 2. Seed SQLite with the supplied hotel, trip, user, and booking
> records, then perform search and all booking create, read, cancel, and delete
> actions through Vue, FastAPI, and persistent SQLite storage.

## Result

The backend imports all four fictional CSV files only when it creates the
database. Vue lets a selected traveler book a searched stay, read history,
cancel while retaining the record, and delete a test booking. Automated and
browser checks use temporary databases so normal application data is not
changed.
