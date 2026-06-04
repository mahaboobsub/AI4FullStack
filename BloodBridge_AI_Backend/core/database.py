"""
Supabase client singletons for BloodBridge AI.
"""
from supabase import create_client, Client
from core.config import get_settings

_supabase_client: Client = None
_supabase_admin_client: Client = None

def get_supabase() -> Client:
    """
    Get the standard Supabase client singleton.
    Subject to PostgreSQL Row Level Security (RLS).
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client

def get_supabase_admin() -> Client:
    """
    Get the Supabase admin client singleton.
    Bypasses Row Level Security (RLS) — used for seeding, migrations, and bulk imports.
    """
    global _supabase_admin_client
    if _supabase_admin_client is None:
        settings = get_settings()
        _supabase_admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _supabase_admin_client
