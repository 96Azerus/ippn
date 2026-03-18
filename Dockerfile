FROM python:3.10-slim

WORKDIR /app

# Установка компилятора и curl для скачивания эфемерид
RUN apt-get update && apt-get install -y gcc curl && rm -rf /var/lib/apt/lists/*

# Скачивание точных швейцарских эфемерид (планеты и Луна для 1800-2399 гг.)
RUN mkdir -p /app/ephe && \
    curl -Lo /app/ephe/sepl_18.se1 https://www.astro.com/swisseph/ephe/sepl_18.se1 && \
    curl -Lo /app/ephe/semo_18.se1 https://www.astro.com/swisseph/ephe/semo_18.se1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
