#!/usr/bin/env python3
"""
Run once to create the initial admin account.

Usage:
    python -m scripts.seed_admin

Environment variables read from .env:
    DATABASE_URL, etc.
"""
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal
from app.models.user import Role
from app.repositories.user_repo import create_user, get_user_by_username
from app.schemas.user import UserCreate


def seed_admin():
    db = SessionLocal()
    try:
        username = "vpnadmin"
        existing = get_user_by_username(db, username)
        if existing:
            print(f"[seed] Admin user '{username}' already exists — skipping.")
            return

        payload = UserCreate(
            username=username,
            email="vpnadmin@hightech.local",
            full_name="Platform Administrator",
            password="Password@123",
            role=Role.ADMIN,
        )
        user = create_user(db, payload)
        print(f"[seed] Created admin user: {user.username} (id={user.id})")
        print("[seed] ⚠  Change the default password immediately!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
