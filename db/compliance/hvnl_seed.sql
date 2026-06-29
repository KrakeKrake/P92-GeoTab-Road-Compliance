-- =========================================================
-- 1. LICENCE CLASSES
-- Based on current licence hierarchy: LR, MR, HR, HC, MC
-- =========================================================

INSERT INTO compliance.licence_classes
(licence_class_id, display_name, rank_value)
VALUES
('LR', 'Light Rigid', 1),
('MR', 'Medium Rigid', 2),
('HR', 'Heavy Rigid', 3),
('HC', 'Heavy Combination', 4),
('MC', 'Multi Combination', 5);


-- =========================================================
-- 2. VEHICLE CATEGORIES
-- Based on vehicle_categories.py
-- =========================================================

INSERT INTO compliance.vehicle_categories
(category_id, category_name)
VALUES
('rigid_trucks', 'Rigid Trucks'),
('articulated_vehicles', 'Prime Mover + Semitrailer'),
('multi_combination', 'Multi-Combination Vehicles');


-- =========================================================
-- 3. VEHICLE TEMPLATES
-- Based on vehicle_templates.py
-- =========================================================

INSERT INTO compliance.vehicle_templates
(template_id, template_name, base_type)
VALUES
('RIGID_TRUCK', 'Rigid truck', 'rigid'),
('PM_SEMI', 'Prime mover + semitrailer', 'articulated'),
('B_DOUBLE', 'B-double', 'b_double');


-- =========================================================
-- 4. MASS SCHEMES
-- Based on mass_validator.py
-- =========================================================

INSERT INTO compliance.mass_schemes
(mass_scheme_id, display_name, description)
VALUES
('GML', 'General Mass Limits', 'Standard general mass limits'),
('CML', 'Concessional Mass Limits', 'Concessional mass limits'),
('HML', 'Higher Mass Limits', 'Higher mass limits');


-- =========================================================
-- 5. VEHICLE PROFILES
-- Based on vehicle_profiles.py
-- =========================================================

INSERT INTO compliance.vehicle_profiles
(
    profile_id,
    display_name,
    category_id,
    template_id,
    vehicle_family,
    combination_type,
    gvm_category,
    axle_count,
    axle_configurable,
    default_width_m,
    default_height_m,
    default_length_m,
    allow_custom_dimensions,
    required_licence_class_id
)
VALUES
(
    'STANDARD_LR_RIGID',
    'Light Rigid Truck (2 Axle, ≤8t GVM)',
    'rigid_trucks',
    'RIGID_TRUCK',
    'rigid_truck',
    'single_vehicle',
    'light',
    2,
    FALSE,
    2.50,
    3.50,
    8.00,
    TRUE,
    'LR'
),
(
    'STANDARD_MR_RIGID',
    'Medium Rigid Truck (2 Axle, >8t GVM)',
    'rigid_trucks',
    'RIGID_TRUCK',
    'rigid_truck',
    'single_vehicle',
    'medium',
    2,
    FALSE,
    2.50,
    4.00,
    10.00,
    TRUE,
    'MR'
),
(
    'STANDARD_HR_RIGID',
    'Heavy Rigid Truck (3+ Axle, >8t GVM)',
    'rigid_trucks',
    'RIGID_TRUCK',
    'rigid_truck',
    'single_vehicle',
    'heavy',
    3,
    FALSE,
    2.50,
    4.30,
    12.50,
    TRUE,
    'HR'
),
(
    'STANDARD_PM_SEMI',
    'Prime Mover + Semitrailer',
    'articulated_vehicles',
    'PM_SEMI',
    'articulated',
    'single_trailer',
    'heavy_combination',
    NULL,
    TRUE,
    2.50,
    4.30,
    19.00,
    TRUE,
    'HC'
),
(
    'STANDARD_B_DOUBLE',
    'B-Double Combination',
    'multi_combination',
    'B_DOUBLE',
    'multi_combination',
    'multi_trailer',
    'multi_combination',
    NULL,
    TRUE,
    2.50,
    4.30,
    26.00,
    TRUE,
    'MC'
);


