# CLASSIFIER INTENSIVE UNIT TESTS

# DIMENSION BOUNDARIES
#
# width below limit
# should pass
#
# width exactly at limit
# should pass
#
# width above limit
# should become class_3
#
# height below limit
# should pass
#
# height exactly at limit
# should pass
#
# height above limit
# should become class_3
#
# length below limit
# should pass
#
# length exactly at limit
# should pass
#
# length above limit
# should become class_3


# CUSTOM DIMENSION ERRORS
#
# missing width
# should return error
#
# missing height
# should return error
#
# missing length
# should return error
#
# all dimensions missing
# should return error


# PROFILE / RULE ERRORS
#
# unknown profile
# should return unknown
#
# missing dimension rule
# should return unknown
#
# invalid axle configuration
# should return unknown


# AXLE CONFIGURATION
#
# valid semitrailer axle configuration
# should use general_access
#
# valid B-double axle configuration
# should use class_2
#
# B-double axle-specific length limit
# should use 26.0 m instead of general 25.0 m
#
# B-double exceeding axle-specific limit
# should become class_3


# MULTIPLE VIOLATIONS
#
# width, height and length all exceed limits
# should become class_3
# should produce 3 warnings


import pytest

from types import SimpleNamespace

from db.compliance.db_classifier import classify_hvnl_from_db
from db.compliance.db_models import (
    VehicleProfile,
    DimensionRule,
    AxleConfiguration,
)


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self.result


class FakeDB:
    def __init__(
        self,
        profile=None,
        dimension_rule=None,
        axle_config=None,
    ):
        self.profile = profile
        self.dimension_rule = dimension_rule
        self.axle_config = axle_config

    def query(self, model):

        if model == VehicleProfile:
            return FakeQuery(self.profile)

        if model == DimensionRule:
            return FakeQuery(self.dimension_rule)

        if model == AxleConfiguration:
            return FakeQuery(self.axle_config)

        return FakeQuery(None)


def rigid_profile():

    return SimpleNamespace(
        profile_id="RIGID_STANDARD",
        template_id="RIGID_TRUCK",
        display_name="Standard Rigid Truck",
        default_width_m=2.5,
        default_height_m=4.3,
        default_length_m=12.5,
    )


def rigid_dimension_rule():

    return SimpleNamespace(
        template_id="RIGID_TRUCK",
        width_limit_m=2.5,
        height_limit_m=4.3,
        length_limit_m=12.5,
        classification_if_exceeded_limit="class_3",
    )


@pytest.mark.parametrize(
    "width, height, length, expected_classification, expected_warning_count",
    [
        (2.49, 4.3, 12.5, "general_access", 0),
        (2.50, 4.3, 12.5, "general_access", 0),
        (2.51, 4.3, 12.5, "class_3", 1),

        (2.5, 4.29, 12.5, "general_access", 0),
        (2.5, 4.30, 12.5, "general_access", 0),
        (2.5, 4.31, 12.5, "class_3", 1),

        (2.5, 4.3, 12.49, "general_access", 0),
        (2.5, 4.3, 12.50, "general_access", 0),
        (2.5, 4.3, 12.51, "class_3", 1),
    ],
)
def test_dimension_boundaries(
    width,
    height,
    length,
    expected_classification,
    expected_warning_count,
):

    db = FakeDB(
        profile=rigid_profile(),
        dimension_rule=rigid_dimension_rule(),
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="RIGID_STANDARD",
        custom_dimensions=True,
        answers={
            "overall_width_m": width,
            "overall_height_m": height,
            "overall_length_m": length,
        },
    )

    assert result["status"] == "ok"

    assert (
        result["classification"]
        == expected_classification
    )

    assert (
        len(result["warnings"])
        == expected_warning_count
    )


def test_all_dimensions_exceeded():

    db = FakeDB(
        profile=rigid_profile(),
        dimension_rule=rigid_dimension_rule(),
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="RIGID_STANDARD",
        custom_dimensions=True,
        answers={
            "overall_width_m": 2.6,
            "overall_height_m": 4.4,
            "overall_length_m": 13.0,
        },
    )

    assert result["status"] == "ok"
    assert result["classification"] == "class_3"
    assert len(result["warnings"]) == 3


@pytest.mark.parametrize(
    "answers, expected_missing_fields",
    [
        (
            {
                "overall_height_m": 4.3,
                "overall_length_m": 12.5,
            },
            ["width_m"],
        ),
        (
            {
                "overall_width_m": 2.5,
                "overall_length_m": 12.5,
            },
            ["height_m"],
        ),
        (
            {
                "overall_width_m": 2.5,
                "overall_height_m": 4.3,
            },
            ["length_m"],
        ),
        (
            {},
            [
                "width_m",
                "height_m",
                "length_m",
            ],
        ),
    ],
)
def test_missing_custom_dimensions(
    answers,
    expected_missing_fields,
):

    db = FakeDB(
        profile=rigid_profile(),
        dimension_rule=rigid_dimension_rule(),
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="RIGID_STANDARD",
        custom_dimensions=True,
        answers=answers,
    )

    assert result["status"] == "error"
    assert result["classification"] == "unknown"

    assert (
        result["missing_fields"]
        == expected_missing_fields
    )


