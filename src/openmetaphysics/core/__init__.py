"""OpenMetaphysics core — deterministic primitives."""

from .calendar import (
    bazi_year_index,
    julian_day,
    julian_day_number,
    lichun_time,
    month_boundary_before,
    sexagenary_day_index,
    solar_longitude,
    solar_term_time,
    solar_terms_for_year,
    solar_to_lunar,
)
from .engines import (
    BaseAgent,
    DeterministicEngine,
    TraceRecorder,
    derive_seed,
    deterministic_rng,
)
from .models import (
    BRANCH_ELEMENT,
    BRANCH_HIDDEN_STEMS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENT,
    STEM_YIN_YANG,
    WUXING,
    WUXING_KE,
    WUXING_SHENG,
    hexagram_from_lines,
    hexagram_lines,
    nayin_for,
    sexagenary_index,
    sexagenary_pair,
    wuxing_relation,
)
from .schemas import (
    AgentInput,
    AgentOutput,
    ConfidenceScore,
    Gender,
    GeoPoint,
    ReasoningStep,
    SexagenaryComponent,
    canonical_input,
    hash_input,
    utcnow,
)
from .solar_time import (
    TrueSolarTimeResult,
    add_equation_of_time,
    equation_of_time,
    longitude_offset_minutes,
    standard_to_local_mean,
    true_solar_time,
)

__all__ = [
    # calendar
    "julian_day_number",
    "julian_day",
    "solar_longitude",
    "solar_term_time",
    "solar_terms_for_year",
    "lichun_time",
    "sexagenary_day_index",
    "month_boundary_before",
    "bazi_year_index",
    "solar_to_lunar",
    # engines
    "TraceRecorder",
    "DeterministicEngine",
    "deterministic_rng",
    "derive_seed",
    "BaseAgent",
    # models
    "HEAVENLY_STEMS",
    "EARTHLY_BRANCHES",
    "STEM_ELEMENT",
    "STEM_YIN_YANG",
    "BRANCH_ELEMENT",
    "BRANCH_HIDDEN_STEMS",
    "WUXING",
    "WUXING_SHENG",
    "WUXING_KE",
    "wuxing_relation",
    "sexagenary_pair",
    "sexagenary_index",
    "nayin_for",
    "hexagram_from_lines",
    "hexagram_lines",
    # schemas
    "Gender",
    "GeoPoint",
    "SexagenaryComponent",
    "AgentInput",
    "ReasoningStep",
    "ConfidenceScore",
    "AgentOutput",
    "canonical_input",
    "hash_input",
    "utcnow",
    # solar_time
    "equation_of_time",
    "longitude_offset_minutes",
    "standard_to_local_mean",
    "add_equation_of_time",
    "true_solar_time",
    "TrueSolarTimeResult",
]




