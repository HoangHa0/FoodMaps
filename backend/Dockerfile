# FoodMaps API image, built and run by a Hugging Face Space (Docker SDK). See docs/DEPLOY.md.
#
# - torch comes from the CPU-only index: the default (CUDA) build adds ~3 GB of nvidia packages a CPU
#   host never uses. The other dependencies are the exact versions of uv.lock (exported below).
# - The embedding model is downloaded at build time, so a cold start does not wait for the Hub and
#   the container runs offline (HF_HUB_OFFLINE=1).
# - Hugging Face runs the container as user 1000 and sends traffic to port 7860.
# - Start: apply migrations (idempotent), then one uvicorn worker (one copy of the model in RAM).
#
# Local test (from backend/):
#   docker build -t foodmaps-api .
#   docker run --rm -p 7860:7860 --env-file .env foodmaps-api

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/hf-cache

WORKDIR /app

# --- dependencies (layer cached until pyproject.toml / uv.lock change) ---------------------------
COPY pyproject.toml uv.lock ./
RUN pip install uv \
 && uv export --frozen --no-dev --extra ai --no-hashes --no-emit-project --format requirements-txt \
      | grep -v -E '^(torch|triton|nvidia-)' > /tmp/requirements.txt \
 && TORCH_VERSION=$(grep -A1 '^name = "torch"$' uv.lock | sed -n 's/^version = "\(.*\)"$/\1/p') \
 && uv pip install --system --index-url https://download.pytorch.org/whl/cpu "torch==${TORCH_VERSION}" \
 && uv pip install --system -r /tmp/requirements.txt \
 && pip uninstall -y uv && rm /tmp/requirements.txt

# --- embedding model, baked into the image ---------------------------------------------------------
# Must match app/modules/match/embedding.py (EMBED_MODEL, default below). Change both together.
ARG EMBED_MODEL=intfloat/multilingual-e5-small
ENV EMBED_MODEL=${EMBED_MODEL}
RUN python -c "import os; from sentence_transformers import SentenceTransformer; SentenceTransformer(os.environ['EMBED_MODEL'])" \
 && chmod -R a+rX "$HF_HOME"
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# --- application -----------------------------------------------------------------------------------
RUN useradd --create-home --uid 1000 user
COPY --chown=user alembic.ini ./
COPY --chown=user migrations ./migrations
COPY --chown=user app ./app
USER user

ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
