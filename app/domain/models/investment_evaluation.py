import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models import Base


class InvestmentEvaluation(Base):
    __tablename__ = "investment_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("weather_snapshots.id"), nullable=False, unique=True
    )
    region_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("regions.id"), nullable=False
    )
    investment_level: Mapped[str] = mapped_column(String(50), nullable=False)
    base_fare: Mapped[float] = mapped_column(Float, nullable=False)
    incentive_pct: Mapped[float] = mapped_column(Float, nullable=False)
    incentive_amt: Mapped[float] = mapped_column(Float, nullable=False)
    total_investment: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL")
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    snapshot: Mapped["WeatherSnapshot"] = relationship(  # noqa: F821
        back_populates="evaluation"
    )
    region: Mapped["Region"] = relationship(back_populates="evaluations")  # noqa: F821
