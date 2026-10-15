# classification passes + mass below limit
# both should pass

# classification passes + mass exactly at limit
# both should pass

# classification passes + mass above limit
# mass should fail

# class_3 classification + mass passes
# classification should remain class_3
# mass should pass

# unknown classification + mass passes
# classification result should remain unknown

# mass scheme not applicable
# should return not_applicable

# mass limit not found
# should return mass error

# missing profile_id
# should return 400

# missing axle_config_id
# should return 400

# missing mass_scheme
# should return 400

# invalid operating mass
# should return 400

# unknown vehicle profile
# should return 404


import pytest

from flask import Flask
from types import SimpleNamespace

from db.compliance import routes
from db.compliance.db_models import (
    VehicleProfile,
    AxleConfigMassLimit,
)


class FakeQuery:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(
        self,
        profile=None,
        mass_limit=None,
    ):
        self.profile = profile
        self.mass_limit = mass_limit

    def query(self, model):

        if model == VehicleProfile:
            return FakeQuery(self.profile)

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


def make_profile():

    return SimpleNamespace(
        profile_id="SEMI_STANDARD",
        display_name="Prime Mover + Semi",
        template_id="PM_SEMI",
    )


def make_classification(
    classification="general_access",
    status="ok",
):

    return {
        "status": status,
        "classification": classification,
        "reason": "Test classification result.",
        "used_dimensions": {
            "width_m": 2.5,
            "height_m": 4.3,
            "length_m": 19.0,
        },
        "missing_fields": [],
        "warnings": [],
    }


@pytest.mark.parametrize(
    "operating_mass, expected_status, expected_compliant",
    [
        (
            42.49,
            "ok",
            True,
        ),
        (
            42.50,
            "ok",
            True,
        ),
        (
            42.51,
            "exceeds_limit",
            False,
        ),
    ],
)
def test_combined_mass_boundaries(
    client,
    monkeypatch,
    operating_mass,
    expected_status,
    expected_compliant,
):

    profile = make_profile()

    mass_limit = SimpleNamespace(
        mass_limit_t=42.5,
    )

    fake_db = FakeDB(
        profile=profile,
        mass_limit=mass_limit,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    monkeypatch.setattr(
        routes,
        "classify_hvnl_from_db",
        lambda **kwargs: make_classification(),
    )

    response = client.post(
        "/api/compliance/classify-and-validate",
        json={
            "profile_id": "SEMI_STANDARD",
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "GML",
            "operating_mass_t": operating_mass,
            "custom_dimensions": False,
            "answers": {},
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert (
        data["classification_result"]["classification"]
        == "general_access"
    )

    assert (
        data["classification_result"]["status"]
        == "ok"
    )

    assert (
        data["mass_validation_result"]["status"]
        == expected_status
    )

    assert (
        data["mass_validation_result"]["compliant"]
        is expected_compliant
    )

    assert (
        data["mass_validation_result"]["selected_limit_t"]
        == 42.5
    )


def test_class_3_classification_with_compliant_mass(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        mass_limit=SimpleNamespace(
            mass_limit_t=42.5,
        ),
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    monkeypatch.setattr(
        routes,
        "classify_hvnl_from_db",
        lambda **kwargs: make_classification(
            classification="class_3"
        ),
    )

    response = client.post(
        "/api/compliance/classify-and-validate",
        json={
            "profile_id": "SEMI_STANDARD",
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "GML",
            "operating_mass_t": 42.0,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert (
        data["classification_result"]["classification"]
        == "class_3"
    )

    assert (
        data["mass_validation_result"]["compliant"]
        is True
    )


def test_unknown_classification_is_preserved(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        mass_limit=SimpleNamespace(
            mass_limit_t=42.5,
        ),
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    monkeypatch.setattr(
        routes,
        "classify_hvnl_from_db",
        lambda **kwargs: make_classification(
            classification="unknown",
            status="error",
        ),
    )

    response = client.post(
        "/api/compliance/classify-and-validate",
        json={
            "profile_id": "SEMI_STANDARD",
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "GML",
            "operating_mass_t": 42.0,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert (
        data["classification_result"]["classification"]
        == "unknown"
    )

    assert (
        data["classification_result"]["status"]
        == "error"
    )

    assert (
        data["mass_validation_result"]["compliant"]
        is True
    )


def test_mass_scheme_not_applicable(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        mass_limit=SimpleNamespace(
            mass_limit_t=None,
        ),
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    monkeypatch.setattr(
        routes,
        "classify_hvnl_from_db",
        lambda **kwargs: make_classification(),
    )

    response = client.post(
        "/api/compliance/classify-and-validate",
        json={
            "profile_id": "SEMI_STANDARD",
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "HML",
            "operating_mass_t": 42.0,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert (
        data["mass_validation_result"]["status"]
        == "not_applicable"
    )

    assert (
        data["mass_validation_result"]["compliant"]
        is False
    )

    assert (
        data["mass_validation_result"]["selected_limit_t"]
        is None
    )


def test_mass_limit_not_found(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        mass_limit=None,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    monkeypatch.setattr(
        routes,
        "classify_hvnl_from_db",
        lambda **kwargs: make_classification(),
    )

    response = client.post(
        "/api/compliance/classify-and-validate",
        json={
            "profile_id": "SEMI_STANDARD",
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "ABC",
            "operating_mass_t": 42.0,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert (
        data["mass_validation_result"]["status"]
        == "error"
    )

    assert (
        data["mass_validation_result"]["compliant"]
        is False
    )

    assert (
        data["mass_validation_result"]["selected_limit_t"]
        is None
    )


@pytest.mark.parametrize(
    "payload, expected_detail",
    [
        (
            {
                "axle_config_id": "SEMI_6_AXLE",
                "mass_scheme": "GML",
                "operating_mass_t": 42.0,
            },
            "profile_id is required.",
        ),
        (
            {
                "profile_id": "SEMI_STANDARD",
                "mass_scheme": "GML",
                "operating_mass_t": 42.0,
            },
            "axle_config_id is required.",
        ),
        (
            {
                "profile_id": "SEMI_STANDARD",
                "axle_config_id": "SEMI_6_AXLE",
                "operating_mass_t": 42.0,
            },
            "mass_scheme is required.",
        ),
        (
            {
                "profile_id": "SEMI_STANDARD",
                "axle_config_id": "SEMI_6_AXLE",
                "mass_scheme": "GML",
                "operating_mass_t": "abc",
            },
            "operating_mass_t must be a number.",
        ),
    ],
)
def test_invalid_required_inputs(
    client,
    payload,
    expected_detail,
):

    response = client.post(
        "/api/compliance/classify-and-validate",
        json=payload,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["detail"] == expected_detail


def test_unknown_vehicle_profile_returns_404(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=None,
        mass_limit=None,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/classify-and-validate",
        json={
            "profile_id": "DOES_NOT_EXIST",
            "axle_config_id": "SEMI_6_AXLE",
            "mass_scheme": "GML",
            "operating_mass_t": 42.0,
        },
    )

    assert response.status_code == 404

    data = response.get_json()

    assert (
        data["detail"]
        == "Vehicle profile not found."
    )