# Elasticsearch Migration Troubleshooting Guide

## Quick Diagnostics

Run this command to check everything:
```bash
# Check all services
docker-compose ps

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health?pretty

# Check if data exists in MongoDB
python3 -c "
from backend['1-mongodb-app'].dependencies import db
import asyncio

async def check():
    collections = ['songs', 'albums', 'playlists', 'users']
    for col in collections:
        count = await db[col].count_documents({})
        print(f'{col}: {count} documents')

asyncio.run(check())
"
```

---

## Issue: Elasticsearch Container Won't Start

### Symptoms:
- `docker-compose up -d elasticsearch` fails
- Container exits immediately
- "Connection refused" errors

### Solutions:

#### 1. Check Docker Resources
```bash
# Elasticsearch needs at least 512MB RAM
docker stats

# If memory is low, restart Docker
# Or increase Docker Desktop resources
```

#### 2. Check Port Conflicts
```bash
# See if port 9200 is already in use
sudo lsof -i :9200

# Kill the process if needed
sudo kill -9 <PID>
```

#### 3. Reset Elasticsearch Data
```bash
# Remove existing volume
docker-compose down -v
docker volume rm spotify-clone_elasticsearch-data

# Start fresh
docker-compose up -d elasticsearch
```

#### 4. Check Logs
```bash
docker logs es01

# Common errors:
# - "max virtual memory areas too low" → Increase vm.max_map_count
# - "insufficient memory" → Increase Docker memory
```

#### 5. Fix vm.max_map_count (Linux)
```bash
# Temporary fix
sudo sysctl -w vm.max_map_count=262144

# Permanent fix
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## Issue: Migration Script Fails

### Symptoms:
- `python -m migrate_to_elasticsearch` throws errors
- "Module not found" errors
- Connection errors

### Solutions:

#### 1. Check Python Environment
```bash
cd backend/1-mongodb-app

# Check if in correct directory
pwd

# Should show: .../backend/1-mongodb-app
```

#### 2. Install Dependencies
```bash
cd backend
poetry install

# Or with pip
pip install -r requirements.txt
```

#### 3. Check MongoDB Connection
```bash
# Verify .env file exists at project root
cat ../../.env | grep MONGODB_URL

# Test connection
python3 -c "
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv('../../.env')
url = os.getenv('MONGODB_URL')
print(f'MongoDB URL: {url}')

async def test():
    client = AsyncIOMotorClient(url)
    result = await client.server_info()
    print('MongoDB connected:', result['version'])

asyncio.run(test())
"
```

#### 4. Check Elasticsearch Connection
```bash
# Test basic connection
curl http://localhost:9200

# Should return JSON with cluster info
```

#### 5. Run with Debug Logging
```bash
# Set logging level to DEBUG
export PYTHONPATH=../..:$PYTHONPATH
python -m migrate_to_elasticsearch
```

---

## Issue: No Data in Elasticsearch After Migration

### Symptoms:
- Migration completes successfully
- But `curl http://localhost:9200/songs/_count` shows 0

### Solutions:

#### 1. Verify MongoDB Has Data
```bash
# Connect to MongoDB and check
python3 -c "
from backend['1-mongodb-app'].dependencies import db
import asyncio

async def check():
    songs = await db['songs'].count_documents({})
    print(f'Songs in MongoDB: {songs}')

asyncio.run(check())
"
```

#### 2. Check Elasticsearch Logs
```bash
docker logs es01 | grep -i error
```

#### 3. Check Migration Script Output
Look for these messages:
```
✓ Successfully migrated X songs to Elasticsearch
✓ songs: MongoDB=X, Elasticsearch=X
```

#### 4. Manually Check Elasticsearch
```bash
# List all indexes
curl http://localhost:9200/_cat/indices?v

# Search songs
curl http://localhost:9200/songs/_search?pretty

# Get specific document
curl http://localhost:9200/songs/_doc/<some-id>?pretty
```

#### 5. Re-run Migration
```bash
# Delete indexes and start fresh
curl -X DELETE http://localhost:9200/songs
curl -X DELETE http://localhost:9200/albums
curl -X DELETE http://localhost:9200/playlists
curl -X DELETE http://localhost:9200/users

# Re-run migration
python -m migrate_to_elasticsearch
```

---

## Issue: Search API Returns No Results

### Symptoms:
- `/search/songs?q=test` returns empty results
- But data exists in Elasticsearch

### Solutions:

#### 1. Check if FastAPI is Using Elasticsearch
```bash
# Start your FastAPI app
cd backend
poetry run uvicorn 1-mongodb-app.main:app --reload

# Check startup logs for:
# "Elasticsearch connected: 8.11.0"
```

