# Data Import Guide

This document explains how to update restaurant and review data in the FoodMaps database.

> **Important:** Do not commit raw CSV files containing collected or internal form data. Files under `data/raw/` are ignored by Git.

---

## 1. Prerequisites

Make sure Docker is running and the FoodMaps database is available.

From the project root:

```bash
make db
```

---

## 2. Import Restaurant Data

Restaurant data is stored locally as:

```text
data/raw/places.csv
```

Run the Places import script from the `backend/` directory:

```bash
cd backend
uv run python scripts/import_places.py ../data/raw/places.csv
```

After importing, verify that the expected restaurant records are present in the database.

---

## 3. Import Review Data

Review data comes from the team's internal Google Form.

### 3.1 Export the Google Form responses

Export the latest Google Form responses as a CSV file and save it to:

```text
data/raw/reviews.csv
```

The file is ignored by Git and should not be committed.

### 3.2 Preview the import

Before modifying the database, run the importer in dry-run mode:

```bash
cd backend
uv run python scripts/import_reviews.py ../data/raw/reviews.csv --dry-run
```

Check the output for invalid rows, missing places, duplicate reviews, or other import errors.

### 3.3 Replace the existing sheet reviews

If the dry-run output is clean, remove the reviews previously imported from the Google Form:

```bash
docker compose exec db psql -U foodmaps -d foodmaps -c "DELETE FROM reviews WHERE source = 'sheet';"
```

This only removes reviews with:

```text
source = 'sheet'
```

User-submitted reviews with:

```text
source = 'user'
```

are not affected.

### 3.4 Run the actual import

Run the importer again without `--dry-run`:

```bash
uv run python scripts/import_reviews.py ../data/raw/reviews.csv
```

The import can be run again whenever the Google Form data is updated.

---

## 4. Recommended Update Flow

When new restaurant or review data is available:

```text
Update source data
      │
      ├── places.csv
      │       ↓
      │   Import Places
      │
      └── reviews.csv
              ↓
          Run --dry-run
              ↓
          Check output
              ↓
          Delete old sheet reviews
              ↓
          Run actual import
```

For reviews, always run the `--dry-run` version before the real import.

---

## 5. Important Notes

- `data/raw/places.csv` and `data/raw/reviews.csv` are local data files and should not be committed to Git.
- Use the provided import scripts instead of manually inserting data into PostgreSQL.
- For reviews, only records with `source = 'sheet'` are replaced during a Google Form refresh.
- User-submitted reviews (`source = 'user'`) must not be deleted during the sheet import process.
- If the import script reports errors during `--dry-run`, fix the source data or importer before running the real import.