import psycopg2

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    user='postgres',
    password='2205802',
    dbname='postgres'
)
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT 1 FROM pg_database WHERE datname = 'ai_saas_db'")
if not cur.fetchone():
    cur.execute("CREATE DATABASE ai_saas_db")
    print("DATABASE_CREATED: ai_saas_db")
else:
    print("DATABASE_EXISTS: ai_saas_db")
cur.close()
conn.close()

conn2 = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    user='postgres',
    password='2205802',
    dbname='ai_saas_db'
)
conn2.autocommit = True
cur2 = conn2.cursor()
try:
    cur2.execute("CREATE EXTENSION IF NOT EXISTS vector")
    print("PGVECTOR_EXTENSION_ENABLED")
except Exception as e:
    print("PGVECTOR_ERROR:", e)
cur2.close()
conn2.close()
