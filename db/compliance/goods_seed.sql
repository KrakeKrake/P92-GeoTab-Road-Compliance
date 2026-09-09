-- =========================================================
-- GOODS TYPES
-- Goods carried by the heavy vehicle.
-- These are journey-specific and separate from vehicle type.
-- =========================================================

INSERT INTO compliance.goods_types
(
    goods_type_id,
    display_name,
    description
)
VALUES
(
    'GENERAL_FREIGHT',
    'General Freight',
    'General freight with no goods-specific routing override.'
),
(
    'LIVESTOCK',
    'Livestock',
    'Livestock carried by an eligible heavy vehicle.'
),
(
    'GRAIN',
    'Grain',
    'Grain transport. Goods-specific network access depends on vehicle eligibility.'
),
(
    'HAY',
    'Hay',
    'Hay transport. Goods-specific network access depends on vehicle eligibility and applicable arrangements.'
),
(
    'FODDER',
    'Fodder',
    'Fodder transport. Special access may depend on applicable emergency or drought arrangements.'
),
(
    'VEHICLE_CARRIER',
    'Vehicles / Cars',
    'Transport of vehicles or cars using an eligible vehicle carrier.'
),
(
    'DANGEROUS_GOODS',
    'Dangerous Goods',
    'Dangerous goods transport. Additional routing restrictions may apply.'
),
(
    'OTHER',
    'Other',
    'Other goods with no specific routing rule unless separately configured.'
);

-- =========================================================
-- PROOF-OF-CONCEPT GOODS → NETWORK RULES
-- =========================================================

-- Grain + Rigid Truck
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'GRAIN',
    'RIGID_TRUCK',
    NULL,
    NULL,
    NULL,
    'GHMS_RIGID_SEMI',
    100,
    TRUE,
    'Prototype mapping: Grain carried by a rigid truck uses the GHMS rigid truck and semi-trailer network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'GRAIN'
      AND template_id = 'RIGID_TRUCK'
      AND network_override_key = 'GHMS_RIGID_SEMI'
);


-- Grain + Prime Mover / Semitrailer
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'GRAIN',
    'PM_SEMI',
    NULL,
    NULL,
    NULL,
    'GHMS_RIGID_SEMI',
    100,
    TRUE,
    'Prototype mapping: Grain carried by a semitrailer uses the GHMS rigid truck and semi-trailer network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'GRAIN'
      AND template_id = 'PM_SEMI'
      AND network_override_key = 'GHMS_RIGID_SEMI'
);


-- Grain + B-Double
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'GRAIN',
    'B_DOUBLE',
    NULL,
    NULL,
    NULL,
    'GHMS_B_DOUBLE',
    100,
    TRUE,
    'Prototype mapping: Grain carried by a B-double uses the GHMS B-double network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'GRAIN'
      AND template_id = 'B_DOUBLE'
      AND network_override_key = 'GHMS_B_DOUBLE'
);


-- Grain + Type 1 Road Train
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'GRAIN',
    'TYPE_1_ROAD_TRAIN',
    NULL,
    NULL,
    NULL,
    'ROAD_TRAIN_HAY_GRAIN',
    100,
    TRUE,
    'Prototype mapping: Grain carried by a Type 1 Road Train uses the Permit Road Train Hay and Grain Network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'GRAIN'
      AND template_id = 'TYPE_1_ROAD_TRAIN'
      AND network_override_key = 'ROAD_TRAIN_HAY_GRAIN'
);


-- Grain + Type 2 Road Train
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'GRAIN',
    'TYPE_2_ROAD_TRAIN',
    NULL,
    NULL,
    NULL,
    'ROAD_TRAIN_HAY_GRAIN',
    100,
    TRUE,
    'Prototype mapping: Grain carried by a Type 2 Road Train uses the Permit Road Train Hay and Grain Network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'GRAIN'
      AND template_id = 'TYPE_2_ROAD_TRAIN'
      AND network_override_key = 'ROAD_TRAIN_HAY_GRAIN'
);


-- Hay + Type 1 Road Train
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'HAY',
    'TYPE_1_ROAD_TRAIN',
    NULL,
    NULL,
    NULL,
    'ROAD_TRAIN_HAY_GRAIN',
    100,
    TRUE,
    'Prototype mapping: Hay carried by a Type 1 Road Train uses the Permit Road Train Hay and Grain Network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'HAY'
      AND template_id = 'TYPE_1_ROAD_TRAIN'
      AND network_override_key = 'ROAD_TRAIN_HAY_GRAIN'
);


-- Hay + Type 2 Road Train
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'HAY',
    'TYPE_2_ROAD_TRAIN',
    NULL,
    NULL,
    NULL,
    'ROAD_TRAIN_HAY_GRAIN',
    100,
    TRUE,
    'Prototype mapping: Hay carried by a Type 2 Road Train uses the Permit Road Train Hay and Grain Network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'HAY'
      AND template_id = 'TYPE_2_ROAD_TRAIN'
      AND network_override_key = 'ROAD_TRAIN_HAY_GRAIN'
);


-- Fodder
INSERT INTO compliance.goods_network_rules
(
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    network_override_key,
    priority,
    active,
    note
)
SELECT
    'FODDER',
    NULL,
    NULL,
    NULL,
    NULL,
    'EMERGENCY_DROUGHT_NETWORK',
    100,
    TRUE,
    'Prototype mapping: Fodder uses the Emergency Drought Network.'
WHERE NOT EXISTS (
    SELECT 1
    FROM compliance.goods_network_rules
    WHERE goods_type_id = 'FODDER'
      AND network_override_key = 'EMERGENCY_DROUGHT_NETWORK'
);