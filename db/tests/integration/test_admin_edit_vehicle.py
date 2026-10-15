# ADMIN EDIT VEHICLE TESTS
#
# This test file checks the
# PUT /api/compliance/admin/vehicles/<profile_id> endpoint.
#
# It tests:
# - invalid JSON requests
# - preventing profile ID changes
# - required vehicle fields
# - licence validation
# - classification validation
# - minimum and maximum sanity ranges
# - default dimensions staying inside sanity ranges
# - legal dimension limits staying inside sanity ranges
# - axle configuration being required when enabled
# - vehicle profile existing in the database
# - preventing template ID changes
# - preventing category ID changes
# - licence existing in the database
# - duplicate axle configuration IDs
# - axle display name being required
# - valid axle access paths
# - axle maximum length staying inside sanity ranges
# - axle group masses being required
# - negative GML, CML and HML values being rejected
# - axle configuration belonging to the correct template
# - required mass schemes existing
# - updating an existing axle configuration
# - adding a new axle configuration during editing
# - successful database commit
# - rollback when a database error occurs
#
# FakeDB is used for database operations, so these tests do not
# modify records in the real PostgreSQL database.


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
    MassScheme,
)


class FakeQuery:
    def __init__(self, db, result=None):
        self.db = db
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result

    def delete(self, *args, **kwargs):
        self.db.delete_count += 1
        return 1


class FakeDB:
    def __init__(
        self,
        results=None,
        fail_commit=False,
    ):
        self.results = results or {}
        self.fail_commit = fail_commit

        self.added = []
        self.commit_count = 0
        self.rollback_count = 0
        self.flush_count = 0
        self.delete_count = 0

    def query(self, model):

        model_results = self.results.get(model, [])

        if model_results:
            result = model_results.pop(0)
        else:
            result = None

        return FakeQuery(
            self,
            result,
        )

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flush_count += 1

    def commit(self):

        if self.fail_commit:
            raise RuntimeError(
                "Simulated database failure"
            )

        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        pass


@pytest.fixture
def app():

    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(
        routes.compliance_bp
    )

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def valid_payload():

    return {
        "category": {
            "category_id": "heavy_vehicle",
            "category_name": "Heavy Vehicle",
        },

        "template": {
            "template_id":
                "CUSTOM_RIGID_TEMPLATE",

            "template_name":
                "Updated Rigid Template",

            "base_type": "rigid",
        },

        "profile": {
            "profile_id":
                "CUSTOM_RIGID_VEHICLE",

            "display_name":
                "Updated Rigid Vehicle",

            "vehicle_family": "Rigid",

            "combination_type": "Single",

            "gvm_category": "Heavy",

            "axle_count": 3,

            "axle_configurable": True,

            "default_width_m": 2.5,

            "default_height_m": 4.3,

            "default_length_m": 12.0,

            "allow_custom_dimensions": True,

            "required_licence_class_id":
                "HR",
        },

        "dimension_rule": {
            "rule_name":
                "Updated Rigid Rule",

            "width_limit_m": 2.5,

            "height_limit_m": 4.3,

            "length_limit_m": 12.5,

            "classification_if_exceeded_limit":
                "class_3",

            "note": "Updated rule",
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
                "axle_config_id":
                    "CUSTOM_AXLE",

                "display_name":
                    "Updated 3 Axle",

                "max_length_m": 12.5,

                "access_path":
                    "general_access",

                "axle_group_masses_t": [
                    6.0,
                    16.5,
                ],

                "gml_mass_t": 22.5,

                "cml_mass_t": 23.0,

                "hml_mass_t": None,

                "note": "Updated axle",
            }
        ],
    }


def make_existing_profile():

    return SimpleNamespace(
        profile_id=
            "CUSTOM_RIGID_VEHICLE",

        template_id=
            "CUSTOM_RIGID_TEMPLATE",

        category_id=
            "heavy_vehicle",

        display_name=
            "Old Vehicle",

        vehicle_family="Rigid",

        combination_type="Single",

        gvm_category="Heavy",

        axle_count=3,

        axle_configurable=True,

        default_width_m=2.5,

        default_height_m=4.3,

        default_length_m=12.0,

        allow_custom_dimensions=True,

        required_licence_class_id="HR",
    )


