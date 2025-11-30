"""
Neo4j Graph Database Connection for Spotify Clone
Handles connection to Neo4j for recommendation and graph-based features
"""

import os
from neo4j import GraphDatabase, AsyncGraphDatabase
from typing import Optional
import logging

from .config import Settings

logger = logging.getLogger(__name__)

def get_neo4j_settings():
    """Get Neo4j settings from config or environment"""
    settings = Settings()
    return {
        "uri": os.getenv("NEO4J_URI", settings.neo4j_uri),
        "user": os.getenv("NEO4J_USER", settings.neo4j_user),
        "password": os.getenv("NEO4J_PASSWORD", settings.neo4j_password)
    }


class Neo4jConnection:
    """
    Async Neo4j connection manager for the Spotify Clone application.
    Provides graph database functionality for:
    - Music recommendations based on listening history
    - Social features (following users, similar tastes)
    - Genre/Artist relationship traversals
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        neo4j_settings = get_neo4j_settings()
        self.uri = uri or neo4j_settings["uri"]
        self.user = user or neo4j_settings["user"]
        self.password = password or neo4j_settings["password"]
        self.driver: Optional[AsyncGraphDatabase.driver] = None
    
    async def connect(self):
        """Establish connection to Neo4j"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            await self.driver.verify_connectivity()
            logger.info("Neo4j connected successfully")
            
            # Initialize schema constraints
            await self._init_schema()
            
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j disconnected")
    
    async def _init_schema(self):
        """Initialize Neo4j schema with constraints and indexes"""
        async with self.driver.session() as session:
            # Create constraints for unique IDs
            constraints = [
                "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
                "CREATE CONSTRAINT song_id IF NOT EXISTS FOR (s:Song) REQUIRE s.song_id IS UNIQUE",
                "CREATE CONSTRAINT artist_name IF NOT EXISTS FOR (a:Artist) REQUIRE a.name IS UNIQUE",
                "CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE",
                "CREATE CONSTRAINT playlist_id IF NOT EXISTS FOR (p:Playlist) REQUIRE p.playlist_id IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    # Constraint might already exist
                    logger.debug(f"Constraint creation note: {e}")
            
            logger.info("Neo4j schema initialized")
    
    async def execute_query(self, query: str, parameters: dict = None):
        """Execute a Cypher query and return results"""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            return [record.data() async for record in result]
    
    async def execute_write(self, query: str, parameters: dict = None):
        """Execute a write transaction"""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            summary = await result.consume()
            return summary


# Global Neo4j connection instance
neo4j_connection: Optional[Neo4jConnection] = None


async def get_neo4j() -> Neo4jConnection:
    """Get or create the global Neo4j connection"""
    global neo4j_connection
    if neo4j_connection is None:
        neo4j_connection = Neo4jConnection()
        await neo4j_connection.connect()
    return neo4j_connection


async def init_neo4j():
    """Initialize Neo4j connection"""
    global neo4j_connection
    neo4j_connection = Neo4jConnection()
    await neo4j_connection.connect()


async def close_neo4j():
    """Close Neo4j connection"""
    global neo4j_connection
    if neo4j_connection:
        await neo4j_connection.disconnect()
        neo4j_connection = None
