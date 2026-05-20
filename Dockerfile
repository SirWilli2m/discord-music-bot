FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY bot/ bot/
COPY run.py .
COPY cookies.txt* .

RUN pip install --no-cache-dir .

CMD ["python", "run.py"]
