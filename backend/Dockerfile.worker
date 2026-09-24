FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    VECTOR_BACKEND=qdrant \
    RERANK_ENABLED=false \
    PIPELINE_EVENTS_TO_API=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.worker.txt .
RUN pip install --no-cache-dir -r requirements.worker.txt

COPY livekit_agent/ ./livekit_agent/
COPY qdrant/ ./qdrant/
COPY utils/ ./utils/
COPY medical_rag/ ./medical_rag/

# Prefetch LiveKit plugin assets when the CLI supports it
RUN python -m livekit_agent.agent download-files || true

CMD ["python", "-m", "livekit_agent.agent", "start"]
