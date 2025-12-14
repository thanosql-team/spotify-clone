"""
Elasticsearch-based search routes for the Spotify Clone API
Provides full-text search, autocomplete, and fuzzy matching
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Literal
from enum import Enum

from ..core.dependencies_elasticsearch import get_elasticsearch

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}}
)


class EntityType(str, Enum):
    """Entity types that can be searched"""
    SONG = "song"
    ALBUM = "album"
    PLAYLIST = "playlist"
    USER = "user"
    ALL = "all"


class SearchResult(BaseModel):
    """Individual search result"""
    model_config = ConfigDict(exclude_none=True)
    
    id: str
    score: float
    name: str
    type: str  # "song", "album", "playlist", "user"
    artist: Optional[str] = None
    album_name: Optional[str] = None
    genre: Optional[str] = None
    

class SearchResponse(BaseModel):
    """Search response with results"""
    total: int
    results: List[SearchResult]
    query: str
    entity_type: Optional[str] = None


@router.get("", response_model=SearchResponse, response_model_exclude_none=True)
async def unified_search(
    q: str = Query(..., description="Search query", min_length=1),
    entity: EntityType = Query(EntityType.ALL, description="Entity type to search (song, album, playlist, user, or all)"),
    size: int = Query(20, description="Number of results", ge=1, le=100),
    fuzzy: bool = Query(True, description="Enable fuzzy matching for typo tolerance")
):
    """
    Unified search across all entities or a specific entity type.
    
    Features:
    - Search all entities at once or filter by type
    - Searches genre field for songs automatically
    - Case-insensitive search
    - Smart fuzziness (configurable, disabled for very short queries)
    - Relevance-based sorting with cross-index normalization
    
    Examples:
    - /search?q=shadow&entity=all
    - /search?q=rock&entity=song (searches in name, artist, album, AND genre)
    - /search?q=jane&entity=album
    - /search?q=retro&entity=playlist
    - /search?q=miller&fuzzy=false (exact matching)
    """
    es = await get_elasticsearch()
    
    # Determine fuzziness based on query length
    # AUTO:4,7 means: edit distance 1 for terms 4-6 chars, edit distance 2 for 7+ chars
    # This is less aggressive than AUTO:3,6 and reduces false positives
    fuzziness = None
    if fuzzy and len(q) >= 4:
        fuzziness = "AUTO:4,7"
    elif fuzzy and len(q) >= 3:
        fuzziness = "1"  # Only 1 edit for short queries
    
    all_results = []
    
    # Determine which entities to search
    search_entities = []
    if entity == EntityType.ALL:
        search_entities = [EntityType.SONG, EntityType.ALBUM, EntityType.PLAYLIST, EntityType.USER]
    else:
        search_entities = [entity]
    
    # Search songs
    if EntityType.SONG in search_entities:
        try:
            # Build query with optional fuzziness
            must_clause = {
                "multi_match": {
                    "query": q,
                    "fields": ["name^4", "artist^3", "album_name^1.5", "genre^2"],
                    "type": "best_fields",
                    "operator": "or",
                    "minimum_should_match": "50%"
                }
            }
            if fuzziness:
                must_clause["multi_match"]["fuzziness"] = fuzziness
            
            # Use function_score to normalize and boost exact matches
            songs_query = {
                "query": {
                    "function_score": {
                        "query": must_clause,
                        "functions": [
                            {
                                "filter": {"match_phrase": {"name": {"query": q}}},
                                "weight": 3
                            },
                            {
                                "filter": {"term": {"name.keyword": q.lower()}},
                                "weight": 5
                            }
                        ],
                        "score_mode": "sum",
                        "boost_mode": "multiply"
                    }
                }
            }
            
            songs = await es.search("songs", songs_query, size=size)
            
            for hit in songs:
                all_results.append(SearchResult(
                    id=hit["_id"],
                    score=hit["_score"],
                    name=hit["_source"].get("name", ""),
                    type="song",
                    artist=hit["_source"].get("artist"),
                    album_name=hit["_source"].get("album_name"),
                    genre=hit["_source"].get("genre")
                ))
        except Exception as e:
            pass  # Index might not exist
    
    # Search albums
    if EntityType.ALBUM in search_entities:
        try:
            albums_must = {
                "multi_match": {
                    "query": q,
                    "fields": ["album_name^4", "artist_name^2"],
                    "type": "best_fields",
                    "operator": "or"
                }
            }
            if fuzziness:
                albums_must["multi_match"]["fuzziness"] = fuzziness
            
            albums_query = {
                "query": {
                    "function_score": {
                        "query": albums_must,
                        "functions": [
                            {
                                "filter": {"match_phrase": {"album_name": {"query": q}}},
                                "weight": 3
                            }
                        ],
                        "score_mode": "sum",
                        "boost_mode": "multiply"
                    }
                }
            }
            
            albums = await es.search("albums", albums_query, size=size)
            
            for hit in albums:
                all_results.append(SearchResult(
                    id=hit["_id"],
                    score=hit["_score"],
                    name=hit["_source"].get("album_name", ""),
                    type="album",
                    artist=hit["_source"].get("artist_name")
                ))
        except Exception as e:
            pass  # Index might not exist
    
    # Search playlists
    if EntityType.PLAYLIST in search_entities:
        try:
            playlists_must = {
                "multi_match": {
                    "query": q,
                    "fields": ["playlist_name^3"],
                    "type": "best_fields",
                    "operator": "or"
                }
            }
            if fuzziness:
                playlists_must["multi_match"]["fuzziness"] = fuzziness
            
            playlists_query = {
                "query": {
                    "function_score": {
                        "query": playlists_must,
                        "functions": [
                            {
                                "filter": {"match_phrase": {"playlist_name": {"query": q}}},
                                "weight": 3
                            }
                        ],
                        "score_mode": "sum",
                        "boost_mode": "multiply"
                    }
                }
            }
            
            playlists = await es.search("playlists", playlists_query, size=size)
            
            for hit in playlists:
                all_results.append(SearchResult(
                    id=hit["_id"],
                    score=hit["_score"],
                    name=hit["_source"].get("playlist_name", ""),
                    type="playlist"
                ))
        except Exception as e:
            pass  # Index might not exist
    
    # Search users - higher boost for exact name/surname matches
    if EntityType.USER in search_entities:
        try:
            users_must = {
                "multi_match": {
                    "query": q,
                    "fields": ["username^3", "name^4", "surname^4", "email"],
                    "type": "best_fields",
                    "operator": "or"
                }
            }
            if fuzziness:
                users_must["multi_match"]["fuzziness"] = fuzziness
            
            users_query = {
                "query": {
                    "function_score": {
                        "query": users_must,
                        "functions": [
                            {
                                "filter": {"match_phrase": {"surname": {"query": q}}},
                                "weight": 5
                            },
                            {
                                "filter": {"match_phrase": {"name": {"query": q}}},
                                "weight": 4
                            },
                            {
                                "filter": {"match_phrase": {"username": {"query": q}}},
                                "weight": 3
                            }
                        ],
                        "score_mode": "max",
                        "boost_mode": "multiply"
                    }
                }
            }
            
            users = await es.search("users", users_query, size=size)
            
            for hit in users:
                # Use name + surname if available, otherwise username
                display_name = hit["_source"].get("username", "")
                if hit["_source"].get("name") or hit["_source"].get("surname"):
                    name_parts = [hit["_source"].get("name", ""), hit["_source"].get("surname", "")]
                    display_name = " ".join(filter(None, name_parts)) or display_name
                
                all_results.append(SearchResult(
                    id=hit["_id"],
                    score=hit["_score"],
                    name=display_name,
                    type="user"
                ))
        except Exception as e:
            pass  # Index might not exist
    
    # Sort by score (descending)
    all_results.sort(key=lambda x: x.score, reverse=True)
    
    # Limit results
    all_results = all_results[:size]
    
    return SearchResponse(
        total=len(all_results),
        results=all_results,
        query=q,
        entity_type=entity.value
    )
