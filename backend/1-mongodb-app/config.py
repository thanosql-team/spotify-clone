from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Use top level .env file (one level above ./backend/) to add one-liner:
    # MONGODB_URL="yourconnectionstring"
    # REDIS_URL="redis://localhost:6379/0"
    # NEO4J_URI="bolt://localhost:7687"
    # NEO4J_USER="neo4j"
    # NEO4J_PASSWORD="password"
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")
    mongodb_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    
    # Neo4j configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # Elasticsearch configuration
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_user: str = ""
    elasticsearch_password: str = ""
    
    db_name: str = "spotify-clone"
    
    # Cache TTL time (SECS)
    cache_ttl_aggregation: int = 600
    cache_ttl_list: int = 300
    cache_ttl_single: int = 1800