def make_existing_axle():

    return SimpleNamespace(
        axle_config_id="CUSTOM_AXLE",

        template_id=
            "CUSTOM_RIGID_TEMPLATE",

        display_name="Old Axle",

        max_length_m=12.0,

        access_path="general_access",

        note=None,
    )


def make_dimension_rule():

    return SimpleNamespace(
        template_id=
            "CUSTOM_RIGID_TEMPLATE",

        rule_name="Old Rule",

        width_limit_m=2.5,

        height_limit_m=4.3,

        length_limit_m=12.5,

        classification_if_exceeded_limit=
            "class_3",

        note=None,
    )


def make_sanity_range():

    return SimpleNamespace(
        template_id=
            "CUSTOM_RIGID_TEMPLATE",

        min_width_m=2.0,
        max_width_m=3.0,

        min_height_m=3.0,
        max_height_m=5.0,

        min_length_m=5.0,
        max_length_m=15.0,
    )


def valid_fake_db(
    existing_axle=True,
    fail_commit=False,
):

    profile = make_existing_profile()

    category = SimpleNamespace(
        category_id="heavy_vehicle",
        category_name="Heavy Vehicle",
    )

    template = SimpleNamespace(
        template_id=
            "CUSTOM_RIGID_TEMPLATE",

        template_name=
            "Old Template",

        base_type="rigid",
    )

    licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    axle = (
        make_existing_axle()
        if existing_axle
        else None
    )

    gml = SimpleNamespace(
        mass_scheme_id="GML",
    )

    cml = SimpleNamespace(
        mass_scheme_id="CML",
    )

    hml = SimpleNamespace(
        mass_scheme_id="HML",
    )

    gml_limit = SimpleNamespace(
        mass_scheme_id="GML",
        mass_limit_t=20.0,
    )

    cml_limit = SimpleNamespace(
        mass_scheme_id="CML",
        mass_limit_t=21.0,
    )

    hml_limit = SimpleNamespace(
        mass_scheme_id="HML",
        mass_limit_t=None,
    )

    db = FakeDB(
        {
            VehicleProfile: [
                profile,
            ],

            LicenceClass: [
                licence,
            ],

            VehicleCategory: [
                category,
            ],

            VehicleTemplate: [
                template,
            ],

            DimensionRule: [
                make_dimension_rule(),
            ],

            InputSanityRange: [
                make_sanity_range(),
            ],

            AxleConfiguration: [
                axle,
            ],

            MassScheme: [
                gml,
                cml,
                hml,
            ],

            AxleConfigMassLimit: [
                gml_limit,
                cml_limit,
                hml_limit,
            ],
        },
        fail_commit=fail_commit,
    )

    return (
        db,
        profile,
        axle,
        gml_limit,
        cml_limit,
        hml_limit,
    )


def test_invalid_json_body(client):

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        data="not json",
        content_type="text/plain",
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Invalid or empty JSON body."
    )


def test_profile_id_cannot_be_changed(
    client,
):

    payload = valid_payload()

    payload["profile"][
        "profile_id"
    ] = "DIFFERENT_VEHICLE"

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "profile_id cannot be changed on "
        "the edit page. Create a new vehicle instead."
    )


@pytest.mark.parametrize(
    "section, field, expected_detail",
    [
        (
            "category",
            "category_name",
            "category_name is required.",
        ),
        (
            "template",
            "template_name",
            "template_name is required.",
        ),
        (
            "template",
            "base_type",
            "base_type is required.",
        ),
        (
            "profile",
            "display_name",
            "display_name is required.",
        ),
        (
            "profile",
            "vehicle_family",
            "vehicle_family is required.",
        ),
        (
            "profile",
            "combination_type",
            "combination_type is required.",
        ),
    ],
)
def test_missing_required_fields(
    client,
    section,
    field,
    expected_detail,
):

    payload = valid_payload()

    payload[section][field] = ""

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


def test_invalid_required_licence(
    client,
):

    payload = valid_payload()

    payload["profile"][
        "required_licence_class_id"
    ] = "ABC"

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "required_licence_class_id must be "
        "LR, MR, HR, HC, or MC."
    )


