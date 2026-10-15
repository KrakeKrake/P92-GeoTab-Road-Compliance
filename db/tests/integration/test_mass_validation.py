# Mass validation tests check:

# - Below mass limit
# - Exactly at mass limit
# - Above mass limit
# - Missing axle configuration
# - Missing mass scheme
# - Invalid operating mass input
# - Non-applicable mass scheme
import pytest

from flask import Flask

from db.compliance import routes
from db.compliance.db_models import (
    AxleConfiguration,
    AxleConfigMassLimit,
)


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, axle_config=None, mass_limit=None):
        self.axle_config = axle_config
        self.mass_limit = mass_limit

    def query(self, model):
        if model == AxleConfiguration:
            return FakeQuery(self.axle_config)

        if model == AxleConfigMassLimit:
            return FakeQuery(self.mass_limit)

        return FakeQuery(None)

    def close(self):
        pass


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(routes.compliance_bp)

    return app


@pytest.fixture
def client(app):
    return app.test_client()

@pytest.mark.parametrize(
    "scheme, limit, mass, expected_status, expected_compliant",
    [
        # GML
        ("GML", 42.5, 42.49, "ok", True),
        ("GML", 42.5, 42.50, "ok", True),
        ("GML", 42.5, 42.51, "exceeds_limit", False),

        # CML
        ("CML", 43.5, 43.49, "ok", True),
        ("CML", 43.5, 43.50, "ok", True),
        ("CML", 43.5, 43.51, "exceeds_limit", False),

        # HML
        ("HML", 45.5, 45.49, "ok", True),
        ("HML", 45.5, 45.50, "ok", True),
        ("HML", 45.5, 45.51, "exceeds_limit", False),
    ],
)
def test_mass_scheme_boundaries(
    client,
    monkeypatch,
    scheme,
    limit,
    mass,
    expected_status,
    expected_compliant,
):

    axle_config = type(
        "AxleConfig",
        (),
        {"axle_config_id": "SEMI_6_AXLE"}
    )()

    mass_limit = type(
        "MassLimit",
        (),
        {"mass_limit_t": limit}
    )()

    fake_db = FakeDB(
        axle_config=axle_config,
        mass_limit=mass_limit,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": scheme,
            "operating_mass_t": mass,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == expected_status
    assert data["compliant"] is expected_compliant
    assert data["selected_limit_t"] == limit

def test_missing_axle_config_returns_400(client):
    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "mass_scheme": "GML",
            "operating_mass_t": 42.0,
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["compliant"] is False
    assert data["reason"] == "axle_config_id is required."


def test_missing_mass_scheme_returns_400(client):
    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "axle_config_id": "SEMI_6_AXLE",
            "operating_mass_t": 42.0,
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["compliant"] is False
    assert data["reason"] == "mass_scheme is required."


def test_non_numeric_mass_returns_400(client):
    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "GML",
            "operating_mass_t": "abc",
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["status"] == "error"
    assert data["compliant"] is False
    assert data["reason"] == "operating_mass_t must be a number."


def test_mass_scheme_not_applicable(client, monkeypatch):

    axle_config = type(
        "AxleConfig",
        (),
        {"axle_config_id": "SEMI_6_AXLE"}
    )()

    mass_limit = type(
        "MassLimit",
        (),
        {"mass_limit_t": None}
    )()

    fake_db = FakeDB(
        axle_config=axle_config,
        mass_limit=mass_limit,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "HML",
            "operating_mass_t": 42.0,
        },
    )

    data = response.get_json()

    assert data["status"] == "not_applicable"
    assert data["compliant"] is False
    assert data["selected_limit_t"] is None