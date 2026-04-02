FROM python:3.11-slim

WORKDIR /app

# Сначала ставим torch CPU-only (намного легче чем полный ~2GB → ~200MB)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch --index-url https://download.pytorch.org/whl/cpu

# Зависимости отдельным слоем — кэшируется пока requirements.txt не меняется
COPY requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Код копируем последним — меняется чаще всего
COPY ./app /app

CMD ["python", "bot.py"]
