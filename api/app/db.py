import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_log (
    id bigserial PRIMARY KEY,
    created_at timestamptz NOT NULL DEFAULT now(),
    status text NOT NULL,
    route text NOT NULL,
    model text,
    passes int NOT NULL,
    scores jsonb NOT NULL,
    entity_types jsonb NOT NULL,
    latency_ms int NOT NULL
)"""


async def init_db() -> None:
    async with await psycopg.AsyncConnection.connect(config.DATABASE_URL) as conn:
        await conn.execute(SCHEMA)


async def log_decision(result, latency_ms: int) -> None:
    async with await psycopg.AsyncConnection.connect(config.DATABASE_URL) as conn:
        await conn.execute(
            """INSERT INTO decision_log (status, route, model, passes, scores, entity_types, latency_ms)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (result.status, result.route, result.model, result.passes,
             Jsonb(result.scores), Jsonb(result.entities), latency_ms),
        )


async def recent(limit: int = 20) -> list[dict]:
    async with await psycopg.AsyncConnection.connect(config.DATABASE_URL) as conn:
        cur = conn.cursor(row_factory=dict_row)
        await cur.execute("SELECT * FROM decision_log ORDER BY id DESC LIMIT %s", (limit,))
        return await cur.fetchall()