def test_invalid_classification(
    client,
):

    payload = valid_payload()

    payload["dimension_rule"][
        "classification_if_exceeded_limit"
    ] = "class_4"

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "minimum, maximum, expected_detail",
    [
        (
            "min_width_m",
            "max_width_m",
            "Minimum width cannot be greater "
            "than maximum width.",
        ),
        (
            "min_height_m",
            "max_height_m",
            "Minimum height cannot be greater "
            "than maximum height.",
        ),
        (
            "min_length_m",
            "max_length_m",
            "Minimum length cannot be greater "
            "than maximum length.",
        ),
    ],
)
def test_invalid_sanity_ranges(
    client,
    minimum,
    maximum,
    expected_detail,
):

    payload = valid_payload()

    payload["input_sanity_range"][
        minimum
    ] = 100

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


@pytest.mark.parametrize(
    "field, value, expected_detail",
    [
        (
            "default_width_m",
            4.0,
            "Default width must be within "
            "the input sanity width range.",
        ),
        (
            "default_height_m",
            6.0,
            "Default height must be within "
            "the input sanity height range.",
        ),
        (
            "default_length_m",
            20.0,
            "Default length must be within "
            "the input sanity length range.",
        ),
    ],
)
def test_default_dimensions_outside_range(
    client,
    field,
    value,
    expected_detail,
):

    payload = valid_payload()

    payload["profile"][field] = value

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


@pytest.mark.parametrize(
    "field, value, expected_detail",
    [
        (
            "width_limit_m",
            3.1,
            "Width legal limit cannot be "
            "greater than maximum sanity width.",
        ),
        (
            "height_limit_m",
            5.1,
            "Height legal limit cannot be "
            "greater than maximum sanity height.",
        ),
        (
            "length_limit_m",
            15.1,
            "Length legal limit cannot be "
            "greater than maximum sanity length.",
        ),
    ],
)
def test_legal_limits_outside_range(
    client,
    field,
    value,
    expected_detail,
):

    payload = valid_payload()

    payload["dimension_rule"][
        field
    ] = value

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


def test_axle_required_when_configurable(
    client,
):

    payload = valid_payload()

    payload[
        "axle_configurations"
    ] = []

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "At least one axle configuration is required."
    )


