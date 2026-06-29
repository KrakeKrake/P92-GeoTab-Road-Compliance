from .axle_configurations import axle_configurations


def find_axle_config(config_id: str):
    for template_id, configs in axle_configurations.items():
        for config in configs:
            if config["config_id"] == config_id:
                return template_id, config
    return None, None


def validate_mass(config_id: str, mass_scheme: str, operating_mass_t: float):
    mass_scheme = mass_scheme.upper()

    _, config = find_axle_config(config_id)

    if not config:
        return {
            "status": "error",
            "compliant": False,
            "reason": "Axle configuration not found."
        }

    limit_key = {
        "GML": "gml_mass_t",
        "CML": "cml_mass_t",
        "HML": "hml_mass_t"
    }.get(mass_scheme)

    if not limit_key:
        return {
            "status": "error",
            "compliant": False,
            "reason": "Invalid mass scheme. Use GML, CML, or HML."
        }

    limit = config.get(limit_key)

    if limit is None:
        return {
            "status": "not_applicable",
            "compliant": False,
            "reason": f"{mass_scheme} does not apply to this axle configuration.",
            "selected_limit_t": None
        }

    if operating_mass_t <= limit:
        return {
            "status": "ok",
            "compliant": True,
            "reason": f"Operating mass {operating_mass_t} t is within {mass_scheme} limit of {limit} t.",
            "selected_limit_t": limit
        }

    return {
        "status": "exceeds_limit",
        "compliant": False,
        "reason": f"Operating mass {operating_mass_t} t exceeds {mass_scheme} limit of {limit} t.",
        "selected_limit_t": limit
    }