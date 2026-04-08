"""seed_incentive_configs

Revision ID: 00a3569bb1ee
Revises: ca498f0c03d9
Create Date: 2026-04-08 20:14:23.487854

"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00a3569bb1ee'
down_revision: Union[str, None] = 'ca498f0c03d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Default incentive configs from README
SEED_DATA = [
    {"condition": "CLEAR",        "base_fare": 120.0, "incentive_pct": 0.0},
    {"condition": "CLOUDS",       "base_fare": 120.0, "incentive_pct": 5.0},
    {"condition": "DRIZZLE",      "base_fare": 120.0, "incentive_pct": 15.0},
    {"condition": "RAIN",         "base_fare": 120.0, "incentive_pct": 35.0},
    {"condition": "THUNDERSTORM", "base_fare": 120.0, "incentive_pct": 60.0},
    {"condition": "SNOW",         "base_fare": 120.0, "incentive_pct": 60.0},
    {"condition": "EXTREME",      "base_fare": 120.0, "incentive_pct": 100.0},
]


def upgrade() -> None:
    table = sa.table(
        "incentive_configs",
        sa.column("id", sa.Uuid),
        sa.column("condition", sa.String),
        sa.column("base_fare", sa.Float),
        sa.column("incentive_pct", sa.Float),
    )
    op.bulk_insert(table, [
        {"id": uuid.uuid4(), **row} for row in SEED_DATA
    ])


def downgrade() -> None:
    op.execute(
        "DELETE FROM incentive_configs WHERE condition IN ("
        "'CLEAR','CLOUDS','DRIZZLE','RAIN','THUNDERSTORM','SNOW','EXTREME')"
    )
