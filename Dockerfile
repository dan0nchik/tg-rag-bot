FROM python:3.11-slim

WORKDIR /app

# uv — в 10-100x быстрее pip для resolve и install
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Torch CPU-only отдельным слоем
COPY requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --index-url https://download.pytorch.org/whl/cpu torch && \
    uv pip install --system -r requirements.txt

COPY ./app /app

CMD ["python", "bot.py"]
