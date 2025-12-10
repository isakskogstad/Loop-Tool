"""
Pytest configuration and fixtures for Loop-Auto tests
"""

import pytest
import asyncio
import tempfile
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# NOTE: temp_db fixture removed (2025-12-08)
# Old SQLite database replaced with Supabase
# Use Supabase test database or mocks for database tests


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        'orgnr': '5560001551',
        'name': 'Test Company AB',
        'company_type': 'Aktiebolag',
        'status': 'ACTIVE',
        'postal_street': 'Testgatan 1',
        'postal_code': '12345',
        'postal_city': 'Stockholm',
        'phone': '08-1234567',
        'email': 'info@test.se',
        'website': 'https://test.se',
        'revenue': 1000000,
        'net_profit': 100000,
        'num_employees': 10,
        'equity_ratio': 45.5,
        'source_basic': 'test'
    }


@pytest.fixture
def sample_roles_data():
    """Sample board/management data for testing."""
    return [
        {
            'name': 'Anna Andersson',
            'birth_year': 1975,
            'role_type': 'Styrelseledamot',
            'role_category': 'BOARD',
            'source': 'allabolag'
        },
        {
            'name': 'Bengt Bengtsson',
            'birth_year': 1980,
            'role_type': 'Verkställande direktör',
            'role_category': 'MANAGEMENT',
            'source': 'allabolag'
        },
        {
            'name': 'Cecilia Carlsson',
            'birth_year': 1985,
            'role_type': 'Revisor',
            'role_category': 'AUDITOR',
            'source': 'allabolag'
        }
    ]


@pytest.fixture
def sample_financials_data():
    """Sample financial data for testing."""
    return [
        {
            'period_year': 2023,
            'period_months': 12,
            'is_consolidated': 0,
            'revenue': 10000000,
            'net_profit': 1000000,
            'total_assets': 5000000,
            'equity': 2500000,
            'equity_ratio': 50.0,
            'num_employees': 25,
            'source': 'allabolag'
        },
        {
            'period_year': 2022,
            'period_months': 12,
            'is_consolidated': 0,
            'revenue': 9000000,
            'net_profit': 800000,
            'total_assets': 4500000,
            'equity': 2200000,
            'equity_ratio': 48.9,
            'num_employees': 22,
            'source': 'allabolag'
        }
    ]


# =============================================================================
# XBRL Parser Fixtures
# =============================================================================

from pathlib import Path


@pytest.fixture
def xbrl_test_documents_dir():
    """Path to XBRL test documents directory."""
    return Path(__file__).parent.parent / "test_annual_reports"


@pytest.fixture
def xbrl_comprehensive_dir():
    """Path to comprehensive XBRL analysis directory."""
    return Path(__file__).parent.parent / "test_annual_reports" / "comprehensive"


@pytest.fixture
def sample_xbrl_company_info():
    """Sample company info extracted from XBRL."""
    return {
        'name': 'Test Company AB',
        'orgnr': '5567891234',
        'fiscal_year_start': '2023-01-01',
        'fiscal_year_end': '2023-12-31',
    }


@pytest.fixture
def sample_xbrl_financials():
    """Sample financial data in XBRL format."""
    return {
        'current_year': {
            'revenue': 10500000,
            'operating_profit': 2100000,
            'profit_after_financial': 1900000,
            'net_profit': 1500000,
            'total_assets': 25000000,
            'equity': 12500000,
            'current_liabilities': 8000000,
            'cash': 5200000,
            'equity_ratio': 50,
            'num_employees': 25,
        },
        'previous_year': {
            'revenue': 9200000,
            'net_profit': 1200000,
            'total_assets': 22000000,
            'equity': 11000000,
        }
    }
