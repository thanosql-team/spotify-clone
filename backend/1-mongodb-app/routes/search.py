"""
Elasticsearch-based search routes for the Spotify Clone API
Provides full-text search, autocomplete, and fuzzy matching
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Literal
from enum import Enum

from ..dependencies_elasticsearch import get_elasticsearch

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
    size: int = Query(20, description="Number of results", ge=1, le=100)
):
    """
    Unified search across all entities or a specific entity type.
    
    Features:
    - Search all entities at once or filter by type
    - Searches genre field for songs automatically
    - Case-insensitive search
    - Smart fuzziness (disabled for short queries)
    - Relevance-based sorting
    
    Examples:
    - /search?q=love&entity=all
    - /search?q=rock&entity=song (searches in name, artist, album, AND genre)
    - /search?q=taylor&entity=album
    """
    es = await get_elasticsearch()
    
    # Determine fuzziness based on query length
    fuzziness = "AUTO:3,6" if len(q) >= 3 else None
    
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
            # Search across all song fields including genre
            songs_query = {
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["name^3", "artist^2", "album_name", "genre^2"],
                        "type": "best_fields"
                    }
                }
            }
            if fuzziness:
                songs_query["query"]["multi_match"]["fuzziness"] = fuzziness
            
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
            albums_query = {
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["album_name^3", "artist_name^2"],
                        "type": "best_fields"
                    }
                }
            }
            if fuzziness:
                albums_query["query"]["multi_match"]["fuzziness"] = fuzziness
            
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
            playlists_query = {
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["playlist_name^2"],
                        "type": "best_fields"
                    }
                }
            }
            if fuzziness:
                playlists_query["query"]["multi_match"]["fuzziness"] = fuzziness
            
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
    
    # Search users
    if EntityType.USER in search_entities:
        try:
            users_query = {
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["username^3", "name^2", "surname^2", "email"],
                        "type": "best_fields"
                    }
                }
            }
            if fuzziness:
                users_query["query"]["multi_match"]["fuzziness"] = fuzziness
            
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
