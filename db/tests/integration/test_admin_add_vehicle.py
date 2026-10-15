# ADMIN ADD VEHICLE TESTS
#
# This test file checks the POST /api/compliance/admin/vehicles endpoint.
# - required category, template and profile fields
# - required numeric dimension fields
# - invalid numeric values
# - axle count validation
# - valid licence classes
# - valid vehicle classifications
# - minimum and maximum sanity ranges
# - default dimensions staying inside sanity ranges
# - legal dimension limits staying inside sanity ranges
# - axle configuration being required when enabled
# - duplicate vehicle profile IDs
# - duplicate template IDs
# - licence class existing in the database
# - axle configuration ID being required
# - duplicate axle configuration IDs in the same request
# - axle configuration IDs already existing in the database
# - axle display name being required
# - valid axle access paths
# - axle maximum length staying inside sanity ranges
# - negative GML, CML and HML mass limits being rejected
# - invalid JSON requests
# - successful vehicle creation

import copy
import pytest

from flask import Flask
from types import SimpleNamespace

from db.compliance import routes
from db.compliance.db_models import (
    VehicleCategory,
    VehicleProfile,
    VehicleTemplate,
    LicenceClass,
    AxleConfiguration,
    AxleGroupMass,
    AxleConfigMassLimit,
    DimensionRule,
    InputSanityRange,
)


class FakeQuery:
    def __init__(self, result=None):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(self, results=None):
        self.results = results or {}
        self.added = []
        self.commit_count = 0
        self.rollback_count = 0
        self.flush_count = 0

    def query(self, model):

        model_results = self.results.get(model, [])

        if model_results:
            result = model_results.pop(0)
        else:
            result = None

        return FakeQuery(result)

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flush_count += 1

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

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


def valid_payload():

    return {
        "category": {
            "category_id": "custom rigid",
            "category_name": "Custom Rigid",
        },

        "template": {
            "template_id": "custom rigid template",
            "template_name": "Custom Rigid Template",
            "base_type": "rigid",
        },

        "profile": {
            "profile_id": "custom rigid vehicle",
            "display_name": "Custom Rigid Vehicle",
            "vehicle_family": "Rigid",
            "combination_type": "Single",
            "gvm_category": "Heavy",
            "axle_count": 3,
            "axle_configurable": True,
            "default_width_m": 2.5,
            "default_height_m": 4.3,
            "default_length_m": 12.0,
            "allow_custom_dimensions": True,
            "required_licence_class_id": "HR",
        },

        "dimension_rule": {
            "rule_name": "Custom Rigid Rule",
            "width_limit_m": 2.5,
            "height_limit_m": 4.3,
            "length_limit_m": 12.5,
            "classification_if_exceeded_limit":
                "class_3",
        },

        "input_sanity_range": {
            "min_width_m": 2.0,
            "max_width_m": 3.0,
            "min_height_m": 3.0,
            "max_height_m": 5.0,
            "min_length_m": 5.0,
            "max_length_m": 15.0,
        },

        "axle_configurations": [
            {
                "axle_config_id": "custom axle",
                "display_name": "Custom 3 Axle",
                "max_length_m": 12.5,
                "access_path": "general_access",
                "axle_group_masses_t": [
                    6.0,
                    16.5,
                ],
                "gml_mass_t": 22.5,
                "cml_mass_t": 23.0,
                "hml_mass_t": None,
            }
        ],
    }


def valid_fake_db():

    licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    return FakeDB({
        VehicleProfile: [None],
        VehicleTemplate: [None],
        LicenceClass: [licence],
        VehicleCategory: [None],
        AxleConfiguration: [None],
    })


def set_nested_value(
    payload,
    path,
    value,
):

    current = payload

    for key in path[:-1]:
        current = current[key]

    current[path[-1]] = value


