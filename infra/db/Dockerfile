# PostgreSQL 16 + PostGIS (geospatial queries) + pgvector (embeddings), matching what Supabase offers.
FROM postgis/postgis:16-3.5
RUN apt-get update \
 && apt-get install -y --no-install-recommends postgresql-16-pgvector \
 && rm -rf /var/lib/apt/lists/*
COPY init.sql /docker-entrypoint-initdb.d/10-init.sql
