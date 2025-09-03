import importlib.util
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text

from pyctuator.health.async_health_provider import AsyncHealthProvider, HealthStatus, Status
from pyctuator.health.db_health_provider import DbHealthDetails, DbHealthStatus


class AsyncDbHealthProvider(AsyncHealthProvider):

    def __init__(self, engine: AsyncEngine, name: str = "db") -> None:
        super().__init__()
        self.engine = engine
        self.name = name

    def is_supported(self) -> bool:
        return importlib.util.find_spec("sqlalchemy") is not None

    def get_name(self) -> str:
        return self.name

    async def get_health(self) -> DbHealthStatus:
        try:
            async with self.engine.begin() as conn:
                # Use the dialect-specific select one query for compatibility
                # This is equivalent to what do_ping() uses in the sync version
                dialect_specific_query = self.engine.sync_engine.dialect._dialect_specific_select_one
                await conn.execute(text(dialect_specific_query))
                return DbHealthStatus(
                    status=Status.UP,
                    details=DbHealthDetails(self.engine.name)
                )

        except Exception as e:  # pylint: disable=broad-except
            return DbHealthStatus(
                status=Status.DOWN, 
                details=DbHealthDetails(self.engine.name, str(e))
            ) 