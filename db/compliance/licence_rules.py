from .vehicle_profiles import vehicle_profiles

LICENCE_HIERARCHY = ["LR", "MR", "HR", "HC", "MC"]


def licence_rank(licence_class: str) -> int:
    licence_class = licence_class.upper()
    if licence_class not in LICENCE_HIERARCHY:
        return -1
    return LICENCE_HIERARCHY.index(licence_class)


def required_licence_for_profile(profile: dict) -> str | None:
    family = profile.get("vehicle_family")

    if family == "rigid_truck":
        gvm_category = profile.get("gvm_category")
        axle_count = profile.get("axle_count", 0)

        if gvm_category == "light":
            return "LR"
        if gvm_category == "medium" and axle_count <= 2:
            return "MR"
        if gvm_category == "heavy" and axle_count >= 3:
            return "HR"

    if family == "articulated":
        return "HC"

    if family == "multi_combination":
        return "MC"

    return None


def is_profile_allowed_for_licence(profile: dict, licence_class: str) -> bool:
    required = required_licence_for_profile(profile)
    if not required:
        return False

    return licence_rank(licence_class) >= licence_rank(required)


def get_profiles_by_licence(licence_class: str):
    licence_class = licence_class.upper()

    if licence_class not in LICENCE_HIERARCHY:
        return []

    allowed_profiles = []

    for profile_id, profile in vehicle_profiles.items():
        if is_profile_allowed_for_licence(profile, licence_class):
            allowed_profiles.append({
                "profile_id": profile_id,
                "display_name": profile["display_name"]
            })

    return allowed_profiles