-- =========================================================
-- 6. TEMPLATE QUESTIONS
-- Based on vehicle_templates.py
-- Only B-double currently has PBS question
-- =========================================================

INSERT INTO compliance.template_questions
(template_id, question_name, question_type, question_label, required)
VALUES
(
    'B_DOUBLE',
    'pbs_vehicle',
    'bool',
    'Is this a PBS vehicle?',
    FALSE
);


-- =========================================================
-- 7. AXLE CONFIGURATIONS
-- Based on axle_configurations.py
-- =========================================================

INSERT INTO compliance.axle_configurations
(axle_config_id, template_id, display_name, max_length_m, access_path, note)
VALUES
-- RIGID TRUCK
('RIGID_2_AXLE', 'RIGID_TRUCK', '2 Axle Rigid Truck', 12.50, 'general_access', NULL),
('RIGID_3_AXLE', 'RIGID_TRUCK', '3 Axle Rigid Truck', 12.50, 'general_access', NULL),
('RIGID_4_AXLE', 'RIGID_TRUCK', '4 Axle Rigid Truck', 12.50, 'general_access', NULL),
('RIGID_4_AXLE_TWINSTEER', 'RIGID_TRUCK', '4 Axle Twinsteer Rigid Truck', 12.50, 'general_access', 'Add one tonne if twinsteer axle group is load sharing.'),
('RIGID_5_AXLE_TWINSTEER', 'RIGID_TRUCK', '5 Axle Twinsteer Rigid Truck', 12.50, 'general_access', 'Add one tonne if twinsteer axle group is load sharing.'),

-- PRIME MOVER + SEMITRAILER
('SEMI_3_AXLE_6_9_9', 'PM_SEMI', '3 Axle Semitrailer', 19.00, 'general_access', NULL),
('SEMI_4_AXLE_6_9_16_5', 'PM_SEMI', '4 Axle Semitrailer', 19.00, 'general_access', NULL),
('SEMI_5_AXLE_6_9_20', 'PM_SEMI', '5 Axle Semitrailer', 19.00, 'general_access', NULL),
('SEMI_5_AXLE_6_16_5_16_5', 'PM_SEMI', '5 Axle Semitrailer', 19.00, 'general_access', NULL),
('SEMI_6_AXLE_6_16_5_20', 'PM_SEMI', '6 Axle Semitrailer', 19.00, 'general_access', NULL),

-- B-DOUBLE
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 'B_DOUBLE', '7 Axle B-double', 19.00, 'class_2', NULL),
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 'B_DOUBLE', '8 Axle B-double', 26.00, 'class_2', NULL),
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 'B_DOUBLE', '8 Axle B-double', 26.00, 'class_2', NULL),
('B_DOUBLE_9_AXLE_6_16_5_20_20', 'B_DOUBLE', '9 Axle B-double', 26.00, 'class_2', NULL);


-- =========================================================
-- 8. AXLE GROUP MASSES
-- Based on axle_group_masses_t arrays from axle_configurations.py
-- Rigid truck configs currently do not have axle_group_masses_t arrays
-- =========================================================

INSERT INTO compliance.axle_group_masses
(axle_config_id, group_order, mass_t)
VALUES
-- SEMI_3_AXLE_6_9_9
('SEMI_3_AXLE_6_9_9', 1, 6.00),
('SEMI_3_AXLE_6_9_9', 2, 9.00),
('SEMI_3_AXLE_6_9_9', 3, 9.00),

-- SEMI_4_AXLE_6_9_16_5
('SEMI_4_AXLE_6_9_16_5', 1, 6.00),
('SEMI_4_AXLE_6_9_16_5', 2, 9.00),
('SEMI_4_AXLE_6_9_16_5', 3, 16.50),

