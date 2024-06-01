
FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y ffmpeg

WORKDIR /app

COPY discordbot_test.py .

COPY ytapi.py .

COPY requirements.txt .

RUN pip install -r requirements.txt

ENV PATH="/usr/local/bin:${PATH}"

CMD ["python", "discordbot_test.py"]

