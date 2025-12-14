# Elasticsearch Guide

### Re-run Migration
```bash
# Run from backend/ directory
cd backend
uv run python -m app.scripts.migrate_to_elasticsearch
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
curl http://localhost:9200/songs/_search?pretty=true

# Delete index
curl -X DELETE http://localhost:9200/songs

# Check mapping
curl http://localhost:9200/songs/_mapping?pretty=true
```

### Reset Everything
```bash
# Nuclear option - start completely fresh
docker-compose down -v
docker-compose up -d elasticsearch
cd backend
uv run python -m app.scripts.migrate_to_elasticsearch
```

- Elasticsearch docs: https://www.elastic.co/guide/
