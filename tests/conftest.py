"""Block real network calls during tests so `pytest tests/` never hits the network."""
import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def _blocked(*args, **kwargs):
        raise RuntimeError("network access is not allowed in tests")

    monkeypatch.setattr("radar.ats_clients._session.get", _blocked)
    monkeypatch.setattr("radar.ats_clients._session.post", _blocked)
