# Spotify Clone 🎵

A full-stack Spotify-like application built with modern NoSQL databases for a university NoSQL course project. This application demonstrates the use of multiple database technologies including MongoDB, Redis, Cassandra, Neo4j, and Elasticsearch.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.13+ (for local development)
- UV package manager (recommended for Python)

### Environment Setup

Create a `.env` file in the root directory:

```env
MONGODB_URL=your_mongodb_connection_string
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

### Running with Docker Compose

Start all services:

```bash
docker-compose up -d
```

This will start the following services:

| Service | Port(s) | URL/Access |
|---------|---------|------------|
| **FastAPI Backend** | 8000 | `http://localhost:8000` |
| **Elasticsearch** | 9200 | `http://localhost:9200` |
| **Kibana** | 5601 | `http://localhost:5601` |
| **Redis** | 6379 | `localhost:6379` |
| **Cassandra** | 9042 | `localhost:9042` |
| **Neo4j Browser** | 7474 | `http://localhost:7474` |
| **Neo4j Bolt** | 7687 | `bolt://localhost:7687` |

### Initial Setup

After starting the services, migrate data to Elasticsearch:

```bash
cd backend
uv run python -m app.scripts.migrate_to_elasticsearch
```

### Access the API

Once running, visit:
- **API Documentation (Swagger)**: `http://localhost:8000/docs`
- **Alternative Docs (ReDoc)**: `http://localhost:8000/redoc`
- **Neo4j Browser**: `http://localhost:7474` (user: `neo4j`, password: `password123`)
- **Kibana Dashboard**: `http://localhost:5601`

## 🏗️ Architecture

### Backend
- **Framework**: FastAPI (Python 3.13)
- **API**: RESTful API with automatic OpenAPI documentation

### Databases
- **MongoDB**: Primary database for storing users, songs, albums, and playlists
- **Redis**: Caching layer for improved performance
- **Cassandra**: Distributed storage for change logs and time-series data
- **Neo4j**: Graph database for relationships and recommendations
- **Elasticsearch**: Full-text search engine for songs, albums, playlists, and users

## ✨ Features

### Core Functionality
- **Users**: Create, retrieve, update, and delete user profiles
- **Songs**: Complete CRUD operations for song management
- **Albums**: Album management with song associations
- **Playlists**: Create and manage custom playlists

### Advanced Features
- **Full-Text Search**: Fast search across songs, albums, playlists, and users using Elasticsearch
- **Graph Recommendations**: 
  - Playlist-based recommendations using collaborative filtering
  - Deep recommendations based on user listening patterns
- **Change Logs**: Track all database changes with Cassandra
- **Caching**: Automatic caching with Redis for frequently accessed data
- **Real-time Sync**: Synchronize data between MongoDB and Neo4j for graph operations

## 📚 API Documentation

Once the backend is running, visit:
- **Interactive API Docs (Swagger)**: `http://localhost:8000/docs`
- **Alternative API Docs (ReDoc)**: `http://localhost:8000/redoc`

### Main Endpoints

#### Songs
- `POST /songs` - Create a new song
- `GET /songs` - List all songs
- `GET /songs/{id}` - Get a specific song
- `GET /songs/album/{album_id}` - Get songs by album
- `PUT /songs/{id}` - Update a song
- `DELETE /songs/{id}` - Delete a song

#### Playlists
- `POST /playlists` - Create a new playlist
- `GET /playlists` - List all playlists
- `GET /playlists/{id}` - Get a specific playlist
- `PUT /playlists/{id}` - Update a playlist
- `DELETE /playlists/{id}` - Delete a playlist

#### Users
- `POST /users` - Create a new user
- `GET /users` - List all users
- `GET /users/{id}` - Get a specific user

#### Albums
- `POST /albums` - Create a new album
- `GET /albums` - List all albums
- `GET /albums/{id}` - Get a specific album

#### Search
- `GET /search?q={query}&type={type}` - Search across songs, albums, playlists, and users
  - Types: `song`, `album`, `playlist`, `user`, or `all`

#### Graph/Recommendations
- `GET /graph/recommendations/playlist/{playlist_id}` - Get recommendations based on a playlist
- `GET /graph/recommendations/deep/{user_id}` - Get deep recommendations for a user
- `POST /graph/sync-playlist/{playlist_id}` - Sync a playlist to Neo4j
- `POST /graph/sync-all-playlists` - Sync all playlists to Neo4j
- `POST /graph/sync-from-mongodb` - Sync all data from MongoDB to Neo4j
- `GET /graph/overview` - Get graph database statistics

#### Change Logs
- `GET /change-logs` - List all change logs
- `GET /change-logs/entity/{entity_type}` - Get changes for a specific entity type

## 🗄️ Database Schemas

### MongoDB Collections
- **users**: User profiles and metadata
- **songs**: Song information (title, artist, album, duration, etc.)
- **albums**: Album details and track listings
- **playlists**: User playlists with song references

### Cassandra Keyspace
- **spotify_logs**: Change log entries with timestamps

### Neo4j Graph
- **Nodes**: User, Song, Playlist, Album, Artist, Genre
- **Relationships**: CREATED, CONTAINS, LISTENED_TO, BELONGS_TO

### Elasticsearch Indices
- **songs**: Full-text searchable song data
- **albums**: Album search index
- **playlists**: Playlist search index
- **users**: User search index

## 🛠️ Development Tools

### Elasticsearch Management

Check cluster health:
```bash
curl http://localhost:9200/_cluster/health?pretty
```

List all indices:
```bash
curl http://localhost:9200/_cat/indices?v
```

View Kibana dashboard:
```
http://localhost:5601
```

### Neo4j Browser

Access Neo4j browser interface:
```
http://localhost:7474
```

Default credentials:
- Username: `neo4j`
- Password: `password123`

### Reset Everything

To start fresh with clean databases:
```bash
docker-compose down -v
docker-compose up -d
```

## 📦 Dependencies

### Backend
- FastAPI - Modern web framework
- Motor - Async MongoDB driver
- PyMongo - MongoDB Python driver
- Redis - Python Redis client
- cassandra-driver - Cassandra Python driver
- neo4j - Neo4j Python driver
- elasticsearch[async] - Elasticsearch Python client
- pydantic-settings - Settings management

## 🎯 Project Structure

```
spotify-clone/
├── backend/
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── core/            # Dependencies & config
│   │   ├── scripts/         # Utility scripts
│   │   └── main.py          # FastAPI application
│   ├── Dockerfile
│   └── pyproject.toml
├── schemes/                 # Database schema documentation
├── docker-compose.yml
└── README.md
```

## 🧪 Testing

The application includes health checks for all services:
- Backend: `http://localhost:8000/`
- Elasticsearch: `http://localhost:9200/_cluster/health`
- Redis: `redis-cli ping`
- Neo4j: Browser health check
- Cassandra: `cqlsh -e 'describe keyspaces'`

## 📝 License

This is a university course project.

## 👥 Contributors

NoSQL Course Group Project - 2025
