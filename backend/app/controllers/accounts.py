"""Classroom account validation and server-managed current user."""
import secrets

from fastapi import HTTPException
from app.database import Database


class AccountController:
    def __init__(self, database: Database):
        self.database = database

    def create(self, username: str, password: str) -> dict:
        try:
            return self.database.create_account(username.strip().casefold(), password)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    def login(self, username: str, password: str, old_token: str | None) -> tuple[dict, str]:
        user = self.database.credentials(username.strip().casefold())
        if user is None or user['password'] != password:
            # A failed login must not leave a previous user signed in.
            self.database.delete_session(old_token)
            raise HTTPException(401, "Incorrect username or password.")
        token = secrets.token_urlsafe(32)
        self.database.save_session(token, user['user_id'], old_token)
        return {key: user[key] for key in ('user_id', 'username', 'display_name')}, token

    def current(self, token: str | None) -> dict | None:
        return self.database.session_user(token)

    def require(self, token: str | None, user_id: str) -> dict:
        user = self.current(token)
        if user is None:
            raise HTTPException(401, "Log in to manage your bookings.")
        if user['user_id'] != user_id:
            raise HTTPException(403, "You can only manage your own bookings.")
        return user
