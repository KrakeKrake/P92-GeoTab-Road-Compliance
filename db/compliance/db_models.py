from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, Text
from .database import Base
from sqlalchemy import Column, Integer, Text, TIMESTAMP, ForeignKey


class LicenceClass(Base):
    __tablename__ = "licence_classes"
    __table_args__ = {"schema": "compliance"}

    licence_class_id = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)
    rank_value = Column(Integer, nullable=False, unique=True)


class VehicleCategory(Base):
    __tablename__ = "vehicle_categories"
    __table_args__ = {"schema": "compliance"}

    category_id = Column(Text, primary_key=True)
    category_name = Column(Text, nullable=False)


class VehicleTemplate(Base):
    __tablename__ = "vehicle_templates"
    __table_args__ = {"schema": "compliance"}

    template_id = Column(Text, primary_key=True)
    template_name = Column(Text, nullable=False)
    base_type = Column(Text, nullable=False)

class TemplateQuestion(Base):
    __tablename__ = "template_questions"
    __table_args__ = {"schema": "compliance"}

    question_id = Column(Integer, primary_key=True, index=True)
    template_id = Column(
        Text,
        ForeignKey("compliance.vehicle_templates.template_id"),
        nullable=False
    )

    question_name = Column(Text, nullable=False)
    question_type = Column(Text, nullable=False)
    question_label = Column(Text, nullable=False)
    required = Column(Boolean, default=False)

class AxleConfiguration(Base):
    __tablename__ = "axle_configurations"
    __table_args__ = {"schema": "compliance"}

    axle_config_id = Column(Text, primary_key=True)
    template_id = Column(
        Text,
        ForeignKey("compliance.vehicle_templates.template_id"),
        nullable=False
    )

    display_name = Column(Text, nullable=False)
    max_length_m = Column(Numeric(5, 2), nullable=False)

    access_path = Column(Text, nullable=False)
    note = Column(Text)

class VehicleProfile(Base):
    __tablename__ = "vehicle_profiles"
    __table_args__ = {"schema": "compliance"}

    profile_id = Column(Text, primary_key=True)
    display_name = Column(Text, nullable=False)

    category_id = Column(
        Text,
        ForeignKey("compliance.vehicle_categories.category_id"),
        nullable=False
    )

    template_id = Column(
        Text,
        ForeignKey("compliance.vehicle_templates.template_id"),
        nullable=False
    )

    vehicle_family = Column(Text, nullable=False)
    combination_type = Column(Text, nullable=False)
    gvm_category = Column(Text)

    axle_count = Column(Integer)
    axle_configurable = Column(Boolean, default=False)

    default_width_m = Column(Numeric(5, 2), nullable=False)
    default_height_m = Column(Numeric(5, 2), nullable=False)
    default_length_m = Column(Numeric(5, 2), nullable=False)

    allow_custom_dimensions = Column(Boolean, default=True)

    required_licence_class_id = Column(
        Text,
        ForeignKey("compliance.licence_classes.licence_class_id"),
        nullable=False
    )

class AxleConfigMassLimit(Base):
    __tablename__ = "axle_config_mass_limits"
    __table_args__ = {"schema": "compliance"}

    mass_limit_id = Column(Integer, primary_key=True, index=True)

    axle_config_id = Column(
        Text,
        ForeignKey("compliance.axle_configurations.axle_config_id"),
        nullable=False
    )

    mass_scheme_id = Column(
        Text,
        ForeignKey("compliance.mass_schemes.mass_scheme_id"),
        nullable=False
    )

    mass_limit_t = Column(Numeric(6, 2))
    
class DimensionRule(Base):
    __tablename__ = "dimension_rules"
    __table_args__ = {"schema": "compliance"}

    dimension_rule_id = Column(Integer, primary_key=True, index=True)

    template_id = Column(
        Text,
        ForeignKey("compliance.vehicle_templates.template_id"),
        nullable=False
    )

    rule_name = Column(Text, nullable=False)

    width_limit_m = Column(Numeric(5, 2), nullable=False)
    height_limit_m = Column(Numeric(5, 2), nullable=False)
    length_limit_m = Column(Numeric(5, 2), nullable=False)

    classification_if_exceeded_limit = Column(Text, default="class_3")
    note = Column(Text)


class InputSanityRange(Base):
    __tablename__ = "input_sanity_ranges"
    __table_args__ = {"schema": "compliance"}

    range_id = Column(Integer, primary_key=True, index=True)

    template_id = Column(
        Text,
        ForeignKey("compliance.vehicle_templates.template_id"),
        nullable=False
    )

    min_width_m = Column(Numeric(5, 2), nullable=False)
    max_width_m = Column(Numeric(5, 2), nullable=False)

    min_height_m = Column(Numeric(5, 2), nullable=False)
    max_height_m = Column(Numeric(5, 2), nullable=False)

    min_length_m = Column(Numeric(5, 2), nullable=False)
    max_length_m = Column(Numeric(5, 2), nullable=False)


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "account"}

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(Text, nullable=False, unique=True)
    username = Column(Text, nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    licence_class_id = Column(Text, ForeignKey("compliance.licence_classes.licence_class_id"))
    favourite_profile_id = Column(Text, ForeignKey("compliance.vehicle_profiles.profile_id"))
    created_at = Column(TIMESTAMP)