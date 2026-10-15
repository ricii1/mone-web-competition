FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# Install CPU-only PyTorch first so sentence-transformers doesn't pull the
# much larger CUDA build (we only ever run embeddings on CPU, see AGENTS.md).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
ARG INSTALL_DEV=true
RUN if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir -e ".[dev]"; \
    else pip install --no-cache-dir -e .; fi

COPY . .
RUN useradd --create-home --uid 10001 app && \
    mkdir -p /data/uploads /home/app/.cache/huggingface && \
    chown -R app:app /data/uploads /home/app/.cache /app
ARG APP_USER=root
USER $APP_USER

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
