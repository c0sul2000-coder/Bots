FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY bot_db/ ./bot_db/

# Папка для SQLite базы данных (монтируется как Volume в Railway)
RUN mkdir -p /app/data
ENV DB_PATH=/app/data/bot_data.db

CMD ["python", "bot_db/main.py"]
