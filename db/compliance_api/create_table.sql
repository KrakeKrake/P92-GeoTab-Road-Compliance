DROP TABLE IF EXISTS account.users CASCADE;
DROP TABLE IF EXISTS compliance.input_sanity_ranges CASCADE;
DROP TABLE IF EXISTS compliance.dimension_rules CASCADE;
DROP TABLE IF EXISTS compliance.axle_config_mass_limits CASCADE;
DROP TABLE IF EXISTS compliance.axle_group_masses CASCADE;
DROP TABLE IF EXISTS compliance.axle_configurations CASCADE;
DROP TABLE IF EXISTS compliance.template_questions CASCADE;
DROP TABLE IF EXISTS compliance.vehicle_profiles CASCADE;
DROP TABLE IF EXISTS compliance.mass_schemes CASCADE;
DROP TABLE IF EXISTS compliance.vehicle_templates CASCADE;
DROP TABLE IF EXISTS compliance.vehicle_categories CASCADE;
DROP TABLE IF EXISTS compliance.licence_classes CASCADE;


CREATE TABLE compliance.licence_classes (
    licence_class_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    rank_value INTEGER NOT NULL UNIQUE
);

CREATE TABLE compliance.vehicle_categories (
    category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL
);

CREATE TABLE compliance.vehicle_templates (
    template_id TEXT PRIMARY KEY,
    template_name TEXT NOT NULL,
    base_type TEXT NOT NULL
);

CREATE TABLE compliance.mass_schemes (
    mass_scheme_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE compliance.vehicle_profiles (
    profile_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,

    category_id TEXT NOT NULL,
    template_id TEXT NOT NULL,

    vehicle_family TEXT NOT NULL,
    combination_type TEXT NOT NULL,
    gvm_category TEXT,

    axle_count INTEGER,
    axle_configurable BOOLEAN DEFAULT FALSE,

    default_width_m NUMERIC(5,2) NOT NULL,
    default_height_m NUMERIC(5,2) NOT NULL,
    default_length_m NUMERIC(5,2) NOT NULL,

    allow_custom_dimensions BOOLEAN DEFAULT TRUE,

    required_licence_class_id TEXT NOT NULL,

    FOREIGN KEY (category_id)
        REFERENCES compliance.vehicle_categories(category_id),

    FOREIGN KEY (template_id)
        REFERENCES compliance.vehicle_templates(template_id),

    FOREIGN KEY (required_licence_class_id)
        REFERENCES compliance.licence_classes(licence_class_id)
);

CREATE TABLE compliance.template_questions (
    question_id SERIAL PRIMARY KEY,
    template_id TEXT NOT NULL,

    question_name TEXT NOT NULL,
    question_type TEXT NOT NULL,
    question_label TEXT NOT NULL,
    required BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (template_id)
        REFERENCES compliance.vehicle_templates(template_id)
);

CREATE TABLE compliance.axle_configurations (
    axle_config_id TEXT PRIMARY KEY,
    template_id TEXT NOT NULL,

    display_name TEXT NOT NULL,
    max_length_m NUMERIC(5,2) NOT NULL,

    access_path TEXT NOT NULL,
    note TEXT,

    FOREIGN KEY (template_id)
        REFERENCES compliance.vehicle_templates(template_id)
);

CREATE TABLE compliance.axle_group_masses (
    axle_group_mass_id SERIAL PRIMARY KEY,

    axle_config_id TEXT NOT NULL,
    group_order INTEGER NOT NULL,
    mass_t NUMERIC(5,2) NOT NULL,

    FOREIGN KEY (axle_config_id)
        REFERENCES compliance.axle_configurations(axle_config_id),

    UNIQUE (axle_config_id, group_order)
);

CREATE TABLE compliance.axle_config_mass_limits (
    mass_limit_id SERIAL PRIMARY KEY,

    axle_config_id TEXT NOT NULL,
    mass_scheme_id TEXT NOT NULL,
    mass_limit_t NUMERIC(6,2),

    FOREIGN KEY (axle_config_id)
        REFERENCES compliance.axle_configurations(axle_config_id),

    FOREIGN KEY (mass_scheme_id)
        REFERENCES compliance.mass_schemes(mass_scheme_id),

    UNIQUE (axle_config_id, mass_scheme_id)
);

CREATE TABLE compliance.dimension_rules (
    dimension_rule_id SERIAL PRIMARY KEY,

    template_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,

    width_limit_m NUMERIC(5,2) NOT NULL,
    height_limit_m NUMERIC(5,2) NOT NULL,
    length_limit_m NUMERIC(5,2) NOT NULL,

    classification_if_exceeded_limit TEXT DEFAULT 'class_3',
    note TEXT,

    FOREIGN KEY (template_id)
        REFERENCES compliance.vehicle_templates(template_id)
);

CREATE TABLE compliance.input_sanity_ranges (
    range_id SERIAL PRIMARY KEY,

    template_id TEXT NOT NULL,

    min_width_m NUMERIC(5,2) NOT NULL,
    max_width_m NUMERIC(5,2) NOT NULL,

    min_height_m NUMERIC(5,2) NOT NULL,
    max_height_m NUMERIC(5,2) NOT NULL,

    min_length_m NUMERIC(5,2) NOT NULL,
    max_length_m NUMERIC(5,2) NOT NULL,

    FOREIGN KEY (template_id)
        REFERENCES compliance.vehicle_templates(template_id)
);

CREATE TABLE account.users (
    user_id SERIAL PRIMARY KEY,

    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,

    licence_class_id TEXT,
    favourite_profile_id TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (licence_class_id)
        REFERENCES compliance.licence_classes(licence_class_id),

    FOREIGN KEY (favourite_profile_id)
        REFERENCES compliance.vehicle_profiles(profile_id)
);