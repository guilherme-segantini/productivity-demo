"""API endpoints for radar data."""

import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Trend

router = APIRouter(prefix="/api", tags=["radar"])


class TrendResponse(BaseModel):
    """Response model for a single trend."""

    focus_area: str
    tool_name: str
    classification: str
    confidence_score: int
    technical_insight: str
    signal_evidence: list[str]
    noise_indicators: list[str]
    architectural_verdict: bool
    timestamp: str


class RadarResponse(BaseModel):
    """Response model for radar data."""

    radar_date: str
    trends: list[TrendResponse]


@router.get("/radar", response_model=RadarResponse)
def get_radar(
    date_param: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Get radar analysis for a specific date.

    If no date provided, returns the latest available data.
    """
    if date_param:
        query_date = date_param
    else:
        # Get the most recent radar date
        latest = db.query(Trend.radar_date).order_by(Trend.radar_date.desc()).first()
        if not latest:
            # Return empty response if no data
            return RadarResponse(radar_date=str(date.today()), trends=[])
        query_date = latest[0]

    trends = db.query(Trend).filter(Trend.radar_date == query_date).all()

    return RadarResponse(
        radar_date=query_date,
        trends=[
            TrendResponse(
                focus_area=t.focus_area,
                tool_name=t.tool_name,
                classification=t.classification,
                confidence_score=t.confidence_score,
                technical_insight=t.technical_insight,
                signal_evidence=json.loads(t.signal_evidence) if t.signal_evidence else [],
                noise_indicators=json.loads(t.noise_indicators) if t.noise_indicators else [],
                architectural_verdict=t.architectural_verdict,
                timestamp=t.timestamp,
            )
            for t in trends
        ],
    )


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
