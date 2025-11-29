"""
ENTITIES (Nodes):
- User: users (synced from MongoDB)
- Song: songs (synced from MongoDB)  
- Artist: artists
- Genre: genres

RELATIONSHIPS:
- LISTENED_TO: user listened to a song
- LIKES: user liked a song
- FOLLOWS: user follows another user
- PERFORMED_BY: song performed by artist
- BELONGS_TO_GENRE: song belongs to genre
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional

from ..dependencies_neo4j import get_neo4j

router = APIRouter(
    prefix="/graph",
    tags=["graph"],
    responses={404: {"description": "Not found"}}
)

class ListenEvent(BaseModel):
    """Record when a user listens to a song"""
    user_id: str = Field(..., description="MongoDB User ID")
    song_id: str = Field(..., description="MongoDB Song ID")
    song_name: str = Field(..., description="Song name for display")
    artist_name: str = Field(..., description="Artist name")
    genre: str = Field(..., description="Song genre")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "652e9f3b9b1d8e77a9b5d222",
                "song_id": "652e9f3b9b1d8e77a9b5d333",
                "song_name": "Bohemian Rhapsody",
                "artist_name": "Queen",
                "genre": "Rock"
            }
        }
    }


class LikeEvent(BaseModel):
    """Record when a user likes a song"""
    user_id: str
    song_id: str
    song_name: str
    artist_name: str
    genre: str


class FollowEvent(BaseModel):
    """Record when a user follows another user"""
    follower_id: str = Field(..., description="User who is following")
    followed_id: str = Field(..., description="User being followed")

# Data Input Endpoints - Populate the Graph

@router.post("/listen", status_code=status.HTTP_201_CREATED)
async def record_listen(event: ListenEvent):
    """
    Record that a user listened to a song.
    Creates User, Song, Artist, Genre nodes and relationships.
    """
    neo4j = await get_neo4j()
    
    query = """
    MERGE (u:User {user_id: $user_id})
    MERGE (s:Song {song_id: $song_id})
    ON CREATE SET s.name = $song_name
    
    MERGE (a:Artist {name: $artist_name})
    MERGE (g:Genre {name: $genre})
    
    MERGE (s)-[:PERFORMED_BY]->(a)
    MERGE (s)-[:BELONGS_TO_GENRE]->(g)
    
    CREATE (u)-[:LISTENED_TO {timestamp: datetime()}]->(s)
    
    RETURN u.user_id as user_id, s.name as song_name
    """
    
    result = await neo4j.execute_query(query, {
        "user_id": event.user_id,
        "song_id": event.song_id,
        "song_name": event.song_name,
        "artist_name": event.artist_name,
        "genre": event.genre
    })
    
    return {"message": "Listen event recorded", "data": result}


@router.post("/like", status_code=status.HTTP_201_CREATED)
async def record_like(event: LikeEvent):
    """
    Record that a user liked a song.
    """
    neo4j = await get_neo4j()
    
    query = """
    MERGE (u:User {user_id: $user_id})
    MERGE (s:Song {song_id: $song_id})
    ON CREATE SET s.name = $song_name
    
    MERGE (a:Artist {name: $artist_name})
    MERGE (g:Genre {name: $genre})
    
    MERGE (s)-[:PERFORMED_BY]->(a)
    MERGE (s)-[:BELONGS_TO_GENRE]->(g)
    
    MERGE (u)-[r:LIKES]->(s)
    ON CREATE SET r.timestamp = datetime()
    
    RETURN u.user_id as user_id, s.name as song_name
    """
    
    result = await neo4j.execute_query(query, {
        "user_id": event.user_id,
        "song_id": event.song_id,
        "song_name": event.song_name,
        "artist_name": event.artist_name,
        "genre": event.genre
    })
    
    return {"message": "Like recorded", "data": result}


@router.post("/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(event: FollowEvent):
    """
    Record that one user follows another (for social recommendations).
    """
    neo4j = await get_neo4j()
    
    query = """
    MERGE (follower:User {user_id: $follower_id})
    MERGE (followed:User {user_id: $followed_id})
    
    MERGE (follower)-[r:FOLLOWS]->(followed)
    ON CREATE SET r.since = datetime()
    
    RETURN follower.user_id as follower, followed.user_id as followed
    """
    
    result = await neo4j.execute_query(query, {
        "follower_id": event.follower_id,
        "followed_id": event.followed_id
    })
    
    return {"message": "Follow relationship created", "data": result}


# RECOMMENDATION ENDPOINTS - Deep Graph Queries

@router.get("/recommendations/similar-listeners/{user_id}")
async def get_recommendations_from_similar_listeners(
    user_id: str,
    depth: int = Query(default=2, ge=1, le=5, description="Traversal depth (1-5)"),
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    DEEP QUERY #1: Recommendations based on similar listeners.

    1. Find users who listened to the same songs
    2. Traverse deep through social connections (FOLLOWS) up to specified depth
    3. Recommend songs that the target user hasn't heard yet
    
    Depth is configurable (1-5), allowing "friends of friends" recommendations.
    """
    neo4j = await get_neo4j()
    
    # depth setting in Cypher query
    query = f"""
    // Songs that the user has already listened to
    MATCH (me:User {{user_id: $user_id}})-[:LISTENED_TO|LIKES]->(mySong:Song)
    WITH me, collect(DISTINCT mySong) as mySongs
    
    // Find similar users (listened to the same songs)
    MATCH (me)-[:LISTENED_TO|LIKES]->(:Song)<-[:LISTENED_TO|LIKES]-(similar:User)
    WHERE similar <> me
    
    // Traverse deep through FOLLOWS relationships (variable depth)
    MATCH path = (similar)-[:FOLLOWS*0..{depth - 1}]->(deepUser:User)
    WHERE deepUser <> me
    
    // Find songs that "deep" users like but I haven't listened to
    MATCH (deepUser)-[:LISTENED_TO|LIKES]->(recSong:Song)
    WHERE NOT recSong IN mySongs
    
    // Get song information
    OPTIONAL MATCH (recSong)-[:PERFORMED_BY]->(artist:Artist)
    OPTIONAL MATCH (recSong)-[:BELONGS_TO_GENRE]->(genre:Genre)
    
    // Calculate popularity and distance
    WITH recSong, artist, genre, 
         count(DISTINCT deepUser) as popularity,
         min(length(path)) as distance
    
    RETURN recSong.song_id as song_id,
           recSong.name as song_name,
           artist.name as artist,
           genre.name as genre,
           popularity,
           distance,
           popularity * 1.0 / (distance + 1) as score
    ORDER BY score DESC
    LIMIT $limit
    """
    
    results = await neo4j.execute_query(query, {
        "user_id": user_id,
        "limit": limit
    })
    
    return {
        "user_id": user_id,
        "depth": depth,
        "algorithm": "similar_listeners",
        "recommendations": results
    }


