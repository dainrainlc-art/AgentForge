FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agentforge ./agentforge
COPY integrations ./integrations
COPY run.py .

RUN mkdir -p logs data

EXPOSE 8000

CMD ["python", "run.py"]
