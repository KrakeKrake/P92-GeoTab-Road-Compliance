# valid request
# should return resolver result

#  missing goods_type_id
# should return 400

# missing profile_id
# should return 400

# missing axle_config_id
# should return 400

# missing vehicle_classification
# should return 400

# invalid vehicle classification
# should return 400

# condition_codes is not a list
# should return 400

# unknown vehicle profile
# should return 404

# unknown axle configuration
# should return 404

# axle configuration belongs to another template
# should return 400

# resolver returns error
# endpoint should return 404

# lowercase / spaced IDs
# should be normalized correctly

# condition codes
# should be stripped and converted to uppercase


import pytest

from flask import Flask
from types import SimpleNamespace

from db.compliance import routes
from db.compliance.db_models import (
    VehicleProfile,
    AxleConfiguration,
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
        axle_config=None,
    ):
        self.profile = profile
        self.axle_config = axle_config

    def query(self, model):

        if model == VehicleProfile:
            return FakeQuery(self.profile)

        if model == AxleConfiguration:
            return FakeQuery(self.axle_config)

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
        profile_id="STANDARD_PM_SEMI",
        template_id="PM_SEMI",
        display_name="Prime Mover + Semitrailer",
    )


def make_axle_config():

    return SimpleNamespace(
        axle_config_id="SEMI_6_AXLE_6_16_5_20",
        template_id="PM_SEMI",
        access_path="general_access",
    )


def test_valid_goods_routing_request(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        axle_config=make_axle_config(),
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    fake_result = {
        "status": "ok",
        "routing_preset": "test_preset",
    }

    monkeypatch.setattr(
        routes,
        "resolve_goods_routing_preset",
        lambda **kwargs: fake_result,
    )

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "GENERAL",
            "profile_id": "STANDARD_PM_SEMI",
            "axle_config_id":
                "SEMI_6_AXLE_6_16_5_20",
            "vehicle_classification":
                "general_access",
            "condition_codes": [],
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"
    assert data["routing_preset"] == "test_preset"


@pytest.mark.parametrize(
    "payload, expected_detail",
    [
        (
            {
                "profile_id": "STANDARD_PM_SEMI",
                "axle_config_id":
                    "SEMI_6_AXLE_6_16_5_20",
                "vehicle_classification":
                    "general_access",
            },
            "goods_type_id is required.",
        ),
        (
            {
                "goods_type_id": "GENERAL",
                "axle_config_id":
                    "SEMI_6_AXLE_6_16_5_20",
                "vehicle_classification":
                    "general_access",
            },
            "profile_id is required.",
        ),
        (
            {
                "goods_type_id": "GENERAL",
                "profile_id": "STANDARD_PM_SEMI",
                "vehicle_classification":
                    "general_access",
            },
            "axle_config_id is required.",
        ),
        (
            {
                "goods_type_id": "GENERAL",
                "profile_id": "STANDARD_PM_SEMI",
                "axle_config_id":
                    "SEMI_6_AXLE_6_16_5_20",
            },
            "vehicle_classification is required.",
        ),
    ],
)
def test_missing_required_fields(
    client,
    payload,
    expected_detail,
):

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json=payload,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["detail"] == expected_detail


@pytest.mark.parametrize(
    "classification",
    [
        "unknown",
        "invalid_input",
        "class_4",
        "abc",
    ],
)
def test_invalid_vehicle_classification(
    client,
    classification,
):

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "GENERAL",
            "profile_id": "STANDARD_PM_SEMI",
            "axle_config_id":
                "SEMI_6_AXLE_6_16_5_20",
            "vehicle_classification":
                classification,
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert (
        data["detail"]
        ==
        "vehicle_classification must be "
        "general_access, class_1, class_2, or class_3."
    )


@pytest.mark.parametrize(
    "classification",
    [
        "general_access",
        "class_1",
        "class_2",
        "class_3",
    ],
)
def test_all_valid_vehicle_classifications(
    client,
    monkeypatch,
    classification,
):

    fake_db = FakeDB(
        profile=make_profile(),
        axle_config=make_axle_config(),
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    monkeypatch.setattr(
        routes,
        "resolve_goods_routing_preset",
        lambda **kwargs: {
            "status": "ok",
            "classification":
                kwargs["vehicle_classification"],
        },
    )

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "GENERAL",
            "profile_id": "STANDARD_PM_SEMI",
            "axle_config_id":
                "SEMI_6_AXLE_6_16_5_20",
            "vehicle_classification":
                classification,
            "condition_codes": [],
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"
    assert data["classification"] == classification


@pytest.mark.parametrize(
    "condition_codes",
    [
        "ABC",
        123,
        {"code": "ABC"},
        True,
    ],
)
def test_condition_codes_must_be_list(
    client,
    condition_codes,
):

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "GENERAL",
            "profile_id": "STANDARD_PM_SEMI",
            "axle_config_id":
                "SEMI_6_AXLE_6_16_5_20",
            "vehicle_classification":
                "general_access",
            "condition_codes":
                condition_codes,
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert (
        data["detail"]
        == "condition_codes must be a list."
    )


def test_unknown_profile_returns_404(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=None,
        axle_config=None,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "GENERAL",
            "profile_id": "DOES_NOT_EXIST",
            "axle_config_id":
                "SEMI_6_AXLE_6_16_5_20",
            "vehicle_classification":
                "general_access",
            "condition_codes": [],
        },
    )

    assert response.status_code == 404

    data = response.get_json()

    assert (
        data["detail"]
        == "Vehicle profile not found."
    )


def test_unknown_axle_configuration_returns_404(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        axle_config=None,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "GENERAL",
            "profile_id": "STANDARD_PM_SEMI",
            "axle_config_id": "DOES_NOT_EXIST",
            "vehicle_classification":
                "general_access",
            "condition_codes": [],
        },
    )

    assert response.status_code == 404

    data = response.get_json()

    assert (
        data["detail"]
        == "Axle configuration not found."
    )


