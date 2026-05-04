from __future__ import annotations

from shared.rebuild.search_term_review import build_search_term_review


def test_confirmed_service_and_region_does_not_create_obvious_client_question() -> None:
    review = build_search_term_review(
        [
            {"Search term": "emdr therapy toronto", "Impr.": "60", "Clicks": "6", "Conversions": "0"},
            {"Search term": "emdr therapy hamilton", "Impr.": "8", "Clicks": "1", "Conversions": "0"},
            {"Search term": "pain clinic toronto", "Impr.": "11", "Clicks": "2", "Conversions": "0"},
        ],
        service_terms=["EMDR Therapy", "Chronic Pain Therapy"],
        approved_regions=["Toronto, Ontario, Canada"],
        candidate_regions=["Toronto", "Hamilton"],
    )

    decisions = {decision.search_term: decision for decision in review.decisions}
    assert decisions["emdr therapy toronto"].category == "focus_candidate"
    assert decisions["emdr therapy toronto"].client_action == "Do not ask if service and region are already confirmed."
    assert decisions["emdr therapy hamilton"].category == "unknown_region_confirmation"
    assert decisions["pain clinic toronto"].category == "exclude_recommendation"

    regional_groups = [group for group in review.question_groups if group.group_type == "regional"]
    assert len(regional_groups) == 1
    group = regional_groups[0]
    assert group.group_id == "regional_keyword_targeting"
    assert group.group_type == "regional"
    assert group.regions == ["Hamilton"]
    assert group.terms == ["emdr therapy hamilton"]
    assert "Focus, Keep, or Exclude keyword targeting" in group.question


def test_unknown_region_terms_are_grouped_into_one_question() -> None:
    review = build_search_term_review(
        [
            {"Search term": "emdr therapy markham", "Impr.": "3", "Clicks": "2", "Conversions": "1"},
            {"Search term": "trauma therapy markham", "Impr.": "4", "Clicks": "1", "Conversions": "0"},
            {"Search term": "trauma therapy mississauga", "Impr.": "5", "Clicks": "1", "Conversions": "0"},
        ],
        service_terms=["EMDR Therapy", "Trauma Therapy"],
        approved_regions=["Toronto"],
        candidate_regions=["Markham", "Mississauga", "Toronto"],
    )

    regional_groups = [group for group in review.question_groups if group.group_type == "regional"]
    assert len(regional_groups) == 1
    group = regional_groups[0]
    assert group.regions == ["Markham", "Mississauga"]
    assert "emdr therapy markham" in group.terms
    assert "trauma therapy markham" in group.terms


def test_virtual_only_confirmed_telehealth_region_does_not_create_city_question() -> None:
    review = build_search_term_review(
        [
            {"Search term": "cbt therapy new york", "Impr.": "10", "Clicks": "2", "Conversions": "0"},
            {"Search term": "cbt therapy pennsylvania", "Impr.": "8", "Clicks": "1", "Conversions": "0"},
        ],
        service_terms=["CBT Therapy"],
        approved_regions=["New York"],
        candidate_regions=["New York", "Pennsylvania"],
        telehealth_regions=["New York", "New Jersey"],
        virtual_only=True,
    )

    decisions = {decision.search_term: decision for decision in review.decisions}
    assert decisions["cbt therapy new york"].category == "covered_service_observation"
    assert decisions["cbt therapy pennsylvania"].category == "unknown_region_confirmation"
    assert [group.regions for group in review.question_groups] == [["Pennsylvania"]]


def test_question_groups_include_service_and_exclude_sections() -> None:
    review = build_search_term_review(
        [
            {"Search term": "brainspotting consult", "Impr.": "12", "Clicks": "1", "Conversions": "0"},
            {"Search term": "somatic coaching", "Impr.": "10", "Clicks": "1", "Conversions": "0"},
            {"Search term": "therapy intensive", "Impr.": "9", "Clicks": "1", "Conversions": "0"},
            {"Search term": "pain clinic toronto", "Impr.": "11", "Clicks": "2", "Conversions": "0"},
        ],
        service_terms=["EMDR Therapy"],
        approved_regions=["Toronto"],
        candidate_regions=["Toronto"],
    )

    groups = {group.group_type: group for group in review.question_groups}
    assert "service" in groups
    assert "exclude" in groups
    assert groups["service"].title == "Review unclear search intent cluster"
    assert groups["exclude"].title == "Review grouped exclusions"


def test_competitor_terms_are_pruned_without_client_question() -> None:
    review = build_search_term_review(
        [
            {"Search term": "khetani therapy reviews", "Impr.": "30", "Clicks": "4", "Conversions": "0"},
            {"Search term": "dr khetani trauma therapy", "Impr.": "12", "Clicks": "2", "Conversions": "0"},
            {"Search term": "trauma therapy toronto", "Impr.": "40", "Clicks": "5", "Conversions": "1"},
        ],
        service_terms=["Trauma Therapy"],
        approved_regions=["Toronto"],
        candidate_regions=["Toronto"],
        competitor_terms=["khetani"],
    )

    decisions = {decision.search_term: decision for decision in review.decisions}
    assert decisions["khetani therapy reviews"].category == "competitor_negative_candidate"
    assert decisions["khetani therapy reviews"].action_term == "khetani"
    assert decisions["khetani therapy reviews"].negative_match_type == "Negative Phrase"
    assert decisions["khetani therapy reviews"].negative_level == "Campaign"
    assert decisions["dr khetani trauma therapy"].action_term == "khetani"
    assert all(group.group_type != "exclude" for group in review.question_groups)