#### 2. Test Elasticsearch Directly
```bash
# This should return results
curl -X POST http://localhost:9200/songs/_search \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match_all": {}}}'
```

#### 3. Check Field Names
```bash
# Get mapping to see field names
curl http://localhost:9200/songs/_mapping?pretty

# Verify your search query uses correct field names
```

#### 4. Test Simple Match Query
```bash
curl -X POST http://localhost:9200/songs/_search?pretty \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match": {
        "name": "test"
      }
    }
  }'
```

#### 5. Check API Endpoint
```bash
# Test with curl
curl "http://localhost:8000/search/songs?q=test"

# Should return JSON with results array
```

---

## Issue: Autocomplete Not Working

### Symptoms:
- `/search/songs/autocomplete?q=lo` returns no results
- Or returns unexpected results

### Solutions:

#### 1. Check Index Mapping
```bash
curl http://localhost:9200/songs/_mapping?pretty | grep autocomplete
```

#### 2. Reindex with Correct Mapping
```bash
# Delete and recreate index
curl -X DELETE http://localhost:9200/songs

# Run migration again (will recreate with correct mapping)
python -m migrate_to_elasticsearch
```

#### 3. Test Edge N-gram Analyzer
```bash
curl -X POST http://localhost:9200/songs/_search?pretty \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match": {
        "name.autocomplete": "lo"
      }
    }
  }'
```

---

## Issue: Slow Search Performance

### Symptoms:
- Search takes > 1 second
- Timeouts occur

### Solutions:

#### 1. Check Index Size
```bash
curl http://localhost:9200/_cat/indices?v
```

#### 2. Add More Memory to Elasticsearch
Edit `docker-compose.yml`:
```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # Increase to 1GB
```

#### 3. Optimize Index
```bash
# Force merge to reduce segments
curl -X POST http://localhost:9200/songs/_forcemerge?max_num_segments=1
```

#### 4. Use Result Size Limits
```bash
# Limit results to improve performance
curl "http://localhost:8000/search/songs?q=test&size=10"
```

---

## Issue: Data Out of Sync

### Symptoms:
- New songs in MongoDB don't appear in search
- Updated songs show old data

### Solutions:

#### 1. Understand Migration is One-Time
The migration script is a one-time data copy. Changes after migration won't automatically sync.

#### 2. Re-run Migration
```bash
# Re-run to sync latest data
python -m migrate_to_elasticsearch
```

#### 3. Implement Real-Time Sync
Add to your CRUD endpoints:

```python
# In routes/songs.py
from dependencies_elasticsearch import get_elasticsearch

@router.post("/songs")
async def create_song(song: SongCreate):
    # Insert to MongoDB
    result = await song_collection.insert_one(new_song)
    
    # ALSO index to Elasticsearch
    es = await get_elasticsearch()
    await es.index_document("songs", str(result.inserted_id), new_song)
    
    return new_song
```

#### 4. Use Change Streams (Advanced)
MongoDB Change Streams can automatically sync changes to Elasticsearch.

See: `change_logger.py` in your project

---

## Getting Help

### Check Logs
```bash
# Elasticsearch logs
docker logs es01

# FastAPI logs
# (in your terminal where uvicorn is running)

# Migration script output
python -m migrate_to_elasticsearch 2>&1 | tee migration.log
```

### Useful Commands
```bash
# Elasticsearch cluster health
curl http://localhost:9200/_cluster/health?pretty

# List all indexes
curl http://localhost:9200/_cat/indices?v

# Count documents
curl http://localhost:9200/songs/_count

# Sample documents
curl http://localhost:9200/songs/_search?size=3&pretty

# Delete index
curl -X DELETE http://localhost:9200/songs

# Check mapping
curl http://localhost:9200/songs/_mapping?pretty
```

### Reset Everything
```bash
# Nuclear option - start completely fresh
docker-compose down -v
docker-compose up -d elasticsearch
# Wait 30 seconds
python -m migrate_to_elasticsearch
```

---

## Still Having Issues?

1. Check Docker Desktop is running
2. Verify all containers are healthy: `docker-compose ps`
3. Check `.env` file has correct connection strings
4. Ensure Python 3.8+ is installed
5. Verify poetry dependencies are installed: `poetry install`
6. Check firewall isn't blocking ports 9200, 5601
7. Review logs for specific error messages

---

**Need more help?** See:
- `ELASTICSEARCH_MIGRATION.md` for detailed guide
- `ELASTICSEARCH_SETUP_SUMMARY.md` for overview
- Elasticsearch docs: https://www.elastic.co/guide/
