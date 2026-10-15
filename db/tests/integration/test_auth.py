# AUTHENTICATION + USER PROFILE TESTS

# SIGNUP
# missing email
# missing username
# missing password
# duplicate email
# duplicate username
# invalid licence
# invalid favourite vehicle
# valid signup

# LOGIN
# missing login
# missing password
# unknown user
# user has no password hash
# wrong password
# correct password

# PROFILE UPDATE
# missing licence
# unknown user
# invalid licence
# invalid favourite vehicle
# favourite vehicle requires higher licence
# valid profile update


import pytest

from flask import Flask
from types import SimpleNamespace
from werkzeug.security import generate_password_hash

from db.compliance import routes
from db.compliance.db_models import (
    User,
    LicenceClass,
    VehicleProfile,
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

    def query(self, model):

        model_results = self.results.get(model, [])

        if model_results:
            result = model_results.pop(0)
        else:
            result = None

        return FakeQuery(result)

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.commit_count += 1

    def refresh(self, obj):
        if getattr(obj, "user_id", None) is None:
            obj.user_id = 1

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
    "payload, expected_detail",
    [
        (
            {
                "username": "ben",
                "password": "Password123",
            },
            "Email is required.",
        ),
        (
            {
                "email": "ben@example.com",
                "password": "Password123",
            },
            "Username is required.",
        ),
        (
            {
                "email": "ben@example.com",
                "username": "ben",
            },
            "Password is required.",
        ),
    ],
)
def test_signup_missing_required_fields(
    client,
    payload,
    expected_detail,
):

    response = client.post(
        "/api/compliance/auth/signup",
        json=payload,
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["detail"] == expected_detail


def test_signup_duplicate_email(
    client,
    monkeypatch,
):

    existing_user = SimpleNamespace(
        email="ben@example.com",
    )

    fake_db = FakeDB({
        User: [existing_user],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/signup",
        json={
            "email": "ben@example.com",
            "username": "ben",
            "password": "Password123",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "Email already exists."
    )


def test_signup_duplicate_username(
    client,
    monkeypatch,
):

    existing_user = SimpleNamespace(
        username="ben",
    )

    fake_db = FakeDB({
        User: [
            None,
            existing_user,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/signup",
        json={
            "email": "new@example.com",
            "username": "ben",
            "password": "Password123",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "Username already exists."
    )


def test_signup_invalid_licence(
    client,
    monkeypatch,
):

    fake_db = FakeDB({
        User: [
            None,
            None,
        ],
        LicenceClass: [
            None,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/signup",
        json={
            "email": "ben@example.com",
            "username": "ben",
            "password": "Password123",
            "licence_class_id": "ABC",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "Invalid licence class."
    )


def test_signup_invalid_favourite_vehicle(
    client,
    monkeypatch,
):

    licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    fake_db = FakeDB({
        User: [
            None,
            None,
        ],
        LicenceClass: [
            licence,
        ],
        VehicleProfile: [
            None,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/signup",
        json={
            "email": "ben@example.com",
            "username": "ben",
            "password": "Password123",
            "licence_class_id": "HR",
            "favourite_profile_id":
                "DOES_NOT_EXIST",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "Invalid favourite vehicle profile."
    )


def test_valid_signup(
    client,
    monkeypatch,
):

    licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    profile = SimpleNamespace(
        profile_id="STANDARD_HR_RIGID",
    )

    fake_db = FakeDB({
        User: [
            None,
            None,
        ],
        LicenceClass: [
            licence,
        ],
        VehicleProfile: [
            profile,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/signup",
        json={
            "email": " BEN@EXAMPLE.COM ",
            "username": "Ben",
            "password": "Password123",
            "licence_class_id": "hr",
            "favourite_profile_id":
                "STANDARD_HR_RIGID",
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Signup successful."

    assert (
        data["user"]["email"]
        == "ben@example.com"
    )

    assert (
        data["user"]["licence_class_id"]
        == "HR"
    )

    assert (
        data["user"]["favourite_profile_id"]
        == "STANDARD_HR_RIGID"
    )

    assert len(fake_db.added) == 1

    created_user = fake_db.added[0]

    assert (
        created_user.password_hash
        != "Password123"
    )


@pytest.mark.parametrize(
    "payload, expected_detail",
    [
        (
            {
                "password": "Password123",
            },
            "Email or username is required.",
        ),
        (
            {
                "login": "ben@example.com",
            },
            "Password is required.",
        ),
    ],
)
def test_login_missing_required_fields(
    client,
    payload,
    expected_detail,
):

    response = client.post(
        "/api/compliance/auth/login",
        json=payload,
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == expected_detail
    )


def test_login_unknown_user(
    client,
    monkeypatch,
):

    fake_db = FakeDB({
        User: [None],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/login",
        json={
            "login": "unknown@example.com",
            "password": "Password123",
        },
    )

    assert response.status_code == 401

    assert (
        response.get_json()["detail"]
        ==
        "Invalid email/username or password."
    )


def test_login_user_without_password_hash(
    client,
    monkeypatch,
):

    user = SimpleNamespace(
        user_id=1,
        email="ben@example.com",
        username="ben",
        password_hash=None,
        licence_class_id="HR",
        favourite_profile_id=None,
    )

    fake_db = FakeDB({
        User: [user],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/login",
        json={
            "login": "ben@example.com",
            "password": "Password123",
        },
    )

    assert response.status_code == 401


def test_login_wrong_password(
    client,
    monkeypatch,
):

    user = SimpleNamespace(
        user_id=1,
        email="ben@example.com",
        username="ben",
        password_hash=
            generate_password_hash(
                "CorrectPassword"
            ),
        licence_class_id="HR",
        favourite_profile_id=None,
    )

    fake_db = FakeDB({
        User: [user],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/login",
        json={
            "login": "ben@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401


def test_login_correct_password(
    client,
    monkeypatch,
):

    user = SimpleNamespace(
        user_id=1,
        email="ben@example.com",
        username="ben",
        password_hash=
            generate_password_hash(
                "Password123"
            ),
        licence_class_id="HR",
        favourite_profile_id=
            "STANDARD_HR_RIGID",
    )

    fake_db = FakeDB({
        User: [user],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.post(
        "/api/compliance/auth/login",
        json={
            "login": "BEN@EXAMPLE.COM",
            "password": "Password123",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Login successful."

    assert data["user"]["user_id"] == 1

    assert (
        data["user"]["email"]
        == "ben@example.com"
    )


def test_profile_update_missing_licence(
    client,
):

    response = client.put(
        "/api/compliance/auth/users/1/profile",
        json={
            "favourite_profile_id":
                "STANDARD_HR_RIGID",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "licence_class_id is required."
    )


def test_profile_update_unknown_user(
    client,
    monkeypatch,
):

    fake_db = FakeDB({
        User: [None],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/auth/users/99/profile",
        json={
            "licence_class_id": "HR",
        },
    )

    assert response.status_code == 404

    assert (
        response.get_json()["detail"]
        == "User not found."
    )


def test_profile_update_invalid_licence(
    client,
    monkeypatch,
):

    user = SimpleNamespace(
        user_id=1,
        licence_class_id="HR",
        favourite_profile_id=None,
    )

    fake_db = FakeDB({
        User: [user],
        LicenceClass: [None],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/auth/users/1/profile",
        json={
            "licence_class_id": "ABC",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        == "Invalid licence class."
    )


def test_profile_update_invalid_favourite(
    client,
    monkeypatch,
):

    user = SimpleNamespace(
        user_id=1,
        email="ben@example.com",
        username="ben",
        licence_class_id="HR",
        favourite_profile_id=None,
    )

    selected_licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    fake_db = FakeDB({
        User: [user],
        LicenceClass: [
            selected_licence,
        ],
        VehicleProfile: [
            None,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/auth/users/1/profile",
        json={
            "licence_class_id": "HR",
            "favourite_profile_id":
                "DOES_NOT_EXIST",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Invalid favourite vehicle profile."
    )


def test_favourite_vehicle_requires_allowed_licence(
    client,
    monkeypatch,
):

    user = SimpleNamespace(
        user_id=1,
        email="ben@example.com",
        username="ben",
        licence_class_id="HR",
        favourite_profile_id=None,
    )

    selected_licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    favourite_profile = SimpleNamespace(
        profile_id="STANDARD_B_DOUBLE",
        required_licence_class_id="MC",
    )

    required_licence = SimpleNamespace(
        licence_class_id="MC",
        rank_value=5,
    )

    fake_db = FakeDB({
        User: [user],
        LicenceClass: [
            selected_licence,
            required_licence,
        ],
        VehicleProfile: [
            favourite_profile,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/auth/users/1/profile",
        json={
            "licence_class_id": "HR",
            "favourite_profile_id":
                "STANDARD_B_DOUBLE",
        },
    )

    assert response.status_code == 400

    assert (
        response.get_json()["detail"]
        ==
        "Selected favourite vehicle is not allowed "
        "for this licence class."
    )


def test_valid_profile_update(
    client,
    monkeypatch,
):

    user = SimpleNamespace(
        user_id=1,
        email="ben@example.com",
        username="ben",
        licence_class_id="MR",
        favourite_profile_id=None,
    )

    selected_licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    favourite_profile = SimpleNamespace(
        profile_id="STANDARD_HR_RIGID",
        required_licence_class_id="HR",
    )

    required_licence = SimpleNamespace(
        licence_class_id="HR",
        rank_value=3,
    )

    fake_db = FakeDB({
        User: [user],
        LicenceClass: [
            selected_licence,
            required_licence,
        ],
        VehicleProfile: [
            favourite_profile,
        ],
    })

    monkeypatch.setattr(
        routes,
        "get_db_session",
        lambda: fake_db,
    )

    response = client.put(
        "/api/compliance/auth/users/1/profile",
        json={
            "licence_class_id": "HR",
            "favourite_profile_id":
                "STANDARD_HR_RIGID",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert (
        data["message"]
        == "Profile updated successfully."
    )

    assert (
        data["user"]["licence_class_id"]
        == "HR"
    )

    assert (
        data["user"]["favourite_profile_id"]
        == "STANDARD_HR_RIGID"
    )