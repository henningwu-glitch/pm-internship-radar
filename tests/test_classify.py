from radar.classify import (
    is_pm_internship,
    is_relevant,
    is_relevant_uk,
    is_uk_location,
    looks_like_2027_cycle,
)


def test_matches_basic_pm_intern():
    assert is_pm_internship("Product Manager Intern, Summer 2027")


def test_matches_apm_intern():
    assert is_pm_internship("APM Intern")


def test_matches_technical_pm_internship():
    assert is_pm_internship("Technical Product Manager Internship")


def test_matches_associate_product_manager_internship():
    assert is_pm_internship("Associate Product Manager Internship - Summer 2027")


def test_rejects_senior_pm_not_internship():
    assert not is_pm_internship("Senior Product Manager")


def test_rejects_software_engineer_intern():
    assert not is_pm_internship("Software Engineer Intern")


def test_rejects_internship_coordinator():
    assert not is_pm_internship("Product Internship Coordinator")


def test_rejects_manager_of_interns():
    assert not is_pm_internship("Manager of Interns - Product Team")


def test_lowercase_apm_does_not_match():
    # "apm" lowercase is too ambiguous (e.g. "campaign") — only exact-case APM counts.
    assert not is_pm_internship("apm intern")


def test_matches_product_owner_intern():
    assert is_pm_internship("Product Owner Intern, Summer 2027")


def test_matches_ux_intern():
    assert is_pm_internship("UX Intern, Summer 2027")


def test_matches_ux_design_intern():
    assert is_pm_internship("UX Design Intern")


def test_matches_user_experience_intern():
    assert is_pm_internship("User Experience Intern, Summer 2027")


def test_matches_product_design_intern():
    assert is_pm_internship("Product Designer Intern")


def test_matches_user_research_intern():
    assert is_pm_internship("User Researcher Intern")


def test_lowercase_ux_does_not_match():
    # lowercase "ux" is too ambiguous as a bare substring — only exact-case UX counts.
    assert not is_pm_internship("flux intern")


def test_year_2027_included():
    assert looks_like_2027_cycle("Product Manager Intern, Summer 2027")


def test_year_2026_excluded():
    assert not looks_like_2027_cycle("Product Manager Intern, Summer 2026")


def test_no_year_included():
    assert looks_like_2027_cycle("Product Manager Intern")


def test_future_year_included():
    assert looks_like_2027_cycle("Product Manager Intern, Summer 2028")


def test_is_relevant_combines_both_checks():
    assert is_relevant("Product Manager Intern, Summer 2027")
    assert not is_relevant("Product Manager Intern, Summer 2026")
    assert not is_relevant("Software Engineer Intern, Summer 2027")


def test_uk_country_name_matches():
    assert is_uk_location("United Kingdom")
    assert is_uk_location("Remote - UK")
    assert is_uk_location("London, England, United Kingdom")


def test_uk_city_matches():
    assert is_uk_location("London")
    assert is_uk_location("Manchester, UK")
    assert is_uk_location("Edinburgh")


def test_us_location_does_not_match():
    assert not is_uk_location("San Francisco, CA")
    assert not is_uk_location("New York, NY, USA")
    assert not is_uk_location(None)
    assert not is_uk_location("")


def test_london_ontario_is_not_uk():
    assert not is_uk_location("London, Ontario, Canada")


def test_new_york_is_not_uk():
    # Regression: "York" is also a real UK city, but must not fire on "New York".
    assert not is_uk_location("New York, NY, USA")


def test_is_relevant_uk_requires_both_title_and_location():
    assert is_relevant_uk("Product Manager Intern, Summer 2027", "London, UK")
    assert not is_relevant_uk("Product Manager Intern, Summer 2027", "San Francisco, CA")
    assert not is_relevant_uk("Software Engineer Intern, Summer 2027", "London, UK")
