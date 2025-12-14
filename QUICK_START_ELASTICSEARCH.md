# 🚀 Quick Start: MongoDB → Elasticsearch Migration

## One-Command Migration

```bash
cd backend/1-mongodb-app
./migrate.sh
```

That's it! The script will:
- ✅ Check Elasticsearch status
- ✅ Start container if needed
- ✅ Migrate all data
- ✅ Verify success

## What Gets Migrated

| MongoDB Collection | Elasticsearch Index | Documents |
|-------------------|---------------------|-----------|
| songs             | songs               | All       |
| albums            | albums              | All       |
| playlists         | playlists           | All       |
| users             | users               | All       |

## Test the Search API

### Basic Search
```bash
curl "http://localhost:8000/search/songs?q=love&size=10"
```

### Autocomplete
```bash
curl "http://localhost:8000/search/songs/autocomplete?q=lo"
```

### By Genre
```bash
curl "http://localhost:8000/search/songs/by-genre?genre=Rock"
```

### Search Everything
```bash
curl "http://localhost:8000/search/all?q=music"
```

## API Documentation

Open in browser: **http://localhost:8000/docs**

Look for the **"search"** tag with 4 new endpoints.

## Kibana Dashboard

Open in browser: **http://localhost:5601**

Navigate to: **Dev Tools** → Run queries:

```
GET songs/_count
GET songs/_search
```

## Verify Migration

```bash
# Check Elasticsearch is running
curl http://localhost:9200

# Count documents per index
curl http://localhost:9200/songs/_count
curl http://localhost:9200/albums/_count
curl http://localhost:9200/playlists/_count
curl http://localhost:9200/users/_count
```

## Common Issues

### ❌ Elasticsearch not running
```bash
docker-compose up -d elasticsearch
# Wait 30 seconds for startup
```

### ❌ Connection refused
Check your `.env` file has:
```env
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

### ❌ No data migrated
Verify MongoDB has data:
```python
python3 -c "from dependencies import db; import asyncio; print(asyncio.run(db['songs'].count_documents({})))"
```

### ❌ Re-run migration
```bash
# Delete all Elasticsearch data
curl -X DELETE http://localhost:9200/_all

# Re-run
./migrate.sh
```

## Project Structure

```
backend/1-mongodb-app/
├── migrate_to_elasticsearch.py  ← Migration script
├── migrate.sh                    ← Easy migration runner
├── ELASTICSEARCH_MIGRATION.md    ← Full documentation
├── routes/
│   └── search.py                 ← New search endpoints
├── dependencies_elasticsearch.py ← ES connection manager
└── main.py                       ← Updated with ES init
```

## Next Steps

1. ✅ Run migration: `./migrate.sh`
2. 🧪 Test endpoints: http://localhost:8000/docs
3. 📊 View in Kibana: http://localhost:5601
4. 💻 Integrate with frontend
5. 🔄 Add real-time sync (optional)

---

📖 **Full Guide**: See `ELASTICSEARCH_MIGRATION.md`  
📋 **Summary**: See `ELASTICSEARCH_SETUP_SUMMARY.md` in project root
