# Używamy oficjalnego obrazu Pythona
FROM python:3.9-slim

# Instalujemy ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg

# Ustawiamy katalog roboczy na /app
WORKDIR /app

# Kopiujemy plik discordbot_test.py do katalogu /app w obrazie
COPY discordbot_test.py .

COPY ytapi.py .
# Kopiujemy plik requirements.txt do katalogu /app w obrazie
COPY requirements.txt .

# Instalujemy zależności Pythona z pliku requirements.txt
RUN pip install -r requirements.txt

# Dodajemy ścieżkę do ffmpeg do zmiennej PATH
ENV PATH="/usr/local/bin:${PATH}"

# Domyślnie uruchamiamy nasz skrypt po uruchomieniu kontenera
CMD ["python", "discordbot_test.py"]