-- SEMI_5_AXLE_6_9_20
('SEMI_5_AXLE_6_9_20', 1, 6.00),
('SEMI_5_AXLE_6_9_20', 2, 9.00),
('SEMI_5_AXLE_6_9_20', 3, 20.00),

-- SEMI_5_AXLE_6_16_5_16_5
('SEMI_5_AXLE_6_16_5_16_5', 1, 6.00),
('SEMI_5_AXLE_6_16_5_16_5', 2, 16.50),
('SEMI_5_AXLE_6_16_5_16_5', 3, 16.50),

-- SEMI_6_AXLE_6_16_5_20
('SEMI_6_AXLE_6_16_5_20', 1, 6.00),
('SEMI_6_AXLE_6_16_5_20', 2, 16.50),
('SEMI_6_AXLE_6_16_5_20', 3, 20.00),

-- B_DOUBLE_7_AXLE_6_16_5_16_5_16_5
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 1, 6.00),
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 2, 16.50),
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 3, 16.50),
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 4, 16.50),

-- B_DOUBLE_8_AXLE_6_16_5_20_16_5
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 1, 6.00),
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 2, 16.50),
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 3, 20.00),
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 4, 16.50),

-- B_DOUBLE_8_AXLE_6_16_5_16_5_20
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 1, 6.00),
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 2, 16.50),
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 3, 16.50),
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 4, 20.00),

-- B_DOUBLE_9_AXLE_6_16_5_20_20
('B_DOUBLE_9_AXLE_6_16_5_20_20', 1, 6.00),
('B_DOUBLE_9_AXLE_6_16_5_20_20', 2, 16.50),
('B_DOUBLE_9_AXLE_6_16_5_20_20', 3, 20.00),
('B_DOUBLE_9_AXLE_6_16_5_20_20', 4, 20.00);


-- =========================================================
-- 9. AXLE CONFIG MASS LIMITS
-- Based on gml_mass_t, cml_mass_t, hml_mass_t in axle_configurations.py
-- NULL means that mass scheme is not applicable
-- =========================================================

INSERT INTO compliance.axle_config_mass_limits
(axle_config_id, mass_scheme_id, mass_limit_t)
VALUES
-- RIGID_2_AXLE
('RIGID_2_AXLE', 'GML', 15.00),
('RIGID_2_AXLE', 'CML', NULL),
('RIGID_2_AXLE', 'HML', NULL),

-- RIGID_3_AXLE
('RIGID_3_AXLE', 'GML', 22.50),
('RIGID_3_AXLE', 'CML', 23.00),
('RIGID_3_AXLE', 'HML', NULL),

-- RIGID_4_AXLE
('RIGID_4_AXLE', 'GML', 26.00),
('RIGID_4_AXLE', 'CML', 27.00),
('RIGID_4_AXLE', 'HML', NULL),

-- RIGID_4_AXLE_TWINSTEER
('RIGID_4_AXLE_TWINSTEER', 'GML', 26.50),
('RIGID_4_AXLE_TWINSTEER', 'CML', 27.00),
('RIGID_4_AXLE_TWINSTEER', 'HML', NULL),

-- RIGID_5_AXLE_TWINSTEER
('RIGID_5_AXLE_TWINSTEER', 'GML', 30.00),
('RIGID_5_AXLE_TWINSTEER', 'CML', 31.00),
('RIGID_5_AXLE_TWINSTEER', 'HML', NULL),

-- SEMI_3_AXLE_6_9_9
('SEMI_3_AXLE_6_9_9', 'GML', 24.00),
('SEMI_3_AXLE_6_9_9', 'CML', NULL),
('SEMI_3_AXLE_6_9_9', 'HML', NULL),

-- SEMI_4_AXLE_6_9_16_5
('SEMI_4_AXLE_6_9_16_5', 'GML', 31.50),
('SEMI_4_AXLE_6_9_16_5', 'CML', 32.00),
('SEMI_4_AXLE_6_9_16_5', 'HML', 32.00),

