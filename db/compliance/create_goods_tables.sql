-- =========================================================
-- GOODS / ROUTING TABLES
-- Safe incremental creation for existing development DB.
-- =========================================================

CREATE TABLE IF NOT EXISTS compliance.goods_types (
    goods_type_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT
);


CREATE TABLE IF NOT EXISTS compliance.routing_restrictions (
    restriction_id TEXT PRIMARY KEY,

    restriction_name TEXT NOT NULL,
    source TEXT NOT NULL,
    restriction_type TEXT NOT NULL,

    geometry_ref TEXT,

    is_derived BOOLEAN DEFAULT FALSE,

    provenance_note TEXT,

    active BOOLEAN DEFAULT TRUE
);


CREATE TABLE IF NOT EXISTS compliance.goods_network_rules (
    goods_network_rule_id SERIAL PRIMARY KEY,

    goods_type_id TEXT NOT NULL,

    template_id TEXT,
    axle_config_id TEXT,

    vehicle_classification TEXT,
    access_path TEXT,

    network_override_key TEXT,

    priority INTEGER DEFAULT 100,

    active BOOLEAN DEFAULT TRUE,

    note TEXT,

    FOREIGN KEY (goods_type_id)
        REFERENCES compliance.goods_types(goods_type_id),

    FOREIGN KEY (template_id)
        REFERENCES compliance.vehicle_templates(template_id),

    FOREIGN KEY (axle_config_id)
        REFERENCES compliance.axle_configurations(axle_config_id)
);


CREATE TABLE IF NOT EXISTS compliance.goods_restriction_rules (
    goods_restriction_rule_id SERIAL PRIMARY KEY,

    goods_type_id TEXT NOT NULL,

    restriction_id TEXT NOT NULL,

    condition_code TEXT,

    priority INTEGER DEFAULT 100,

    active BOOLEAN DEFAULT TRUE,

    note TEXT,

    FOREIGN KEY (goods_type_id)
        REFERENCES compliance.goods_types(goods_type_id),

    FOREIGN KEY (restriction_id)
        REFERENCES compliance.routing_restrictions(restriction_id)
);