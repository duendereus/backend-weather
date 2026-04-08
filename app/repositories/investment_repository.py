import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.models.investment_evaluation import InvestmentEvaluation


class InvestmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_evaluation(self, evaluation: InvestmentEvaluation) -> InvestmentEvaluation:
        self._session.add(evaluation)
        await self._session.flush()
        await self._session.refresh(evaluation)
        return evaluation

    async def get_history(
        self,
        *,
        region_id: uuid.UUID | None = None,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InvestmentEvaluation]:
        stmt = (
            select(InvestmentEvaluation)
            .options(joinedload(InvestmentEvaluation.region))
            .order_by(InvestmentEvaluation.evaluated_at.desc())
        )
        if region_id is not None:
            stmt = stmt.where(InvestmentEvaluation.region_id == region_id)
        if source is not None:
            stmt = stmt.where(InvestmentEvaluation.source == source)
        stmt = stmt.limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
