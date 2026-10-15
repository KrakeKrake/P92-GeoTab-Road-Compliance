# LICENCE TESTS
#
# LR
# should allow LR
# should not allow MR, HR, HC, MC
#
# MR
# should allow LR and MR
# should not allow HR, HC, MC
#
# HR
# should allow LR, MR and HR
# should not allow HC, MC
#
# HC
# should allow LR, MR, HR and HC
# should not allow MC
#
# MC
# should allow LR, MR, HR, HC and MC
#
# invalid licence
# should return empty list


# MASS VALIDATION TESTS
#
# GML
# below limit should pass
# exactly at limit should pass
# above limit should fail
#
# CML
# below limit should pass
# exactly at limit should pass
# above limit should fail
#
# HML
# below limit should pass
# exactly at limit should pass
# above limit should fail
#
# non-applicable mass scheme
# should return not_applicable
#
# different axle configurations
# should retrieve their actual database limits


import pytest

from flask import Flask

from db.compliance import routes


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    app.register_blueprint(routes.compliance_bp)

    return app


@pytest.fixture
def client(app):
    return app.test_client()


# LICENCE HIERARCHY
@pytest.mark.parametrize(
    "licence, allowed_profiles, forbidden_profiles",
    [
        (
            "LR",
            {
                "STANDARD_LR_RIGID",
            },
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
def test_full_licence_hierarchy_real_database(
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

    assert returned_profiles.isdisjoint(
        forbidden_profiles
    )


def test_invalid_licence_real_database(client):

    response = client.get(
        "/api/compliance/profiles-by-licence/INVALID"
    )

    assert response.status_code == 200
    assert response.get_json() == []


# GML / CML / HML BOUNDARY TESTS
@pytest.mark.parametrize(
    "scheme, operating_mass, expected_status, expected_compliant, expected_limit",
    [
        # GML = 42.5
        (
            "GML",
            42.49,
            "ok",
            True,
            42.5,
        ),
        (
            "GML",
            42.50,
            "ok",
            True,
            42.5,
        ),
        (
            "GML",
            42.51,
            "exceeds_limit",
            False,
            42.5,
        ),

        # CML = 43.5
        (
            "CML",
            43.49,
            "ok",
            True,
            43.5,
        ),
        (
            "CML",
            43.50,
            "ok",
            True,
            43.5,
        ),
        (
            "CML",
            43.51,
            "exceeds_limit",
            False,
            43.5,
        ),

        # HML = 45.5
        (
            "HML",
            45.49,
            "ok",
            True,
            45.5,
        ),
        (
            "HML",
            45.50,
            "ok",
            True,
            45.5,
        ),
        (
            "HML",
            45.51,
            "exceeds_limit",
            False,
            45.5,
        ),
    ],
)
def test_real_database_mass_boundaries(
    client,
    scheme,
    operating_mass,
    expected_status,
    expected_compliant,
    expected_limit,
):

    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "axle_config_id":
                "SEMI_6_AXLE_6_16_5_20",

            "mass_scheme":
                scheme,

            "operating_mass_t":
                operating_mass,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == expected_status

    assert (
        data["compliant"]
        is expected_compliant
    )

    assert (
        data["selected_limit_t"]
        == expected_limit
    )

# NON-APPLICABLE MASS SCHEMES
@pytest.mark.parametrize(
    "scheme",
    [
        "CML",
        "HML",
    ],
)
def test_real_database_non_applicable_mass_scheme(
    client,
    scheme,
):

    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "axle_config_id":
                "RIGID_2_AXLE",

            "mass_scheme":
                scheme,

            "operating_mass_t":
                10.0,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "not_applicable"
    assert data["compliant"] is False
    assert data["selected_limit_t"] is None


# DIFFERENT AXLE CONFIGURATIONS
@pytest.mark.parametrize(
    "axle_config_id, expected_limit",
    [
        (
            "RIGID_2_AXLE",
            15.0,
        ),
        (
            "SEMI_6_AXLE_6_16_5_20",
            42.5,
        ),
        (
            "B_DOUBLE_9_AXLE_6_16_5_20_20",
            62.5,
        ),
    ],
)
def test_different_axle_configs_use_correct_gml_limit(
    client,
    axle_config_id,
    expected_limit,
):

    response = client.post(
        "/api/compliance/validate-mass",
        json={
            "axle_config_id":
                axle_config_id,

            "mass_scheme":
                "GML",

            "operating_mass_t":
                expected_limit,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"
    assert data["compliant"] is True

    assert (
        data["selected_limit_t"]
        == expected_limit
    )