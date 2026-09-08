from .db_models import (
    GoodsType,
    GoodsNetworkRule,
    GoodsRestrictionRule,
    RoutingRestriction,
)


def resolve_goods_routing_preset(
    db,
    goods_type_id,
    template_id,
    axle_config_id,
    vehicle_classification,
    access_path,
    condition_codes=None,
):
    """
    Resolve any goods-specific routing changes.

    Important:
    - The normal/base vehicle network is determined elsewhere.
    - network_override_key = None means keep that normal network.
    - WorkSafe and other restrictions are returned separately.
    """

    condition_codes = condition_codes or []

    # ---------------------------------------------------------
    # 1. Validate goods type
    # ---------------------------------------------------------
    goods_type = (
        db.query(GoodsType)
        .filter(
            GoodsType.goods_type_id == goods_type_id
        )
        .first()
    )

    if not goods_type:
        return {
            "status": "error",
            "reason": "Goods type not found.",
            "goods_type_id": goods_type_id,
            "network_override_key": None,
            "additional_restrictions": [],
        }

    # ---------------------------------------------------------
    # 2. Find matching goods/network rules
    # ---------------------------------------------------------
    rules = (
        db.query(GoodsNetworkRule)
        .filter(
            GoodsNetworkRule.goods_type_id
            == goods_type_id,

            GoodsNetworkRule.active.is_(True),
        )
        .all()
    )

    matching_rules = []

    for rule in rules:
        # NULL means this rule does not care
        # about that particular vehicle field.

        if (
            rule.template_id is not None
            and rule.template_id != template_id
        ):
            continue

        if (
            rule.axle_config_id is not None
            and rule.axle_config_id
            != axle_config_id
        ):
            continue

        if (
            rule.vehicle_classification is not None
            and rule.vehicle_classification
            != vehicle_classification
        ):
            continue

        if (
            rule.access_path is not None
            and rule.access_path != access_path
        ):
            continue

        specificity = sum([
            rule.template_id is not None,
            rule.axle_config_id is not None,
            rule.vehicle_classification is not None,
            rule.access_path is not None,
        ])

        matching_rules.append(
            (rule, specificity)
        )

    selected_network_rule = None

    if matching_rules:
        #Lower priority number wins.
        #When priorities are equal, the more specific
        #rule should win.

        matching_rules.sort(
            key=lambda item: (
                item[0].priority
                if item[0].priority is not None
                else 100,
                -item[1],
            )
        )

        selected_network_rule = (
            matching_rules[0][0]
        )

    # ---------------------------------------------------------
    # 3. Find additional routing restrictions
    # ---------------------------------------------------------
    restriction_rules = (
        db.query(
            GoodsRestrictionRule,
            RoutingRestriction,
        )
        .join(
            RoutingRestriction,
            GoodsRestrictionRule.restriction_id
            == RoutingRestriction.restriction_id,
        )
        .filter(
            GoodsRestrictionRule.goods_type_id
            == goods_type_id,

            GoodsRestrictionRule.active.is_(True),

            RoutingRestriction.active.is_(True),
        )
        .all()
    )

    additional_restrictions = []

    for restriction_rule, restriction in restriction_rules:

        # No condition means it always applies
        # to this goods type.
        if restriction_rule.condition_code:
            if (
                restriction_rule.condition_code
                not in condition_codes
            ):
                continue

        additional_restrictions.append({
            "restriction_id":
                restriction.restriction_id,

            "restriction_name":
                restriction.restriction_name,

            "source":
                restriction.source,

            "restriction_type":
                restriction.restriction_type,

            "geometry_ref":
                restriction.geometry_ref,

            "is_derived":
                bool(restriction.is_derived),

            "condition_code":
                restriction_rule.condition_code,
        })

    # ---------------------------------------------------------
    # 4. Build result
    # ---------------------------------------------------------
    network_override_key = None
    network_rule_note = None

    if selected_network_rule:
        network_override_key = (
            selected_network_rule.network_override_key
        )

        network_rule_note = (
            selected_network_rule.note
        )

    if network_override_key:
        reason = (
            "A goods-specific network rule matched "
            "the selected vehicle and load."
        )
    else:
        reason = (
            "No goods-specific network override matched. "
            "Keep the normal vehicle routing network."
        )

    return {
        "status": "ok",

        "goods_type_id":
            goods_type.goods_type_id,

        "goods_display_name":
            goods_type.display_name,

        "network_override_key":
            network_override_key,

        "network_rule_note":
            network_rule_note,

        "additional_restrictions":
            additional_restrictions,

        "reason":
            reason,
    }