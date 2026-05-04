from __future__ import annotations

from shared.rebuild.service_logic_research import build_service_logic_research


def test_service_logic_supports_high_end_restaurant_services() -> None:
    source_attribution = {
        "source_pages": [
            {
                "url": "https://www.fdlxibalba.com/welcome",
                "title": "Flor de Lis - Experiencia",
                "headings": [
                    "A restaurant that tells stories through its food",
                    "Flor de Lis presents Contemporary Guatemalan Food.",
                    "Book your table at Flor de Lis-12 course mayan tasting menu in Guatemala City.",
                    "Chef's Table Q850 pp",
                    "Wine Pairing Q795",
                ],
            },
            {
                "url": "https://www.fdlxibalba.com/menu",
                "title": "Menu",
                "headings": ["MENU", "LOCATION"],
            },
        ]
    }

    payload = build_service_logic_research(
        services=[
            "12 Course Mayan Tasting Menu",
            "Chef's Table Guatemala City",
            "Fine Dining Reservations",
            "Contemporary Guatemalan Food",
            "Wine Pairing Dinner",
        ],
        website_scan={},
        source_attribution=source_attribution,
    )

    assert payload["status"] == "pass"
    assert payload["failing_services"] == 0
    assert {record["buyer_type"] for record in payload["services"]} == {"b2c"}
    assert all("restaurant" in record["concept_tokens"] for record in payload["services"])
