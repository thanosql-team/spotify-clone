"""
Elasticsearch Connection for Spotify Clone
Handles connection to Elasticsearch for full-text search features
"""

import os
from elasticsearch import AsyncElasticsearch
from typing import Optional
import logging

from .config import Settings

logger = logging.getLogger(__name__)


def get_elasticsearch_settings():
    """Get Elasticsearch settings from config or environment"""
    settings = Settings()
    return {
        "host": os.getenv("ELASTICSEARCH_HOST", settings.elasticsearch_host),
        "port": int(os.getenv("ELASTICSEARCH_PORT", settings.elasticsearch_port)),
        "user": os.getenv("ELASTICSEARCH_USER", settings.elasticsearch_user),
        "password": os.getenv("ELASTICSEARCH_PASSWORD", settings.elasticsearch_password)
    }


class ElasticsearchConnection:
    """
    Async Elasticsearch connection manager for the Spotify Clone application.
    Provides full-text search functionality for:
    - Song search by name, artist, lyrics
    - Autocomplete/suggestions
    - Fuzzy matching
    """
    
    def __init__(self, host: str = None, port: int = None, user: str = None, password: str = None):
        es_settings = get_elasticsearch_settings()
        self.host = host or es_settings["host"]
        self.port = port or es_settings["port"]
        self.user = user or es_settings["user"]
        self.password = password or es_settings["password"]
        self.client: Optional[AsyncElasticsearch] = None
    
    async def connect(self):
        """Establish connection to Elasticsearch"""
        try:
            # Build connection URL
            if self.user and self.password:
                self.client = AsyncElasticsearch(
                    hosts=[f"http://{self.host}:{self.port}"],
                    basic_auth=(self.user, self.password)
                )
            else:
                self.client = AsyncElasticsearch(
                    hosts=[f"http://{self.host}:{self.port}"]
                )
            
            # Verify connectivity
            info = await self.client.info()
            logger.info(f"Elasticsearch connected: {info['version']['number']}")
            
            # Initialize indexes
            await self._init_indexes()
            
        except Exception as e:
            logger.error(f"Elasticsearch connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close Elasticsearch connection"""
        if self.client:
            await self.client.close()
            logger.info("Elasticsearch disconnected")
    
    async def _init_indexes(self):
        """Initialize Elasticsearch indexes for songs, albums, playlists"""
        
        # Songs index with full-text search capabilities
        songs_mapping = {
            "mappings": {
                "properties": {
                    "song_id": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "autocomplete": {
                                "type": "text",
                                "analyzer": "autocomplete"
                            }
                        }
                    },
                    "artist": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "genre": {"type": "keyword"},
                    "album_name": {"type": "text"},
                    "release_year": {"type": "integer"},
                    "duration": {"type": "integer"}
                }
            },
            "settings": {
                "analysis": {
                    "analyzer": {
                        "autocomplete": {
                            "tokenizer": "autocomplete",
                            "filter": ["lowercase"]
                        }
                    },
                    "tokenizer": {
                        "autocomplete": {
                            "type": "edge_ngram",
                            "min_gram": 2,
                            "max_gram": 20,
                            "token_chars": ["letter", "digit"]
                        }
                    }
                }
            }
        }
        
        # Create songs index if not exists
        if not await self.client.indices.exists(index="songs"):
            await self.client.indices.create(index="songs", body=songs_mapping)
            logger.info("Created 'songs' index")
        
        # Albums index
        albums_mapping = {
            "mappings": {
                "properties": {
                    "album_id": {"type": "keyword"},
                    "album_name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "artist_name": {"type": "text"},
                    "release_year": {"type": "integer"}
                }
            }
        }
        
        if not await self.client.indices.exists(index="albums"):
            await self.client.indices.create(index="albums", body=albums_mapping)
            logger.info("Created 'albums' index")
        
        # Playlists index
        playlists_mapping = {
            "mappings": {
                "properties": {
                    "playlist_id": {"type": "keyword"},
                    "playlist_name": {
                        "type": "text",
                        "analyzer": "standard",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "user_id": {"type": "keyword"},
                    "song_count": {"type": "integer"}
                }
            }
        }
        
        if not await self.client.indices.exists(index="playlists"):
            await self.client.indices.create(index="playlists", body=playlists_mapping)
            logger.info("Created 'playlists' index")
        
        logger.info("Elasticsearch indexes initialized")
    
    async def search(self, index: str, query: dict, size: int = 10):
        """Execute a search query"""
        if not self.client:
            raise RuntimeError("Elasticsearch client not initialized. Call connect() first.")
        
        result = await self.client.search(index=index, body=query, size=size)
        return result["hits"]["hits"]
    
    async def index_document(self, index: str, doc_id: str, document: dict):
        """Index a document"""
        if not self.client:
            raise RuntimeError("Elasticsearch client not initialized. Call connect() first.")
        
        await self.client.index(index=index, id=doc_id, document=document)
    
    async def delete_document(self, index: str, doc_id: str):
        """Delete a document"""
        if not self.client:
            raise RuntimeError("Elasticsearch client not initialized. Call connect() first.")
        
        await self.client.delete(index=index, id=doc_id, ignore=[404])
    
    async def bulk_index(self, index: str, documents: list[dict]):
        """Bulk index multiple documents"""
        if not self.client:
            raise RuntimeError("Elasticsearch client not initialized. Call connect() first.")
        
        from elasticsearch.helpers import async_bulk
        
        actions = [
            {
                "_index": index,
                "_id": doc.get("_id") or doc.get("song_id") or doc.get("album_id"),
                "_source": doc
            }
            for doc in documents
        ]
        
        await async_bulk(self.client, actions)


# Global Elasticsearch connection instance
elasticsearch_connection: Optional[ElasticsearchConnection] = None


async def get_elasticsearch() -> ElasticsearchConnection:
    """Get or create the global Elasticsearch connection"""
    global elasticsearch_connection
    if elasticsearch_connection is None:
        elasticsearch_connection = ElasticsearchConnection()
        await elasticsearch_connection.connect()
    return elasticsearch_connection


async def init_elasticsearch():
    """Initialize Elasticsearch connection"""
    global elasticsearch_connection
    elasticsearch_connection = ElasticsearchConnection()
    await elasticsearch_connection.connect()


async def close_elasticsearch():
    """Close Elasticsearch connection"""
    global elasticsearch_connection
    if elasticsearch_connection:
        await elasticsearch_connection.disconnect()
        elasticsearch_connection = None
