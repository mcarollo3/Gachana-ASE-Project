FROM python:3.12-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file dell'applicazione nel container
COPY ./backend/user_service .

# Copia i file secrets necessari
COPY ./secrets/db/db_user.txt /run/secrets/db_user
COPY ./secrets/db/db_password.txt /run/secrets/db_password
COPY ./secrets/jwt_secrets.txt /run/secrets/jwt_secret
COPY ./secrets/https/user/key.pem /run/secrets/https_user_key
COPY ./secrets/https/user/cert.pem /run/secrets/https_user_cert
COPY ./secrets/cryptography/key.txt /run/secrets/cryptography_key
COPY ./backend/utils .


ENV DB_HOST=user_db
ENV DB_NAME=UserService
ENV DB_USER=/run/secrets/db_user
ENV DB_PASSWORD=/run/secrets/db_password
ENV SECRET_KEY=/run/secrets/jwt_secret

# Installa le dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta dell'applicazione
EXPOSE 5000

# Comando di avvio, utilizzando i certificati e il servizio Flask
CMD ["flask", "--app", "user_api", "run", "--host=0.0.0.0", "--port=5000", "--cert=/run/secrets/https_user_cert", "--key=/run/secrets/https_user_key"]

# docker build -t user_service_test  -f backend/user_service/Dockerfile .    dalla root del progetto
# docker run --name user_service_test_container -p 5000:5000 user_service_test