from __future__ import annotations

from shared.clients.supabase_client_registry import to_supabase_client_record


def test_supabase_record_filters_active_end_clients() -> None:
    record = to_supabase_client_record(
        {
            "id": "client-1",
            "status": "active",
            "relationship_type": "client",
            "company_id": "company-1",
            "google_ads_account_id": "123-456-7890",
            "login_customer_id": "211-993-1898",
            "discord_channel_id": "123",
        },
        {
            "id": "company-1",
            "company_name": "Example Client",
            "company_type": "client",
            "website": "https://example.com/",
        },
        {"id": "paid-1", "client_id": "client-1"},
    )

    assert record.is_active_end_client is True
    assert record.google_ads_customer_id == "1234567890"
    assert record.google_ads_login_customer_id == "2119931898"


def test_supabase_record_excludes_agency_companies() -> None:
    record = to_supabase_client_record(
        {"id": "client-1", "status": "active", "relationship_type": "client", "company_id": "company-1"},
        {"id": "company-1", "company_name": "Example Agency", "company_type": "agency"},
        {},
    )

    assert record.is_active_end_client is False

