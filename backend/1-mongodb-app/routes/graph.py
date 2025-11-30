"""
ENTITIES (Nodes):
- User: users (synced from MongoDB)
- Song: songs (synced from MongoDB)  
- Artist: artists
- Genre: genres

RELATIONSHIPS:
- LISTENED_TO: user listened to a song
- PERFORMED_BY: song performed by artist
- BELONGS_TO_GENRE: song belongs to genre
"""

from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId

from ..dependencies_neo4j import get_neo4j

router = APIRouter(
    prefix="/graph",
    tags=["graph"],
    responses={404: {"description": "Not found"}}
)

@router.get("/recommendations/playlist/{playlist_id}")
async def recommend_songs_for_playlist(
    playlist_id: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Playlist-based song recommendations.
    
    Finds songs with matching genres and artists from the playlist,
    ranked by relevance (artist match > genre match).
    """
    from ..dependencies import db
    neo4j = await get_neo4j()
    playlist_collection = db.get_collection("playlists")
    
    playlist = await playlist_collection.find_one({"_id": ObjectId(playlist_id)})
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    song_ids = [str(sid) for sid in playlist.get("song_ID", [])]
    if not song_ids:
        return {
            "playlist_id": playlist_id,
            "recommendations": [],
            "message": "Playlist is empty"
        }
        
    # Counts frequency of each genre in playlist
    # Counts frequency of each artist
    # Computes a score = genre match weight + artist match weight
    # Returns songs ordered by total score
    
    query = """
    MATCH (targetSong:Song)
    WHERE targetSong.song_id IN $song_ids

    // Collect playlist genres
    MATCH (targetSong)-[:BELONGS_TO_GENRE]->(tg:Genre)
    WITH collect(tg.name) AS allGenres, $song_ids AS song_ids

    // Genre weights
    UNWIND allGenres AS g
    WITH song_ids, g, count(g) AS genre_weight
    WITH song_ids, collect({genre: g, weight: genre_weight}) AS genreWeights

    // Collect playlist artists
    MATCH (ts:Song)
    WHERE ts.song_id IN song_ids
    MATCH (ts)-[:PERFORMED_BY]->(ta:Artist)
    WITH song_ids, genreWeights, collect(ta.name) AS allArtists

    // Artist weights
    UNWIND allArtists AS a
    WITH song_ids, genreWeights, a, count(a) AS artist_weight
    WITH song_ids, genreWeights, collect({artist: a, weight: artist_weight}) AS artistWeights

    // Score candidate songs
    MATCH (similar:Song)
    WHERE NOT similar.song_id IN song_ids
    OPTIONAL MATCH (similar)-[:BELONGS_TO_GENRE]->(sg:Genre)
    OPTIONAL MATCH (similar)-[:PERFORMED_BY]->(sa:Artist)
    WITH similar, sg, sa, genreWeights, artistWeights,

        // Genre score
        reduce(gScore = 0, gw IN genreWeights |
            CASE WHEN sg.name = gw.genre THEN gScore + gw.weight ELSE gScore END
        ) AS genreScore,

        // Artist score
        reduce(aScore = 0, aw IN artistWeights |
            CASE WHEN sa.name = aw.artist THEN aScore + (aw.weight * 3) ELSE aScore END
        ) AS artistScore

    WITH similar,
        coalesce(genreScore, 0) AS genreScore,
        coalesce(artistScore, 0) AS artistScore,
        (genreScore + artistScore) AS relevance,
        sa, sg

    RETURN similar.song_id AS song_id,
        similar.name AS song_name,
        collect(DISTINCT sa.name) AS artists,
        collect(DISTINCT sg.name) AS genres,
        relevance
    ORDER BY relevance DESC, song_name ASC
    LIMIT $limit
    """
    
    results = await neo4j.execute_query(query, {
        "song_ids": song_ids,
        "limit": limit
    })
    
    return {
        "playlist_id": playlist_id,
        "recommendations": results
    }

@router.get("/recommendations/deep/{user_id}")
async def deep_graph_recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Deep Graph Search (Gili Paieška)

    Finds similar users based on shared music preferences (artists/genres)
    and recommends songs from those users, even when no songs overlap.
    """
    neo4j = await get_neo4j()

    query = """
    MATCH (u:User {user_id: $user_id})
    
    // Get user's preferred artists and genres
    MATCH (u)-[:LISTENED_TO]->(userSong:Song)
    OPTIONAL MATCH (userSong)-[:PERFORMED_BY]->(userArtist:Artist)
    OPTIONAL MATCH (userSong)-[:BELONGS_TO_GENRE]->(userGenre:Genre)
    
    WITH u, 
         collect(DISTINCT userArtist.name) AS userArtists,
         collect(DISTINCT userGenre.name) AS userGenres
    
    // Find other users and calculate similarity
    MATCH (other:User)
    WHERE other.user_id <> $user_id
    
    MATCH (other)-[:LISTENED_TO]->(otherSong:Song)
    OPTIONAL MATCH (otherSong)-[:PERFORMED_BY]->(otherArtist:Artist)
    OPTIONAL MATCH (otherSong)-[:BELONGS_TO_GENRE]->(otherGenre:Genre)
    
    WITH u, userArtists, userGenres, other,
         collect(DISTINCT otherArtist.name) AS otherArtists,
         collect(DISTINCT otherGenre.name) AS otherGenres
    
    // Calculate similarity scores
    WITH u, other,
         // Artist similarity (weighted more heavily)
         size([a IN userArtists WHERE a IN otherArtists]) * 3 AS artistSimilarity,
         // Genre similarity  
         size([g IN userGenres WHERE g IN otherGenres]) * 1 AS genreSimilarity,
         otherArtists, otherGenres
    
    WITH u, other, 
         (artistSimilarity + genreSimilarity) AS totalSimilarity,
         otherArtists, otherGenres
    WHERE totalSimilarity > 0
    
    // Get recommendations from similar users
    MATCH (other)-[:LISTENED_TO]->(recommendedSong:Song)
    WHERE NOT (u)-[:LISTENED_TO]->(recommendedSong)
    
    OPTIONAL MATCH (recommendedSong)-[:PERFORMED_BY]->(ra:Artist)
    OPTIONAL MATCH (recommendedSong)-[:BELONGS_TO_GENRE]->(rg:Genre)
    
    // Boost score if recommended song has familiar artists/genres
    WITH recommendedSong, totalSimilarity, ra, rg, u,
         collect(DISTINCT ra.name) AS recArtists,
         collect(DISTINCT rg.name) AS recGenres
    
    MATCH (u)-[:LISTENED_TO]->(userSong:Song)
    OPTIONAL MATCH (userSong)-[:PERFORMED_BY]->(ua:Artist)  
    OPTIONAL MATCH (userSong)-[:BELONGS_TO_GENRE]->(ug:Genre)
    
    WITH recommendedSong, totalSimilarity, recArtists, recGenres,
         collect(DISTINCT ua.name) AS userArtists,
         collect(DISTINCT ug.name) AS userGenres
    
    WITH recommendedSong,
         totalSimilarity +
         size([a IN recArtists WHERE a IN userArtists]) * 2 +  // Bonus for familiar artist
         size([g IN recGenres WHERE g IN userGenres]) * 1      // Bonus for familiar genre
         AS finalScore,
         recArtists, recGenres
    
    RETURN DISTINCT recommendedSong.song_id AS song_id,
           recommendedSong.name AS song_name,
           recArtists AS artists,
           recGenres AS genres,
           finalScore AS relevance
    ORDER BY relevance DESC, song_name ASC
    LIMIT $limit
    """

    results = await neo4j.execute_query(query, {
        "user_id": user_id,
        "limit": limit
    })

    return {
        "user_id": user_id,
        "deep_recommendations": results
    }

@router.post("/sync-playlist/{playlist_id}")
async def sync_playlist_to_neo4j(playlist_id: str):
    """
    Sync a playlist and create LISTENED_TO relationships.
    """
    from ..dependencies import db
    neo4j = await get_neo4j()
    
    playlist_collection = db.get_collection("playlists")
    song_collection = db.get_collection("songs")
    
    playlist = await playlist_collection.find_one({"_id": ObjectId(playlist_id)})
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    user_id = str(playlist.get("user_id", "unknown"))
    song_ids = playlist.get("song_ID", [])
    
    await neo4j.execute_query("""
        MERGE (u:User {user_id: $user_id})
    """, {"user_id": user_id})
    
    synced_songs = 0
    
    for song_id in song_ids:
        song = await song_collection.find_one({"_id": ObjectId(song_id)})
        if not song:
            continue
        
        await neo4j.execute_query("""
            MERGE (s:Song {song_id: $song_id})
            SET s.name = $song_name
            
            MERGE (a:Artist {name: $artist_name})
            MERGE (g:Genre {name: $genre})
            
            MERGE (s)-[:PERFORMED_BY]->(a)
            MERGE (s)-[:BELONGS_TO_GENRE]->(g)
            
            WITH s
            MATCH (u:User {user_id: $user_id})
            MERGE (u)-[:LISTENED_TO]->(s)
        """, {
            "song_id": str(song_id),
            "song_name": song.get("name", "Unknown"),
            "artist_name": song.get("artist", "Unknown"),
            "genre": song.get("genre", "Unknown"),
            "user_id": user_id
        })
        synced_songs += 1
    
    return {
        "message": "Playlist synced",
        "synced_songs": synced_songs
    }

@router.post("/sync-all-playlists")
async def sync_all_playlists():
    from ..dependencies import db
    neo4j = await get_neo4j()

    playlist_collection = db.get_collection("playlists")
    playlists = await playlist_collection.find().to_list(1000)

    synced_count = 0
    for playlist in playlists:
        playlist_id = str(playlist["_id"])
        await sync_playlist_to_neo4j(playlist_id)
        synced_count += 1

    return {"message": "All playlists synced", "count": synced_count}

@router.get("/overview")
async def get_graph_overview():
    """Get graph statistics."""
    neo4j = await get_neo4j()
    
    query = """
    MATCH (u:User) WITH count(u) as users
    MATCH (s:Song) WITH users, count(s) as songs
    MATCH (a:Artist) WITH users, songs, count(a) as artists
    MATCH (g:Genre) WITH users, songs, artists, count(g) as genres
    RETURN users, songs, artists, genres
    """
    
    results = await neo4j.execute_query(query)
    return {"nodes": results[0] if results else {}}

@router.post("/sync-from-mongodb", status_code=status.HTTP_201_CREATED)
async def sync_songs_from_mongodb():
    """Sync songs and users from MongoDB to Neo4j."""
    from ..dependencies import db
    
    neo4j = await get_neo4j()
    song_collection = db.get_collection("songs")
    user_collection = db.get_collection("users")
    
    songs = await song_collection.find().to_list(1000)
    synced_songs = 0
    
    for song in songs:
        await neo4j.execute_query("""
            MERGE (s:Song {song_id: $song_id})
            SET s.name = $song_name
            
            MERGE (a:Artist {name: $artist_name})
            MERGE (g:Genre {name: $genre})
            
            MERGE (s)-[:PERFORMED_BY]->(a)
            MERGE (s)-[:BELONGS_TO_GENRE]->(g)
        """, {
            "song_id": str(song.get("_id")),
            "song_name": song.get("name", "Unknown"),
            "artist_name": song.get("artist", "Unknown"),
            "genre": song.get("genre", "Unknown")
        })
        synced_songs += 1
    
    users = await user_collection.find().to_list(1000)
    synced_users = 0
    
    for user in users:
        await neo4j.execute_query("""
            MERGE (u:User {user_id: $user_id})
            SET u.username = $username
        """, {
            "user_id": str(user.get("_id")),
            "username": user.get("username", "Unknown")
        })
        synced_users += 1
    
    return {
        "message": "Sync completed",
        "synced_songs": synced_songs,
        "synced_users": synced_users
    }