-- SEMI_5_AXLE_6_9_20
('SEMI_5_AXLE_6_9_20', 'GML', 35.00),
('SEMI_5_AXLE_6_9_20', 'CML', 36.00),
('SEMI_5_AXLE_6_9_20', 'HML', 37.50),

-- SEMI_5_AXLE_6_16_5_16_5
('SEMI_5_AXLE_6_16_5_16_5', 'GML', 39.00),
('SEMI_5_AXLE_6_16_5_16_5', 'CML', 40.00),
('SEMI_5_AXLE_6_16_5_16_5', 'HML', 40.00),

-- SEMI_6_AXLE_6_16_5_20
('SEMI_6_AXLE_6_16_5_20', 'GML', 42.50),
('SEMI_6_AXLE_6_16_5_20', 'CML', 43.50),
('SEMI_6_AXLE_6_16_5_20', 'HML', 45.50),

-- B_DOUBLE_7_AXLE_6_16_5_16_5_16_5
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 'GML', 55.50),
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 'CML', 57.00),
('B_DOUBLE_7_AXLE_6_16_5_16_5_16_5', 'HML', 57.00),

-- B_DOUBLE_8_AXLE_6_16_5_20_16_5
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 'GML', 59.00),
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 'CML', 61.00),
('B_DOUBLE_8_AXLE_6_16_5_20_16_5', 'HML', 62.50),

-- B_DOUBLE_8_AXLE_6_16_5_16_5_20
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 'GML', 59.00),
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 'CML', 61.00),
('B_DOUBLE_8_AXLE_6_16_5_16_5_20', 'HML', 62.50),

-- B_DOUBLE_9_AXLE_6_16_5_20_20
('B_DOUBLE_9_AXLE_6_16_5_20_20', 'GML', 62.50),
('B_DOUBLE_9_AXLE_6_16_5_20_20', 'CML', 64.50),
('B_DOUBLE_9_AXLE_6_16_5_20_20', 'HML', 68.00);


-- =========================================================
-- 10. DIMENSION RULES
-- Based on hardcoded limits in classifier.py
-- =========================================================

INSERT INTO compliance.dimension_rules
(
    template_id,
    rule_name,
    width_limit_m,
    height_limit_m,
    length_limit_m,
    classification_if_exceeded_limit,
    note
)
VALUES
(
    'RIGID_TRUCK',
    'General rigid truck dimension rule',
    2.50,
    4.30,
    12.50,
    'class_3',
    'Rigid trucks exceeding common general dimension limits are flagged as Class 3 in the prototype.'
),
(
    'PM_SEMI',
    'General prime mover and semitrailer dimension rule',
    2.50,
    4.30,
    19.00,
    'class_3',
    'Prime mover and semitrailer combinations exceeding common general dimension limits are flagged as Class 3 in the prototype.'
),
(
    'B_DOUBLE',
    'B-double prototype dimension rule',
    2.50,
    4.30,
    25.00,
    'class_3',
    'B-double classification follows Class 2 path unless prototype limits are exceeded. Selected axle configuration may override length to 26.0 m.'
);


-- =========================================================
-- 11. INPUT SANITY RANGES
-- Based on INPUT_SANITY_LIMITS in classifier.py and frontend helper text
-- =========================================================

INSERT INTO compliance.input_sanity_ranges
(
    template_id,
    min_width_m,
    max_width_m,
    min_height_m,
    max_height_m,
    min_length_m,
    max_length_m
)
VALUES
('RIGID_TRUCK', 2.00, 3.00, 2.50, 5.00, 5.00, 15.00),
('PM_SEMI', 2.00, 3.00, 2.50, 5.00, 10.00, 25.00),
('B_DOUBLE', 2.00, 3.00, 2.50, 5.00, 15.00, 30.00);