def test_axle_config_must_match_profile_template(
    client,
    monkeypatch,
):

    profile = make_profile()

    wrong_axle = SimpleNamespace(
        axle_config_id="B_DOUBLE_9_AXLE",
        template_id="B_DOUBLE",
        access_path="class_2",
    )

    fake_db = FakeDB(
        profile=profile,
        axle_config=wrong_axle,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "GENERAL",
            "profile_id": "STANDARD_PM_SEMI",
            "axle_config_id": "B_DOUBLE_9_AXLE",
            "vehicle_classification":
                "general_access",
            "condition_codes": [],
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert (
        data["detail"]
        ==
        "The axle configuration does not belong "
        "to the selected vehicle profile."
    )


def test_resolver_error_returns_404(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        axle_config=make_axle_config(),
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    monkeypatch.setattr(
        routes,
        "resolve_goods_routing_preset",
        lambda **kwargs: {
            "status": "error",
            "reason": "Goods type not found.",
        },
    )

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id": "UNKNOWN_GOODS",
            "profile_id": "STANDARD_PM_SEMI",
            "axle_config_id":
                "SEMI_6_AXLE_6_16_5_20",
            "vehicle_classification":
                "general_access",
            "condition_codes": [],
        },
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["status"] == "error"


def test_input_normalisation(
    client,
    monkeypatch,
):

    fake_db = FakeDB(
        profile=make_profile(),
        axle_config=make_axle_config(),
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    captured = {}

    def fake_resolver(**kwargs):

        captured.update(kwargs)

        return {
            "status": "ok",
        }

    monkeypatch.setattr(
        routes,
        "resolve_goods_routing_preset",
        fake_resolver,
    )

    response = client.post(
        "/api/compliance/resolve-goods-routing",
        json={
            "goods_type_id":
                " general ",

            "profile_id":
                " standard_pm_semi ",

            "axle_config_id":
                " semi_6_axle_6_16_5_20 ",

            "vehicle_classification":
                " CLASS_2 ",

            "condition_codes": [
                " abc ",
                " def ",
                "",
            ],
        },
    )

    assert response.status_code == 200

    assert (
        captured["goods_type_id"]
        == "GENERAL"
    )

    assert (
        captured["vehicle_classification"]
        == "class_2"
    )

    assert (
        captured["condition_codes"]
        == ["ABC", "DEF"]
    )

    assert (
        captured["template_id"]
        == "PM_SEMI"
    )

    assert (
        captured["axle_config_id"]
        == "SEMI_6_AXLE_6_16_5_20"
    )

    assert (
        captured["access_path"]
        == "general_access"
    )