"""
Data Provenance and Observation Status Schemas
Guarantees scientific integrity and transparent data origin tracking across all feeds.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProvenanceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    FORECAST = "FORECAST"
    MODEL_PREDICTED = "MODEL_PREDICTED"
    DERIVED = "DERIVED"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"


class ProvenanceRecord(BaseModel):
    source: str = Field(..., description="Origin data system or model (e.g. GCC SWD GIS, XGBoost Baseline)")
    timestamp: str = Field(..., description="ISO-8601 observation or generation timestamp")
    status: ProvenanceStatus = Field(..., description="Status of the measurement or inference")
    unit: Optional[str] = Field(None, description="Physical unit of measurement")
    confidence: Optional[float] = Field(None, description="Confidence score [0.0, 1.0] if probabilistic")
    notes: Optional[str] = Field(None, description="Contextual qualifications, limitations or caveats")
