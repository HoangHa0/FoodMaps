FROM postgis/postgis:16-3.5
# Base image is Debian 11, which apt.postgresql.org no longer serves: fall back to the archive mirror.
RUN (apt-get update || (sed -i 's|apt.postgresql.org|apt-archive.postgresql.org|g' /etc/apt/sources.list.d/pgdg.* && apt-get update)) \
  && apt-get install -y --no-install-recommends postgresql-16-pgvector \
  && rm -rf /var/lib/apt/lists/*
COPY init.sql /docker-entrypoint-initdb.d/10-init.sql
