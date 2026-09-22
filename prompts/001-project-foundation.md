# Project Foundation

## Selected instruction

> Build the new travel project from the Hello Agent foundation. Keep the existing Vue frontend and FastAPI backend structure, adapt it to the new project requirements, and begin with the Markdown files.

## Result

The project keeps separate `frontend/` and `backend/` folders. The Hello Agent
calculator was replaced with the Part 1 CSV hotel search, and Part 2 later added
persistent SQLite booking CRUD without changing that separation. The current
[accounts and personalized-pricing extension](006-accounts-personalized-pricing.md)
adds explicit MVC controllers, server-managed login, and per-user daily prices.
