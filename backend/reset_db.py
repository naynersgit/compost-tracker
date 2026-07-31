"""
One-off maintenance script — NOT part of the deployed app.
Run this locally once, whenever a schema change needs a clean rebuild.

Usage:
    1. Paste your Railway Postgres PUBLIC connection URL below, or set it
       as an environment variable named DATABASE_PUBLIC_URL before running.
    2. python reset_db.py
    3. Delete or don't commit this file's pasted URL if you hardcode it —
       treat a connection string as a password.
"""

import os
from sqlalchemy import create_engine, text

DATABASE_PUBLIC_URL = os.getenv("DATABASE_PUBLIC_URL", "postgresql://postgres:GOQJrGxxzIWeXouHwlnxFvdDvEPTPDEV@postgres.railway.internal:5432/railway")

if DATABASE_PUBLIC_URL.startswith("postgres://"):
    DATABASE_PUBLIC_URL = DATABASE_PUBLIC_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_PUBLIC_URL)

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS comments, intake_events, batches, users CASCADE;"))
    conn.commit()

print("Tables dropped. Redeploy (or restart) your backend to rebuild them with the new schema.")
