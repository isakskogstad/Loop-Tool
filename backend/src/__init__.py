"""
Swedish Company Data API v3
Multi-source company data aggregation
"""

from .supabase_client import SupabaseDatabase as Database, get_database as get_db
from .orchestrator import DataOrchestrator, get_orchestrator
from .api import app

__version__ = "3.1.0"

__all__ = [
    'Database',
    'DataOrchestrator',
    'app',
    'get_db',
    'get_orchestrator'
]
