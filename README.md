Here is your updated README with the added information about the Postman collection:

---

# Gachana Microservices Application

This project is a microservices-based application hosted on Docker, consisting of several services including UserService, GachaService, MarketService, and CurrencyService. All services are connected via Docker Compose, and they are routed through an Nginx API Gateway.

## Prerequisites

- Docker
- Docker Compose
- .env file for storing sensitive data

## Setup Instructions

### 1. Create the `.env` File

Before starting the application, you need to create a `.env` file at the root level of the project (same level as the `docker-compose.yml`). This file will store sensitive information, such as your JWT secret key.

- **SECRET_KEY**: This key is used for signing and verifying JWT tokens.

Generate a secret key by visiting [https://jwtsecret.com/generate](https://jwtsecret.com/generate) and selecting a 64-character key. Then, add the following to your `.env` file:

```env
SECRET_KEY=your_generated_secret_key
```

### 2. Start the Application

Once the `.env` file is created and properly configured, use Docker Compose to bring up the services in detached mode.

```bash
docker-compose up -d
```

This will start all the microservices and the Nginx API Gateway. The services will be connected through a common network (`api_network`), and each service will be accessible via the API Gateway.

### 3. API Gateway Configuration

The API Gateway (Nginx) is configured to route requests to the appropriate microservices. The following locations are set up:

- **UserService**: `http://localhost/user/` (Proxy to user service)
- **GachaService**: `http://localhost/gacha/` (Proxy to gacha service)
- **CurrencyService**: `http://localhost/currency/` (Proxy to currency service)
- **MarketService**: `http://localhost/market/` (Proxy to market service)

### 4. Service Endpoints

The API Gateway will forward requests to the corresponding service based on the URL path. Here's the mapping:

- **User Service**: `http://localhost/user/`  
  (Access the User Service's endpoints like `/user/signup`, `/user/login`, etc.)

- **Gacha Service**: `http://localhost/gacha/`  
  (Access the Gacha Service's endpoints like `/gacha/collection`, etc.)

- **Currency Service**: `http://localhost/currency/`  
  (Access the Currency Service's endpoints like `/currency/wallet`, etc.)

- **Market Service**: `http://localhost/market/`  
  (Access the Market Service's endpoints like `/market/list`, etc.)

### 5. Postman Collection

A Postman collection containing all the API requests for the application can be found inside the `docs` directory of the project. This collection includes environment variables set in the `.env` file, allowing you to easily test the endpoints in the Postman app.

To get started with the collection:

1. Download the Postman collection from `docs/Postman_Collection.json`.
2. Import the collection into your Postman app.

This collection will provide you with all the necessary API calls for interacting with the microservices.