@pytest.mark.parametrize(
    "path, expected_detail",
    [
        (
            ("category", "category_id"),
            "category_id is required.",
        ),
        (
            ("category", "category_name"),
            "category_name is required.",
        ),
        (
            ("template", "template_id"),
            "template_id is required.",
        ),
        (
            ("template", "template_name"),
            "template_name is required.",
        ),
        (
            ("template", "base_type"),
            "base_type is required.",
        ),
        (
            ("profile", "profile_id"),
            "profile_id is required.",
        ),
        (
            ("profile", "display_name"),
            "display_name is required.",
        ),
        (
            ("profile", "vehicle_family"),
            "vehicle_family is required.",
        ),
        (
            ("profile", "combination_type"),
            "combination_type is required.",
        ),
    ],
)
def test_missing_required_text_fields(
    client,
    path,
    expected_detail,
):

    payload = valid_payload()

    set_nested_value(
        payload,
        path,
        "",
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


@pytest.mark.parametrize(
    "path, expected_detail",
    [
        (
            ("profile", "default_width_m"),
            "default_width_m is required.",
        ),
        (
            ("profile", "default_height_m"),
            "default_height_m is required.",
        ),
        (
            ("profile", "default_length_m"),
            "default_length_m is required.",
        ),
        (
            ("dimension_rule", "width_limit_m"),
            "width_limit_m is required.",
        ),
        (
            ("dimension_rule", "height_limit_m"),
            "height_limit_m is required.",
        ),
        (
            ("dimension_rule", "length_limit_m"),
            "length_limit_m is required.",
        ),
        (
            ("input_sanity_range", "min_width_m"),
            "min_width_m is required.",
        ),
        (
            ("input_sanity_range", "max_width_m"),
            "max_width_m is required.",
        ),
    ],
)
def test_missing_required_numeric_fields(
    client,
    path,
    expected_detail,
):

    payload = valid_payload()

    set_nested_value(
        payload,
        path,
        None,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


def test_invalid_numeric_value(client):

    payload = valid_payload()

    payload["profile"]["default_width_m"] = "abc"

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "default_width_m must be a number."
    )


def test_invalid_axle_count(client):

    payload = valid_payload()

    payload["profile"]["axle_count"] = "abc"

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "axle_count must be an integer."
    )


def test_invalid_required_licence(client):

    payload = valid_payload()

    payload["profile"][
        "required_licence_class_id"
    ] = "ABC"

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "required_licence_class_id must be "
        "LR, MR, HR, HC, or MC."
    )


def test_invalid_exceeded_classification(
    client,
):

    payload = valid_payload()

    payload["dimension_rule"][
        "classification_if_exceeded_limit"
    ] = "class_4"

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "classification_if_exceeded_limit must be "
        "general_access, class_1, class_2, or class_3."
    )


@pytest.mark.parametrize(
    "minimum_field, maximum_field, expected_detail",
    [
        (
            "min_width_m",
            "max_width_m",
            "Minimum width cannot be greater than maximum width.",
        ),
        (
            "min_height_m",
            "max_height_m",
            "Minimum height cannot be greater than maximum height.",
        ),
        (
            "min_length_m",
            "max_length_m",
            "Minimum length cannot be greater than maximum length.",
        ),
    ],
)
def test_invalid_sanity_ranges(
    client,
    minimum_field,
    maximum_field,
    expected_detail,
):

    payload = valid_payload()

    payload["input_sanity_range"][
        minimum_field
    ] = 100

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


@pytest.mark.parametrize(
    "profile_field, value, expected_detail",
    [
        (
            "default_width_m",
            4.0,
            "Default width must be within the input sanity width range.",
        ),
        (
            "default_height_m",
            6.0,
            "Default height must be within the input sanity height range.",
        ),
        (
            "default_length_m",
            20.0,
            "Default length must be within the input sanity length range.",
        ),
    ],
)
def test_default_dimensions_outside_sanity_range(
    client,
    profile_field,
    value,
    expected_detail,
):

    payload = valid_payload()

    payload["profile"][
        profile_field
    ] = value

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


@pytest.mark.parametrize(
    "rule_field, value, expected_detail",
    [
        (
            "width_limit_m",
            3.1,
            "Width legal limit cannot be greater than maximum sanity width.",
        ),
        (
            "height_limit_m",
            5.1,
            "Height legal limit cannot be greater than maximum sanity height.",
        ),
        (
            "length_limit_m",
            15.1,
            "Length legal limit cannot be greater than maximum sanity length.",
        ),
    ],
)
def test_legal_limits_above_sanity_range(
    client,
    rule_field,
    value,
    expected_detail,
):

    payload = valid_payload()

    payload["dimension_rule"][
        rule_field
    ] = value

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


def test_axle_config_required_when_configurable(
    client,
):

    payload = valid_payload()

    payload["axle_configurations"] = []

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "At least one axle configuration is required."
    )


