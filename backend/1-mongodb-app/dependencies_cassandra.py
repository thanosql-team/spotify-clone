import os

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime

CASSANDRA_KEYSPACE = "spotify_clone"

def get_cassandra_session():
    cluster = Cluster([os.getenv("CASSANDRA_HOST", "127.0.0.1")])
    session = cluster.connect()
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
    """)
    session.set_keyspace(CASSANDRA_KEYSPACE)

    # Ensure tables exist
    session.execute("""
        CREATE TABLE IF NOT EXISTS album_change_log (
            album_id TEXT,
            change_time TIMESTAMP,
            user_id TEXT,
            action TEXT,
            old_data TEXT,
            new_data TEXT,
            PRIMARY KEY (album_id, change_time)
        ) WITH CLUSTERING ORDER BY (change_time DESC);
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS playlist_change_log (
            playlist_id TEXT,
            change_time TIMESTAMP,
            user_id TEXT,
            action TEXT,
            old_data TEXT,
            new_data TEXT,
            PRIMARY KEY (playlist_id, change_time)
        ) WITH CLUSTERING ORDER BY (change_time DESC);
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS entity_changes_by_user (
            user_id TEXT,
            change_time TIMESTAMP,
            entity_type TEXT,
            entity_id TEXT,
            action TEXT,
            PRIMARY KEY (user_id, change_time)
        ) WITH CLUSTERING ORDER BY (change_time DESC);
    """)
    session.execute("""
        CREATE TABLE IF NOT EXISTS entity_changes_all (
            entity_type TEXT,
            change_time TIMESTAMP,
            user_id TEXT,
            entity_id TEXT,
            action TEXT,
            PRIMARY KEY (entity_type, change_time)
        ) WITH CLUSTERING ORDER BY (change_time DESC);
    """)

    return session

session = get_cassandra_session()