def test_vehicle_profile_not_found(
    client,
    monkeypatch,
):

    payload = valid_payload()

    fake_db = FakeDB({
        VehicleProfile: [None],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 404

    assert (
        response.get_json()["detail"]
        ==
        "Vehicle profile not found."
    )


def test_template_id_cannot_change(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload["template"][
        "template_id"
    ] = "DIFFERENT_TEMPLATE"

    fake_db = FakeDB({
        VehicleProfile: [
            make_existing_profile()
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "template_id cannot be changed on "
        "the edit page."
    )


def test_category_id_cannot_change(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload["category"][
        "category_id"
    ] = "different_category"

    fake_db = FakeDB({
        VehicleProfile: [
            make_existing_profile()
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "category_id cannot be changed on "
        "the edit page."
    )


def test_licence_not_found_in_database(
    client,
    monkeypatch,
):

    payload = valid_payload()

    fake_db = FakeDB({
        VehicleProfile: [
            make_existing_profile()
        ],

        LicenceClass: [
            None
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Invalid required licence class."
    )


def test_duplicate_axle_id_in_request(
    client,
    monkeypatch,
):

    payload = valid_payload()

    second_axle = copy.deepcopy(
        payload["axle_configurations"][0]
    )

    payload[
        "axle_configurations"
    ].append(second_axle)

    fake_db, *_ = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Duplicate axle_config_id in request: "
        "CUSTOM_AXLE"
    )


def test_missing_axle_display_name(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload[
        "axle_configurations"
    ][0]["display_name"] = ""

    fake_db, *_ = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "axle_configurations[1].display_name "
        "is required."
    )


def test_invalid_axle_access_path(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload[
        "axle_configurations"
    ][0]["access_path"] = "class_4"

    fake_db, *_ = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400


@pytest.mark.parametrize(
    "length",
    [
        4.99,
        15.01,
    ],
)
def test_axle_length_outside_range(
    client,
    monkeypatch,
    length,
):

    payload = valid_payload()

    payload[
        "axle_configurations"
    ][0]["max_length_m"] = length

    fake_db, *_ = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        "must be within the input sanity length range"
        in response.get_json()["detail"]
    )


def test_axle_group_mass_required(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload[
        "axle_configurations"
    ][0]["axle_group_masses_t"] = []

    fake_db, *_ = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "At least one axle group mass "
        "is required for CUSTOM_AXLE."
    )


@pytest.mark.parametrize(
    "field, scheme",
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
def test_negative_mass_limits(
    client,
    monkeypatch,
    field,
    scheme,
):

    payload = valid_payload()

    payload[
        "axle_configurations"
    ][0][field] = -1

    fake_db, *_ = valid_fake_db()

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        f"{scheme} mass cannot be negative "
        f"for CUSTOM_AXLE."
    )


def test_axle_from_another_template_rejected(
    client,
    monkeypatch,
):

    payload = valid_payload()

    wrong_axle = SimpleNamespace(
        axle_config_id="CUSTOM_AXLE",
        template_id="B_DOUBLE",
    )

    fake_db, *_ = valid_fake_db()

    fake_db.results[
        AxleConfiguration
    ] = [
        wrong_axle
    ]

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Axle config CUSTOM_AXLE belongs "
        "to another template and cannot "
        "be edited here."
    )


def test_missing_mass_scheme_rejected(
    client,
    monkeypatch,
):

    payload = valid_payload()

    fake_db, *_ = valid_fake_db()

    fake_db.results[
        MassScheme
    ] = [
        None
    ]

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Mass scheme GML does not exist "
        "in compliance.mass_schemes."
    )


def test_successfully_update_existing_axle(
    client,
    monkeypatch,
):

    payload = valid_payload()

    (
        fake_db,
        existing_profile,
        existing_axle,
        gml_limit,
        cml_limit,
        hml_limit,
    ) = valid_fake_db(
        existing_axle=True
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 200

    data = response.get_json()

    assert (
        data["message"]
        ==
        "Vehicle updated successfully."
    )

    assert (
        data["profile_id"]
        ==
        "CUSTOM_RIGID_VEHICLE"
    )

    assert (
        data["template_id"]
        ==
        "CUSTOM_RIGID_TEMPLATE"
    )

    assert data["axle_config_count"] == 1

    assert fake_db.commit_count == 1

    assert fake_db.delete_count == 1

    assert (
        existing_profile.display_name
        ==
        "Updated Rigid Vehicle"
    )

    assert (
        existing_profile.default_length_m
        == 12.0
    )

    assert (
        existing_axle.display_name
        ==
        "Updated 3 Axle"
    )

    assert (
        existing_axle.max_length_m
        == 12.5
    )

    assert (
        existing_axle.access_path
        ==
        "general_access"
    )

    assert gml_limit.mass_limit_t == 22.5

    assert cml_limit.mass_limit_t == 23.0

    assert hml_limit.mass_limit_t is None


def test_successfully_add_new_axle_during_edit(
    client,
    monkeypatch,
):

    payload = valid_payload()

    payload[
        "axle_configurations"
    ][0]["axle_config_id"] = "NEW_AXLE"

    payload[
        "axle_configurations"
    ][0]["display_name"] = "New Axle"

    (
        fake_db,
        existing_profile,
        _,
        _,
        _,
        _,
    ) = valid_fake_db(
        existing_axle=False
    )

    fake_db.results[
        AxleConfigMassLimit
    ] = [
        None,
        None,
        None,
    ]

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 200

    assert fake_db.commit_count == 1

    assert any(
        isinstance(
            obj,
            AxleConfiguration,
        )
        for obj in fake_db.added
    )

    assert (
        sum(
            isinstance(
                obj,
                AxleConfigMassLimit,
            )
            for obj in fake_db.added
        )
        == 3
    )


def test_database_failure_causes_rollback(
    client,
    monkeypatch,
):

    payload = valid_payload()

    fake_db, *_ = valid_fake_db(
        fail_commit=True
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/admin/vehicles/"
        "CUSTOM_RIGID_VEHICLE",
        json=payload,
    )

    assert response.status_code == 500

    data = response.get_json()

    assert (
        data["detail"]
        ==
        "Failed to update vehicle."
    )

    assert fake_db.rollback_count == 1