def test_duplicate_profile_id(
    client,
    monkeypatch,
):

    payload = valid_payload()

    existing_profile = SimpleNamespace(
        profile_id="CUSTOM_RIGID_VEHICLE"
    )

    fake_db = FakeDB({
        VehicleProfile: [
            existing_profile,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "profile_id already exists. "
        "This page only supports adding new vehicles."
    )


def test_duplicate_template_id(
    client,
    monkeypatch,
):

    payload = valid_payload()

    existing_template = SimpleNamespace(
        template_id="CUSTOM_RIGID_TEMPLATE"
    )

    fake_db = FakeDB({
        VehicleProfile: [None],
        VehicleTemplate: [
            existing_template,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "template_id already exists. "
        "For the add-new-vehicle page, "
        "create a new template_id to avoid "
        "modifying existing vehicle types."
    )


def test_licence_missing_from_database(
    client,
    monkeypatch,
):

    payload = valid_payload()

    fake_db = FakeDB({
        VehicleProfile: [None],
        VehicleTemplate: [None],
        LicenceClass: [None],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "Invalid required licence class."
    )


def test_missing_axle_config_id(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload["axle_configurations"][0][
        "axle_config_id"
    ] = ""

    fake_db = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "axle_configurations[1].axle_config_id is required."
    )


def test_duplicate_axle_id_in_request(
    client,
    monkeypatch,
):

    payload = valid_payload()

    second_axle = copy.deepcopy(
        payload["axle_configurations"][0]
    )

    second_axle["display_name"] = (
        "Duplicate Axle"
    )

    payload[
        "axle_configurations"
    ].append(second_axle)

    fake_db = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Duplicate axle_config_id in request: "
        "CUSTOM_AXLE"
    )


def test_axle_id_already_exists_in_database(
    client,
    monkeypatch,
):

    payload = valid_payload()

    existing_axle = SimpleNamespace(
        axle_config_id="CUSTOM_AXLE",
    )

    fake_db = valid_fake_db()

    fake_db.results[
        AxleConfiguration
    ] = [
        existing_axle,
    ]

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "axle_config_id already exists: "
        "CUSTOM_AXLE"
    )


def test_missing_axle_display_name(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload["axle_configurations"][0][
        "display_name"
    ] = ""

    fake_db = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "axle_configurations[1].display_name is required."
    )


def test_invalid_axle_access_path(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload["axle_configurations"][0][
        "access_path"
    ] = "class_4"

    fake_db = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "axle_configurations[1].access_path must be "
        "general_access, class_1, class_2, or class_3."
    )


@pytest.mark.parametrize(
    "length",
    [
        4.99,
        15.01,
    ],
)
def test_axle_length_outside_sanity_range(
    client,
    monkeypatch,
    length,
):

    payload = valid_payload()

    payload["axle_configurations"][0][
        "max_length_m"
    ] = length

    fake_db = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Axle configuration max length for "
        "CUSTOM_AXLE must be within the "
        "input sanity length range."
    )


@pytest.mark.parametrize(
    "mass_field, expected_name",
    [
        (
            "gml_mass_t",
            "GML",
        ),
        (
            "cml_mass_t",
            "CML",
        ),
        (
            "hml_mass_t",
            "HML",
        ),
    ],
)
def test_negative_mass_limits_rejected(
    client,
    monkeypatch,
    mass_field,
    expected_name,
):

    payload = valid_payload()

    payload["axle_configurations"][0][
        mass_field
    ] = -1

    fake_db = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        f"{expected_name} mass cannot be "
        f"negative for CUSTOM_AXLE."
    )


def test_invalid_json_body(client):

    response = client.post(
        "/api/compliance/admin/vehicles",
        data="this is not json",
        content_type="text/plain",
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "Invalid or empty JSON body."
    )


def test_valid_vehicle_creation(
    client,
    monkeypatch,
):

    payload = valid_payload()

    fake_db = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/admin/vehicles",
        json=payload,
    )

    assert response.status_code == 201

    data = response.get_json()

    assert (
        data["message"]
        == "Vehicle added successfully."
    )

    assert (
        data["profile_id"]
        == "CUSTOM_RIGID_VEHICLE"
    )

    assert (
        data["template_id"]
        == "CUSTOM_RIGID_TEMPLATE"
    )

    assert data["axle_config_count"] == 1

    assert fake_db.commit_count == 1

    assert any(
        isinstance(obj, VehicleProfile)
        for obj in fake_db.added
    )

    assert any(
        isinstance(obj, VehicleTemplate)
        for obj in fake_db.added
    )

    assert any(
        isinstance(obj, DimensionRule)
        for obj in fake_db.added
    )

    assert any(
        isinstance(obj, InputSanityRange)
        for obj in fake_db.added
    )

    assert any(
        isinstance(obj, AxleConfiguration)
        for obj in fake_db.added
    )

    assert any(
        isinstance(obj, AxleGroupMass)
        for obj in fake_db.added
    )

    assert any(
        isinstance(obj, AxleConfigMassLimit)
        for obj in fake_db.added
    )