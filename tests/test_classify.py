from radar.classify import is_pm_internship, is_relevant, looks_like_2027_cycle


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
