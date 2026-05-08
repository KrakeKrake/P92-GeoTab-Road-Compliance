from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

app = FastAPI(
    title="NHVR Route Compliance Validation API",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ─── Enums ─────────────────────────────────────

class MassClass(str, Enum):
    GML = "GML"
    CML = "CML"
    HML = "HML"

class VehicleCategory(str, Enum):
    GENERAL_ACCESS = "general_access"
    B_DOUBLE = "b_double"
    ROAD_TRAIN = "road_train"
    RIGID_TRUCK = "rigid_truck"
    PRIME_MOVER = "prime_mover"
    LIVESTOCK = "livestock"
    VEHICLE_CARRIER = "vehicle_carrier"
    DOUBLE_DECK_BUS = "double_deck_bus"

class ViolationType(str, Enum):
    HEIGHT_EXCEEDED = "height_exceeded"
    MASS_LIMIT_EXCEEDED = "mass_limit_exceeded"
    ROAD_ACCESS_DENIED = "road_access_denied"
    HML_ROAD_REQUIRED = "hml_road_required"
    CML_REQUIREMENT_FAILED = "cml_requirement_failed"

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"

# ─── Rules ─────────────────────────────────────

HEIGHT_LIMITS = {
    VehicleCategory.LIVESTOCK: 4.6,
    VehicleCategory.VEHICLE_CARRIER: 4.6,
    VehicleCategory.DOUBLE_DECK_BUS: 4.4,
}
DEFAULT_HEIGHT_LIMIT = 4.3

MASS_LIMITS = {
    MassClass.GML: 42.5,
    MassClass.CML: 45.5,
    MassClass.HML: 68.0,
}

ROAD_ACCESS = {
    "local": [MassClass.GML],
    "arterial": [MassClass.GML, MassClass.CML],
    "state": [MassClass.GML, MassClass.CML],
    "gazetted": [MassClass.GML, MassClass.CML, MassClass.HML],
    "restricted": [],
}

# ─── Models ─────────────────────────────────────

class VehicleProfile(BaseModel):
    vehicle_id: str
    category: VehicleCategory
    mass_class: MassClass
    height_m: float
    width_m: float
    length_m: float
    gross_mass_t: float
    has_rfs: bool = False

class RoadSegment(BaseModel):
    segment_id: str
    road_name: str
    road_type: str
    max_height_m: Optional[float] = None
    max_mass_t: Optional[float] = None
    is_hml_gazetted: bool = False

class ComplianceRequest(BaseModel):
    vehicle: VehicleProfile
    route_segments: List[RoadSegment]

class Violation(BaseModel):
    segment_id: str
    road_name: str
    violation_type: ViolationType
    severity: Severity
    detail: str
    vehicle_value: float
    limit_value: float

class ComplianceReport(BaseModel):
    vehicle_id: str
    route_compliant: bool
    total_segments: int
    violations: List[Violation]
    summary: str

# ─── Helpers ─────────────────────────────────────

def get_height_limit(category: VehicleCategory) -> float:
    return HEIGHT_LIMITS.get(category, DEFAULT_HEIGHT_LIMIT)

# ─── Validation Engine ───────────────────────────

def validate_segment(vehicle: VehicleProfile, segment: RoadSegment) -> List[Violation]:
    violations = []

    # 1. Regulatory height check
    reg_limit = get_height_limit(vehicle.category)
    if vehicle.height_m > reg_limit:
        violations.append(Violation(
            segment_id=segment.segment_id,
            road_name=segment.road_name,
            violation_type=ViolationType.HEIGHT_EXCEEDED,
            severity=Severity.ERROR,
            detail=f"Vehicle height exceeds NHVR limit ({reg_limit}m).",
            vehicle_value=vehicle.height_m,
            limit_value=reg_limit
        ))

    # 2. Bridge clearance check
    if segment.max_height_m and vehicle.height_m > segment.max_height_m:
        violations.append(Violation(
            segment_id=segment.segment_id,
            road_name=segment.road_name,
            violation_type=ViolationType.HEIGHT_EXCEEDED,
            severity=Severity.ERROR,
            detail=f"Vehicle exceeds bridge clearance ({segment.max_height_m}m).",
            vehicle_value=vehicle.height_m,
            limit_value=segment.max_height_m
        ))

    # 3. Mass check
    limit = segment.max_mass_t if segment.max_mass_t else MASS_LIMITS[vehicle.mass_class]
    if vehicle.gross_mass_t > limit:
        violations.append(Violation(
            segment_id=segment.segment_id,
            road_name=segment.road_name,
            violation_type=ViolationType.MASS_LIMIT_EXCEEDED,
            severity=Severity.ERROR,
            detail=f"Mass exceeds limit ({limit}t).",
            vehicle_value=vehicle.gross_mass_t,
            limit_value=limit
        ))

    # 4. Road access rules
    allowed = ROAD_ACCESS.get(segment.road_type, [])
    if vehicle.mass_class not in allowed:
        violations.append(Violation(
            segment_id=segment.segment_id,
            road_name=segment.road_name,
            violation_type=ViolationType.ROAD_ACCESS_DENIED,
            severity=Severity.ERROR,
            detail=f"{vehicle.mass_class.value} not allowed on {segment.road_type} roads.",
            vehicle_value=1,
            limit_value=0
        ))

    # 5. HML rule
    if vehicle.mass_class == MassClass.HML and not segment.is_hml_gazetted:
        violations.append(Violation(
            segment_id=segment.segment_id,
            road_name=segment.road_name,
            violation_type=ViolationType.HML_ROAD_REQUIRED,
            severity=Severity.ERROR,
            detail="HML requires gazetted roads.",
            vehicle_value=1,
            limit_value=0
        ))

    return violations

# ─── API Endpoint ───────────────────────────────

@app.post("/validate", response_model=ComplianceReport)
def validate_route(request: ComplianceRequest):

    vehicle = request.vehicle
    all_violations = []

    # Vehicle-level check (CML RFS)
    if vehicle.mass_class == MassClass.CML and not vehicle.has_rfs:
        all_violations.append(Violation(
            segment_id="ALL",
            road_name="ALL",
            violation_type=ViolationType.CML_REQUIREMENT_FAILED,
            severity=Severity.ERROR,
            detail="CML requires Road Friendly Suspension (RFS).",
            vehicle_value=0,
            limit_value=1
        ))

    # Segment checks
    for segment in request.route_segments:
        all_violations.extend(validate_segment(vehicle, segment))

    compliant = len(all_violations) == 0

    summary = (
        "Route is COMPLIANT."
        if compliant
        else f"Route is NON-COMPLIANT with {len(all_violations)} violation(s)."
    )

    return ComplianceReport(
        vehicle_id=vehicle.vehicle_id,
        route_compliant=compliant,
        total_segments=len(request.route_segments),
        violations=all_violations,
        summary=summary
    )

@app.get("/rules")
def get_rules():
    return {
        "mass_limits": MASS_LIMITS,
        "height_limits": {
            "default": DEFAULT_HEIGHT_LIMIT,
            "special": {k.value: v for k, v in HEIGHT_LIMITS.items()}
        },
        "road_access": {
            k: [m.value for m in v]
            for k, v in ROAD_ACCESS.items()
        }
    }


@app.get("/height-limits")
def get_height_limits():
    return {
        "default": DEFAULT_HEIGHT_LIMIT,
        "categories": {k.value: v for k, v in HEIGHT_LIMITS.items()}
    }


@app.get("/mass-limits")
def get_mass_limits():
    return {
        k.value: v for k, v in MASS_LIMITS.items()
    }






