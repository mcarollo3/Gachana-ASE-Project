# Gachana-ASE-Project

- Create a .venv
- aggiungere timeout alle chiamate dell'api gateway per i servizi per gestire WobbleServiceInteraction

  # Timeout per la connessione al backend (microservizio)

        proxy_connect_timeout 10s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;

        # Gestione degli errori
        error_page 502 504 /custom_502_504.html;  # Personalizza le pagine di errore per 502 e 504
        location = /custom_502_504.html {
            internal;
            root /usr/share/nginx/html;
            # Puoi anche restituire una risposta JSON personalizzata
            add_header Content-Type application/json;
            return 504 '{"error": "Gateway Timeout. The service took too long to respond."}';
        }

  fare la gestione anche tramite api.

da aggiungere al default

    location /market/ {
        proxy_pass http://market_service:5002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /transaction/ {
        proxy_pass http://transaction_service:5003/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

per usare l'apiGateway le chiamate devono essere:

http://localhost/nomeServizio/endpoint :)

creare un file .env (stesso livello del compose) ed inserire una
SECRET_KEY=la_tua_chiave_segreta

usa https://jwtsecret.com/generate con 64
