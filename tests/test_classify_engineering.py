from radar.classify_engineering import is_internship, is_relevant, is_relevant_uk


def test_matches_basic_engineering_internship():
    assert is_internship("Engineering Internship 2027")


def test_matches_summer_intern_engineer():
    assert is_internship("2027 Summer Intern Engineer")


def test_matches_engineering_summer_work_experience():
    assert is_internship("2027 Engineering Summer Work Experience")


def test_matches_summer_placement_no_role_word():
    # No role filtering — the company registry itself scopes this tracker.
    assert is_internship("Summer Placement 2027")


def test_matches_structural_engineer_internship():
    assert is_internship("Structural Engineer Summer Internship 2027")


def test_matches_software_engineer_intern():
    assert is_internship("Software Engineer Intern")


def test_matches_year_in_industry():
    assert is_internship("Year in Industry")


def test_matches_commercial_analyst_intern():
    assert is_internship("Commercial Analyst Intern, Summer 2027")


def test_matches_vacation_scheme():
    assert is_internship("2027 Vacation Scheme")


def test_rejects_senior_engineer_not_internship():
    assert not is_internship("Senior Mechanical Engineer")


def test_rejects_internship_coordinator():
    assert not is_internship("Engineering Internship Coordinator")


def test_is_relevant_combines_role_and_year():
    assert is_relevant("Engineering Internship 2027")
    assert not is_relevant("Engineering Internship 2026")


def test_is_relevant_uk_requires_both_title_and_location():
    assert is_relevant_uk("Engineering Internship 2027", "London, UK")
    assert not is_relevant_uk("Engineering Internship 2027", "San Francisco, CA")
    assert not is_relevant_uk("Senior Mechanical Engineer", "London, UK")
