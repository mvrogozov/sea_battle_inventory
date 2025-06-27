FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /application
COPY requirements/requirements.txt .
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt
COPY app/ ./app
RUN mkdir ./app/logs
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "app.main:app"]