# Gachana Microservices Application

## Overview

This is a microservices-based application designed to manage gacha systems. The architecture includes four core microservices:

- **UserService**: Handles user-related operations.
- **GachaService**: Manages gacha draws and items.
- **MarketService**: Supports marketplace operations.
- **CurrencyService**: Manages virtual currencies.

Each microservice is associated with a dedicated database, and all services communicate internally over HTTPS using certificates. The application employs two API gateways managed by **NGINX**:

- **Admin Gateway**: For administrative operations.
- **Player Gateway**: For player-facing interactions.

## Architecture

### API Gateways

- **Admin Gateway**: Handles requests for administrative tasks.

  - Example Routes:
    - `https://localhost:443/admin/user` → UserService
    - `https://localhost:443/admin/gacha` → GachaService
    - `https://localhost:443/admin/currency` → CurrencyService
    - `https://localhost:443/admin/market` → MarketService

- **Player Gateway**: Handles requests for player interactions.
  - Example Routes:
    - `https://localhost:444/player/user` → UserService
    - `https://localhost:444/player/gacha` → GachaService
    - `https://localhost:444/player/currency` → CurrencyService
    - `https://localhost:444/player/market` → MarketService

### Databases

Each service has a dedicated MySQL database:

- **user_db**
- **gacha_db**
- **market_db**
- **currency_db**

### Security

- All internal communication between microservices is encrypted using HTTPS and relies on service-specific certificates.
- Sensitive information such as database credentials, JWT secrets, and certificates are securely managed using Docker Secrets.

## Requirements

- **Docker** and **Docker Compose** installed on the host machine.

## Setup and Deployment

### Steps to Run

1. Clone the repository.
2. Ensure Docker and Docker Compose are installed.
3. Build and run the application:
   ```bash
   docker-compose up --build
   ```
4. The application will be accessible via the following endpoints:
   - Admin Gateway: `https://localhost:443`
   - Player Gateway: `https://localhost:444`
5. After all containers have started, wait about ten seconds before starting testing
6. If you receive a 502 Bad Gateway response restart Api Gateways containers

### Docker Compose Details

The application uses the following Docker Compose services:

- **Databases**: MySQL instances for each microservice, preconfigured with their schemas.
- **Microservices**: Individual containers for UserService, GachaService, MarketService, and CurrencyService.
- **API Gateways**: Two NGINX-based gateways for routing requests.

### Configuration

The NGINX configuration files (`default_admin.conf` and `default_player.conf`) define routes to forward requests to the appropriate services.

Example NGINX configuration for Admin UserService Gateway:

```nginx
location /admin/user/ {
    proxy_pass https://user_service:5000/;
    proxy_ssl_verify off;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Secrets Management

- Secrets such as passwords, certificates, and private keys are stored in the `secrets/` directory and managed using Docker Secrets.
- Example:
  - `db_root_password`: Stored in `secrets/db/db_root_password.txt`
  - `jwt_secret`: Stored in `secrets/jwt_secrets.txt`

## Testing the Application

### Postman Collection

To test the application, use the Postman collection located in the `docs/postman` folder. This folder contains:

- Collections for testing the entire application.
- Collections for testing individual microservices in isolation (`docs/postman/unit-test`).

Additionally, the folder includes `env.postman` files with variables used in Postman to simplify testing.

**Note:** If the `current value` field remains empty during the import of `env.postman` files in Postman, you must manually copy the `initial value` into the `current value` field.

### Authentication for Microservices

When testing microservices in isolation, an authentication token is required for API calls. Each collection includes a login endpoint, which should be executed first to obtain the token. This ensures smooth execution of both positive and negative tests for all endpoints.
