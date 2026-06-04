"""
Neo4j async driver client for BloodBridge AI.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from neo4j import GraphDatabase, AsyncDriver, AsyncSession
from core.config import get_settings

logger = logging.getLogger(__name__)

_driver: AsyncDriver = None

def get_driver() -> AsyncDriver:
    """Get the Neo4j AsyncDriver singleton instance."""
    global _driver
    if _driver is None:
        settings = get_settings()
        if not settings.NEO4J_URI:
            logger.warning("NEO4J_URI is not set. Neo4j operations will fail.")
        _driver = GraphDatabase.async_driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
    return _driver

@asynccontextmanager
async def get_neo4j() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager yielding a Neo4j session.
    Usage:
        async with get_neo4j() as session:
            await session.run(...)
    """
    driver = get_driver()
    session = driver.session()
    try:
        yield session
    finally:
        await session.close()

async def health_check() -> bool:
    """Verify connectivity to Neo4j graph database."""
    try:
        driver = get_driver()
        # Verify connectivity using a quick query
        await driver.verify_connectivity()
        async with get_neo4j() as session:
            result = await session.run("RETURN 1 AS ok")
            record = await result.single()
            return record is not None and record["ok"] == 1
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}", exc_info=True)
        return False

async def close():
    """Close the Neo4j AsyncDriver singleton."""
    global _driver
    if _driver is not None:
        logger.info("Closing Neo4j async driver...")
        await _driver.close()
        _driver = None
