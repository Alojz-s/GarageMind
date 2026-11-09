from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import ApiError, require_permission
from app.core.database import get_db
from app.core.permissions import BANDS_READ, BANDS_WRITE
from app.models import Band
from app.schemas.bands import BandCreate, BandResponse, BandUpdate

router = APIRouter(prefix="/bands", tags=["bands"])


@router.get("", dependencies=[require_permission(BANDS_READ)])
def list_bands(db: Annotated[Session, Depends(get_db)]) -> list[BandResponse]:
    bands = db.scalars(select(Band).order_by(Band.id))
    return [BandResponse.model_validate(band) for band in bands]


@router.post("", dependencies=[require_permission(BANDS_WRITE)])
def create_band(body: BandCreate, db: Annotated[Session, Depends(get_db)]) -> BandResponse:
    band = Band(name=body.name, bio=body.bio)
    db.add(band)
    db.commit()
    return BandResponse.model_validate(band)


@router.put("/{band_id}", dependencies=[require_permission(BANDS_WRITE)])
def update_band(
    band_id: int, body: BandUpdate, db: Annotated[Session, Depends(get_db)]
) -> BandResponse:
    band = db.get(Band, band_id)
    if band is None:
        raise ApiError(status.HTTP_404_NOT_FOUND, "Band not found", "band_not_found")
    band.name = body.name
    band.bio = body.bio
    db.commit()
    return BandResponse.model_validate(band)
