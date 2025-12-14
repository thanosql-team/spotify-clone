# MongoDB to Elasticsearch Migration Guide

This guide explains how to migrate your Spotify Clone data from MongoDB to Elasticsearch.

## Prerequisites

1. **Elasticsearch container is running**
   ```bash
   docker-compose up -d elasticsearch
   ```

2. **MongoDB has data to migrate**
   - Verify by checking your MongoDB collections

3. **Python dependencies installed**
   ```bash
   cd backend
   uv sync
   ```

## Quick Start

### Step 1: Start Elasticsearch
```bash
# From the project root
docker-compose up -d elasticsearch

# Wait for Elasticsearch to be healthy (check with)
docker-compose ps elasticsearch
```

### Step 2: Verify Elasticsearch is accessible
```bash
curl http://localhost:9200
```

You should see Elasticsearch info like:
```json
{
  "name" : "es01",
  "cluster_name" : "docker-cluster",
  "version" : {
    "number" : "8.11.0",
    ...
  }
}
```

### Step 3: Run the migration script
```bash
cd backend/1-mongodb-app
python -m migrate_to_elasticsearch
```

## What the Migration Does

The migration script will:

1. **Connect to MongoDB** - Uses your existing MongoDB connection
2. **Connect to Elasticsearch** - Connects to the Elasticsearch container (localhost:9200)
3. **Create indexes** - Automatically creates the following indexes if they don't exist:
   - `songs` - For song search with full-text capabilities
   - `albums` - For album search
   - `playlists` - For playlist search
   - `users` - For user search (optional)

4. **Migrate data** - Copies all documents from MongoDB collections to Elasticsearch indexes:
   - Converts MongoDB `ObjectId` to strings
   - Maps fields to appropriate Elasticsearch schema
   - Uses bulk indexing for performance

5. **Verify** - Checks document counts in both databases to ensure completeness

## Migration Output

You'll see output like:
```
============================================================
MongoDB to Elasticsearch Migration
============================================================
Initializing Elasticsearch connection...
✓ Elasticsearch connected

Starting songs migration...
Found 150 songs to migrate
✓ Successfully migrated 150 songs to Elasticsearch

Starting albums migration...
Found 50 albums to migrate
✓ Successfully migrated 50 albums to Elasticsearch

Starting playlists migration...
Found 30 playlists to migrate
✓ Successfully migrated 30 playlists to Elasticsearch

Starting users migration...
Found 10 users to migrate
✓ Successfully migrated 10 users to Elasticsearch

=== Verifying Migration ===
✓ songs: MongoDB=150, Elasticsearch=150
✓ albums: MongoDB=50, Elasticsearch=50
✓ playlists: MongoDB=30, Elasticsearch=30
✓ users: MongoDB=10, Elasticsearch=10

============================================================
Migration completed successfully!
============================================================
```

## Post-Migration

### Verify in Kibana
You can view your migrated data in Kibana:

1. Open Kibana: http://localhost:5601
2. Go to "Dev Tools"
3. Run queries:
   ```
   GET songs/_count
   GET songs/_search
   ```

### Using Elasticsearch in Your App

The FastAPI application now automatically:
- Initializes Elasticsearch on startup
- Closes connection on shutdown

To use Elasticsearch in your routes:
```python
from dependencies_elasticsearch import get_elasticsearch

@router.get("/search")
async def search_songs(query: str):
    es = await get_elasticsearch()
    
    search_query = {
        "query": {
            "multi_match": {
                "query": query,
                "fields": ["name^2", "artist", "album_name"]
            }
        }
    }
    
    results = await es.search("songs", search_query)
    return results
```

## Troubleshooting

### Elasticsearch not connecting
```bash
# Check if container is running
docker ps | grep elasticsearch

# Check logs
docker logs es01

# Restart container
docker-compose restart elasticsearch
```

### "Connection refused" error
- Ensure Elasticsearch container is running
- Verify port 9200 is accessible: `curl http://localhost:9200`
- Check `ELASTICSEARCH_HOST` and `ELASTICSEARCH_PORT` in your `.env` file

### Index already exists with wrong mapping
```bash
# Delete and recreate indexes
curl -X DELETE http://localhost:9200/songs
curl -X DELETE http://localhost:9200/albums
curl -X DELETE http://localhost:9200/playlists

# Re-run migration
python -m migrate_to_elasticsearch
```

### MongoDB connection issues
- Verify your `MONGODB_URL` in `.env` file
- Ensure MongoDB is accessible

## Re-running Migration

The migration is idempotent and can be re-run safely:
- If indexes exist, they won't be recreated
- Documents will be **overwritten** with the same ID
- No duplicates will be created

To start fresh:
```bash
# Delete all Elasticsearch data
curl -X DELETE http://localhost:9200/_all

# Re-run migration
python -m migrate_to_elasticsearch
```

## Advanced Usage

### Migrate only specific collections

Edit `migrate_to_elasticsearch.py` and comment out the migrations you don't need:

```python
# In main() function
# await migrate_songs()
await migrate_albums()  # Only migrate albums
# await migrate_playlists()
# await migrate_users()
```

### Custom field mappings

Edit the schema in `dependencies_elasticsearch.py` in the `_init_indexes()` method.

### Continuous sync

For real-time sync, you can:
1. Use MongoDB Change Streams (see `change_logger.py`)
2. Update Elasticsearch whenever MongoDB is updated
3. Add ES indexing to your route handlers

Example in `routes/songs.py`:
```python
from dependencies_elasticsearch import get_elasticsearch

@router.post("/songs", response_model=Song)
async def create_song(song: SongCreate):
    # Insert to MongoDB
    result = await song_collection.insert_one(new_song)
    
    # Index to Elasticsearch
    es = await get_elasticsearch()
    await es.index_document("songs", str(result.inserted_id), new_song)
    
    return new_song
```

## Environment Variables

Add to your `.env` file:
```env
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USER=
ELASTICSEARCH_PASSWORD=
```

## Performance

- **Bulk indexing** is used for efficient migration
- Migration time depends on data size:
  - 1,000 documents: ~5 seconds
  - 10,000 documents: ~30 seconds
  - 100,000 documents: ~5 minutes

## Next Steps

1. ✅ Migrate data to Elasticsearch
2. 🔍 Implement search endpoints using Elasticsearch
3. 📊 Use Kibana to visualize and analyze data
4. 🔄 Set up real-time sync between MongoDB and Elasticsearch
5. 🚀 Add advanced features like autocomplete, fuzzy search, facets