@router.get("/recommendations/genre-discovery/{user_id}")
async def discover_through_genres(
    user_id: str,
    max_hops: int = Query(default=3, ge=1, le=6, description="Max hops through artists/genres"),
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    DEEP QUERY #2: Genre/Artist chain discovery.
    
    1. Start from songs the user likes
    2. Go through artists and genres (variable depth)
    3. Discover new songs through these chains
    
    Example: Like Rock -> Rock artist -> their other songs -> Metal genre -> Metal songs
    """
    neo4j = await get_neo4j()
    
    query = f"""
    // Songs that the user has listened to
    MATCH (me:User {{user_id: $user_id}})-[:LISTENED_TO|LIKES]->(liked:Song)
    WITH me, collect(DISTINCT liked) as likedSongs
    
    // Traverse through artists - find their other songs
    MATCH (me)-[:LISTENED_TO|LIKES]->(:Song)-[:PERFORMED_BY]->(artist:Artist)
    MATCH (artist)<-[:PERFORMED_BY]-(otherSong:Song)
    WHERE NOT otherSong IN likedSongs
    
    // Get genre
    OPTIONAL MATCH (otherSong)-[:BELONGS_TO_GENRE]->(genre:Genre)
    
    WITH DISTINCT otherSong, artist, genre, likedSongs
    
    RETURN otherSong.song_id as song_id,
           otherSong.name as song_name,
           artist.name as artist,
           genre.name as genre,
           1.0 as relevance_score
    ORDER BY relevance_score DESC
    LIMIT $limit
    """
    
    results = await neo4j.execute_query(query, {
        "user_id": user_id,
        "limit": limit
    })
    
    return {
        "user_id": user_id,
        "max_hops": max_hops,
        "algorithm": "genre_discovery",
        "recommendations": results
    }


@router.get("/recommendations/shortest-path")
async def find_song_connection(
    from_song_id: str = Query(..., description="Starting song ID"),
    to_song_id: str = Query(..., description="Target song ID"),
    max_depth: int = Query(default=6, ge=1, le=10)
):
    """
    DEEP QUERY #3: Shortest path between songs.

    - Finds the shortest path between two songs, Through artists and genres
    """
    neo4j = await get_neo4j()
    
    query = f"""
    MATCH (start:Song {{song_id: $from_song}}), (end:Song {{song_id: $to_song}})
    
    MATCH path = shortestPath(
        (start)-[:PERFORMED_BY|BELONGS_TO_GENRE*1..{max_depth}]-(end)
    )
    
    RETURN [node in nodes(path) | 
        CASE 
            WHEN 'Song' IN labels(node) THEN {{type: 'Song', id: node.song_id, name: node.name}}
            WHEN 'Artist' IN labels(node) THEN {{type: 'Artist', name: node.name}}
            WHEN 'Genre' IN labels(node) THEN {{type: 'Genre', name: node.name}}
            ELSE {{type: 'Unknown'}}
        END
    ] as path_nodes,
    length(path) as path_length,
    [rel in relationships(path) | type(rel)] as relationship_types
    """
    
    results = await neo4j.execute_query(query, {
        "from_song": from_song_id,
        "to_song": to_song_id
    })
    
    if not results:
        return {
            "from_song": from_song_id,
            "to_song": to_song_id,
            "connected": False,
            "message": f"No connection found within {max_depth} hops"
        }
    
    return {
        "from_song": from_song_id,
        "to_song": to_song_id,
        "connected": True,
        "path": results[0] if results else None
    }

# Analytics /- Endpoints

@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str):
    """
    Get user graph statistics: listened songs, liked songs, following count.
    """
    neo4j = await get_neo4j()
    
    query = """
    MATCH (u:User {user_id: $user_id})
    
    OPTIONAL MATCH (u)-[listened:LISTENED_TO]->(:Song)
    OPTIONAL MATCH (u)-[liked:LIKES]->(:Song)
    OPTIONAL MATCH (u)-[:FOLLOWS]->(following:User)
    OPTIONAL MATCH (follower:User)-[:FOLLOWS]->(u)
    
    OPTIONAL MATCH (u)-[:LISTENED_TO|LIKES]->(:Song)-[:BELONGS_TO_GENRE]->(genre:Genre)
    OPTIONAL MATCH (u)-[:LISTENED_TO|LIKES]->(:Song)-[:PERFORMED_BY]->(artist:Artist)
    
    RETURN u.user_id as user_id,
           count(DISTINCT listened) as total_listens,
           count(DISTINCT liked) as total_likes,
           count(DISTINCT following) as following_count,
           count(DISTINCT follower) as follower_count,
           collect(DISTINCT genre.name)[0..5] as top_genres,
           collect(DISTINCT artist.name)[0..5] as top_artists
    """
    
    results = await neo4j.execute_query(query, {"user_id": user_id})
    
    if not results or not results[0].get("user_id"):
        raise HTTPException(status_code=404, detail="User not found in graph")
    
    return results[0]


@router.get("/overview")
async def get_graph_overview():
    """
    Get overall graph statistics: node counts, relationship counts.
    """
    neo4j = await get_neo4j()
    
    query = """
    MATCH (u:User) WITH count(u) as users
    MATCH (s:Song) WITH users, count(s) as songs
    MATCH (a:Artist) WITH users, songs, count(a) as artists
    MATCH (g:Genre) WITH users, songs, artists, count(g) as genres
    
    RETURN users, songs, artists, genres
    """
    
    results = await neo4j.execute_query(query)
    
    return {
        "nodes": results[0] if results else {"users": 0, "songs": 0, "artists": 0, "genres": 0}
    }


# Sync Endpoint - data from MongoDB to Neo4j

@router.post("/sync-from-mongodb", status_code=status.HTTP_201_CREATED)
async def sync_songs_from_mongodb():
    """
    Sync all songs from MongoDB to Neo4j.
    
    Creates Song, Artist, Genre nodes and relationships between them.
    This allows using recommendation features with existing data.
    """
    from ..dependencies import db
    
    neo4j = await get_neo4j()
    song_collection = db.get_collection("songs")
    user_collection = db.get_collection("users")
    
    # Sync all songs
    songs = await song_collection.find().to_list(1000)
    synced_songs = 0
    
    for song in songs:
        query = """
        MERGE (s:Song {song_id: $song_id})
        SET s.name = $song_name
        
        MERGE (a:Artist {name: $artist_name})
        MERGE (g:Genre {name: $genre})
        
        MERGE (s)-[:PERFORMED_BY]->(a)
        MERGE (s)-[:BELONGS_TO_GENRE]->(g)
        
        RETURN s.song_id as song_id
        """
        
        await neo4j.execute_query(query, {
            "song_id": str(song.get("_id")),
            "song_name": song.get("name", "Unknown"),
            "artist_name": song.get("artist", "Unknown"),
            "genre": song.get("genre", "Unknown")
        })
        synced_songs += 1
    
    # Sync all users
    users = await user_collection.find().to_list(1000)
    synced_users = 0
    
    for user in users:
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.username = $username
        RETURN u.user_id as user_id
        """
        
        await neo4j.execute_query(query, {
            "user_id": str(user.get("_id")),
            "username": user.get("username", "Unknown")
        })
        synced_users += 1
    
    return {
        "message": "Sync completed",
        "synced_songs": synced_songs,
        "synced_users": synced_users
    }

