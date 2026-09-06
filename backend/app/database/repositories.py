"""
Asynchronous Repository Layer for Database Operations.
Provides clean query interfaces for locations, forecasts, references,
predictions, risk grids, models, and pipeline telemetry.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database.models import (
    Location, Forecast, ReferenceWeather, ForecastError,
    BustLabel, Prediction, ModelRecord, DatasetRecord, PipelineRun
)


class LocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, query: str, limit: int = 10) -> List[Location]:
        stmt = select(Location).where(
            (Location.city.ilike(f"%{query}%")) |
            (Location.district.ilike(f"%{query}%")) |
            (Location.state.ilike(f"%{query}%"))
        ).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_coords(self, lat: float, lon: float, tolerance: float = 0.5) -> Optional[Location]:
        stmt = select(Location).where(
            (Location.latitude.between(lat - tolerance, lat + tolerance)) &
            (Location.longitude.between(lon - tolerance, lon + tolerance))
        ).order_by(
            func.abs(Location.latitude - lat) + func.abs(Location.longitude - lon)
        ).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100) -> List[Location]:
        stmt = select(Location).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, city: str, lat: float, lon: float, district: Optional[str] = None, state: Optional[str] = None, elevation: float = 0.0) -> Location:
        loc = Location(city=city, district=district, state=state, latitude=lat, longitude=lon, elevation=elevation)
        self.session.add(loc)
        await self.session.commit()
        await self.session.refresh(loc)
        return loc


class ForecastRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_forecasts(self, forecasts: List[Dict[str, Any]]) -> List[Forecast]:
        objs = [Forecast(**f) for f in forecasts]
        self.session.add_all(objs)
        await self.session.commit()
        return objs

    async def get_forecast_by_horizon(self, lat: float, lon: float, lead_hours: int, tolerance: float = 0.5) -> Optional[Forecast]:
        stmt = select(Forecast).where(
            (Forecast.latitude.between(lat - tolerance, lat + tolerance)) &
            (Forecast.longitude.between(lon - tolerance, lon + tolerance)) &
            (Forecast.lead_hours == lead_hours)
        ).order_by(desc(Forecast.initialization_time)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_forecast_horizons(self, lat: float, lon: float, tolerance: float = 0.5) -> List[Forecast]:
        stmt = select(Forecast).where(
            (Forecast.latitude.between(lat - tolerance, lat + tolerance)) &
            (Forecast.longitude.between(lon - tolerance, lon + tolerance))
        ).order_by(Forecast.lead_hours)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PredictionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_prediction(self, pred_dict: Dict[str, Any]) -> Prediction:
        pred = Prediction(**pred_dict)
        self.session.add(pred)
        await self.session.commit()
        await self.session.refresh(pred)
        return pred

    async def get_latest_risk(self, lat: float, lon: float, lead_hours: int = 96, variable: str = "precipitation", tolerance: float = 0.5) -> Optional[Prediction]:
        stmt = select(Prediction).where(
            (Prediction.latitude.between(lat - tolerance, lat + tolerance)) &
            (Prediction.longitude.between(lon - tolerance, lon + tolerance)) &
            (Prediction.lead_hours == lead_hours) &
            (Prediction.variable == variable)
        ).order_by(desc(Prediction.prediction_time)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_risk_grid(self, lead_hours: int = 96, variable: str = "precipitation") -> List[Prediction]:
        # Return latest prediction per unique spatial grid point
        stmt = select(Prediction).where(
            (Prediction.lead_hours == lead_hours) &
            (Prediction.variable == variable)
        ).order_by(desc(Prediction.prediction_time)).limit(200)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ModelRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_production_model(self) -> Optional[ModelRecord]:
        stmt = select(ModelRecord).where(ModelRecord.status == "PRODUCTION").order_by(desc(ModelRecord.creation_date)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_models(self) -> List[ModelRecord]:
        stmt = select(ModelRecord).order_by(desc(ModelRecord.creation_date))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def register_model(self, record_dict: Dict[str, Any]) -> ModelRecord:
        record = ModelRecord(**record_dict)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def promote_model(self, model_version: str) -> bool:
        # Demote current production model to VALIDATED
        await self.session.execute(
            update(ModelRecord).where(ModelRecord.status == "PRODUCTION").values(status="VALIDATED")
        )
        # Promote target model
        res = await self.session.execute(
            update(ModelRecord).where(ModelRecord.model_version == model_version).values(status="PRODUCTION")
        )
        await self.session.commit()
        return res.rowcount > 0

    async def rollback_to(self, target_version: str) -> bool:
        return await self.promote_model(target_version)


class DatasetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_dataset(self) -> Optional[DatasetRecord]:
        stmt = select(DatasetRecord).order_by(desc(DatasetRecord.created_at)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def register_dataset(self, data_dict: Dict[str, Any]) -> DatasetRecord:
        ds = DatasetRecord(**data_dict)
        self.session.add(ds)
        await self.session.commit()
        await self.session.refresh(ds)
        return ds


class PipelineRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_run(self, run_id: str, task: str, dataset_version: Optional[str] = None, model_version: Optional[str] = None) -> PipelineRun:
        run = PipelineRun(
            run_id=run_id,
            task=task,
            start_time=datetime.utcnow(),
            status="RUNNING",
            dataset_version=dataset_version,
            model_version=model_version
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def complete_run(self, run_id: str, status: str, downloaded: int = 0, processed: int = 0, errors: Optional[str] = None) -> Optional[PipelineRun]:
        stmt = select(PipelineRun).where(PipelineRun.run_id == run_id)
        result = await self.session.execute(stmt)
        run = result.scalar_one_or_none()
        if run:
            run.end_time = datetime.utcnow()
            run.status = status
            run.records_downloaded = downloaded
            run.records_processed = processed
            run.errors = errors
            await self.session.commit()
            await self.session.refresh(run)
        return run

    async def get_recent_runs(self, limit: int = 20) -> List[PipelineRun]:
        stmt = select(PipelineRun).order_by(desc(PipelineRun.start_time)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
