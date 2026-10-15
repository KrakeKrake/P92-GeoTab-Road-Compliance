# valid HR licence
# fake database contains 2 allowed vehicle profiles
# should return both profiles

# invalid licence
# licence does not exist
# should return an empty list

# LR licence
# should allow LR
# should not allow MR, HR, HC, MC

# MR licence
# should allow LR and MR
# should not allow HR, HC, MC

# HR licence
# should allow LR, MR and HR
# should not allow HC, MC

# HC licence
# should allow LR, MR, HR and HC
# should not allow MC

# MC licence
# should allow LR, MR, HR, HC and MC

# invalid licence
# should return empty list

import pytest

from flask import Flask
from types import SimpleNamespace

from db.compliance import routes
from db.compliance.db_models import (
    LicenceClass,
    VehicleProfile,
)


class FakeQuery:
    def __init__(self, result=None, results=None):
        self.result = result
        self.results = results or []

    def join(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result

    def all(self):
        return self.results


class FakeDB:
    def __init__(self, licence=None, profiles=None):
        self.licence = licence
        self.profiles = profiles or []

    def query(self, model):
        if model == LicenceClass:
            return FakeQuery(result=self.licence)

        if model == VehicleProfile:
            return FakeQuery(results=self.profiles)

        return FakeQuery()

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


def test_valid_licence_returns_vehicle_profiles(
    client,
    monkeypatch,
):
    licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    profiles = [
        SimpleNamespace(
            profile_id="RIGID_TRUCK",
            display_name="Rigid Truck",
        ),
        SimpleNamespace(
            profile_id="HEAVY_RIGID",
            display_name="Heavy Rigid Truck",
        ),
    ]

    fake_db = FakeDB(
        licence=licence,
        profiles=profiles,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.get(
        "/api/compliance/profiles-by-licence/HR"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data) == 2

    assert data[0]["profile_id"] == "RIGID_TRUCK"
    assert data[1]["profile_id"] == "HEAVY_RIGID"


def test_invalid_licence_returns_empty_list(
    client,
    monkeypatch,
):
    fake_db = FakeDB(
        licence=None,
    )

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.get(
        "/api/compliance/profiles-by-licence/INVALID"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data == []

@pytest.mark.parametrize(
    "licence, allowed_profiles, forbidden_profiles",
    [
        (
            "LR",
            {"STANDARD_LR_RIGID"},
            {
                "STANDARD_MR_RIGID",
                "STANDARD_HR_RIGID",
                "STANDARD_PM_SEMI",
                "STANDARD_B_DOUBLE",
            },
        ),
        (
            "MR",
            {
                "STANDARD_LR_RIGID",
                "STANDARD_MR_RIGID",
            },
            {
                "STANDARD_HR_RIGID",
                "STANDARD_PM_SEMI",
                "STANDARD_B_DOUBLE",
            },
        ),
        (
            "HR",
            {
                "STANDARD_LR_RIGID",
                "STANDARD_MR_RIGID",
                "STANDARD_HR_RIGID",
            },
            {
                "STANDARD_PM_SEMI",
                "STANDARD_B_DOUBLE",
            },
        ),
        (
            "HC",
            {
                "STANDARD_LR_RIGID",
                "STANDARD_MR_RIGID",
                "STANDARD_HR_RIGID",
                "STANDARD_PM_SEMI",
            },
            {
                "STANDARD_B_DOUBLE",
            },
        ),
        (
            "MC",
            {
                "STANDARD_LR_RIGID",
                "STANDARD_MR_RIGID",
                "STANDARD_HR_RIGID",
                "STANDARD_PM_SEMI",
                "STANDARD_B_DOUBLE",
            },
            set(),
        ),
    ],
)
def test_full_licence_hierarchy(
    client,
    licence,
    allowed_profiles,
    forbidden_profiles,
):

    response = client.get(
        f"/api/compliance/profiles-by-licence/{licence}"
    )

    assert response.status_code == 200

    data = response.get_json()

    returned_profiles = {
        profile["profile_id"]
        for profile in data
    }

    assert allowed_profiles.issubset(returned_profiles)
    assert returned_profiles.isdisjoint(forbidden_profiles)

def test_invalid_licence_real_database(client):

    response = client.get(
        "/api/compliance/profiles-by-licence/INVALID"
    )

    assert response.status_code == 200
    assert response.get_json() == []