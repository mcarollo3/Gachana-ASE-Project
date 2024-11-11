# Usa un'immagine base di Python
FROM python:3.9-slim

# Imposta la cartella di lavoro
WORKDIR /app

# Copia i file del progetto nella cartella di lavoro
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta su cui Flask girerà
EXPOSE 5000

# Comando per avviare l'app
CMD ["python", "user_api.py"]