def test_unknown_vehicle_profile_returns_error():

    db = FakeDB(
        profile=None,
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="DOES_NOT_EXIST",
    )

    assert result["status"] == "error"
    assert result["classification"] == "unknown"
    assert result["reason"] == "Vehicle profile not found."


def test_missing_dimension_rule_returns_error():

    db = FakeDB(
        profile=rigid_profile(),
        dimension_rule=None,
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="RIGID_STANDARD",
    )

    assert result["status"] == "error"
    assert result["classification"] == "unknown"


def test_invalid_axle_configuration_returns_error():

    profile = SimpleNamespace(
        profile_id="SEMI_STANDARD",
        template_id="PM_SEMI",
        display_name="Prime Mover + Semi",
        default_width_m=2.5,
        default_height_m=4.3,
        default_length_m=19.0,
    )

    dimension_rule = SimpleNamespace(
        template_id="PM_SEMI",
        width_limit_m=2.5,
        height_limit_m=4.3,
        length_limit_m=19.0,
        classification_if_exceeded_limit="class_3",
    )

    db = FakeDB(
        profile=profile,
        dimension_rule=dimension_rule,
        axle_config=None,
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="SEMI_STANDARD",
        axle_config_id="INVALID_AXLE",
    )

    assert result["status"] == "error"
    assert result["classification"] == "unknown"
    assert "axle_config_id" in result["missing_fields"]


def test_semitrailer_axle_config_uses_general_access():

    profile = SimpleNamespace(
        profile_id="SEMI_STANDARD",
        template_id="PM_SEMI",
        display_name="Prime Mover + Semi",
        default_width_m=2.5,
        default_height_m=4.3,
        default_length_m=19.0,
    )

    dimension_rule = SimpleNamespace(
        template_id="PM_SEMI",
        width_limit_m=2.5,
        height_limit_m=4.3,
        length_limit_m=19.0,
        classification_if_exceeded_limit="class_3",
    )

    axle_config = SimpleNamespace(
        axle_config_id="SEMI_6_AXLE",
        display_name="6 Axle Semitrailer",
        max_length_m=19.0,
        access_path="general_access",
    )

    db = FakeDB(
        profile=profile,
        dimension_rule=dimension_rule,
        axle_config=axle_config,
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="SEMI_STANDARD",
        axle_config_id="SEMI_6_AXLE",
    )

    assert result["status"] == "ok"
    assert result["classification"] == "general_access"
    assert result["used_dimensions"]["length_limit_m"] == 19.0


def test_b_double_axle_configuration_uses_class_2():

    profile = SimpleNamespace(
        profile_id="B_DOUBLE_STANDARD",
        template_id="B_DOUBLE",
        display_name="B-double",
        default_width_m=2.5,
        default_height_m=4.3,
        default_length_m=26.0,
    )

    dimension_rule = SimpleNamespace(
        template_id="B_DOUBLE",
        width_limit_m=2.5,
        height_limit_m=4.3,
        length_limit_m=25.0,
        classification_if_exceeded_limit="class_3",
    )

    axle_config = SimpleNamespace(
        axle_config_id="B_DOUBLE_9_AXLE",
        display_name="9 Axle B-double",
        max_length_m=26.0,
        access_path="class_2",
    )

    db = FakeDB(
        profile=profile,
        dimension_rule=dimension_rule,
        axle_config=axle_config,
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="B_DOUBLE_STANDARD",
        axle_config_id="B_DOUBLE_9_AXLE",
    )

    assert result["status"] == "ok"
    assert result["classification"] == "class_2"
    assert result["used_dimensions"]["length_limit_m"] == 26.0


def test_b_double_over_axle_length_limit_becomes_class_3():

    profile = SimpleNamespace(
        profile_id="B_DOUBLE_STANDARD",
        template_id="B_DOUBLE",
        display_name="B-double",
        default_width_m=2.5,
        default_height_m=4.3,
        default_length_m=26.0,
    )

    dimension_rule = SimpleNamespace(
        template_id="B_DOUBLE",
        width_limit_m=2.5,
        height_limit_m=4.3,
        length_limit_m=25.0,
        classification_if_exceeded_limit="class_3",
    )

    axle_config = SimpleNamespace(
        axle_config_id="B_DOUBLE_9_AXLE",
        display_name="9 Axle B-double",
        max_length_m=26.0,
        access_path="class_2",
    )

    db = FakeDB(
        profile=profile,
        dimension_rule=dimension_rule,
        axle_config=axle_config,
    )

    result = classify_hvnl_from_db(
        db=db,
        profile_id="B_DOUBLE_STANDARD",
        axle_config_id="B_DOUBLE_9_AXLE",
        custom_dimensions=True,
        answers={
            "overall_width_m": 2.5,
            "overall_height_m": 4.3,
            "overall_length_m": 26.01,
        },
    )

    assert result["status"] == "ok"
    assert result["classification"] == "class_3"
    assert result["used_dimensions"]["length_limit_m"] == 26.0
    assert len(result["warnings"]) == 1