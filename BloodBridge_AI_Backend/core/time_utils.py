"""Shared UTC timestamp helpers for Supabase/PostgreSQL."""
from datetime import datetime, timezone


def utc_now_iso() -> str:
    """Return a PostgreSQL-compatible UTC timestamptz string."""
    return datetime.now(timezone.utc).isoformat()
