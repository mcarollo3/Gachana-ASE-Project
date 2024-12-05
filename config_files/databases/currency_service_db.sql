DROP DATABASE IF EXISTS CurrencyService;

CREATE DATABASE CurrencyService;
USE CurrencyService;

DROP TABLE IF EXISTS Transaction_History;

DROP TABLE IF EXISTS Wallets;

CREATE TABLE Wallets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    wallet DECIMAL(10, 2) DEFAULT 0.00
);

CREATE TABLE Transaction_History (
    id INT AUTO_INCREMENT PRIMARY KEY,
    wallet_id INT NOT NULL,
    user_id INT NOT NULL,
    old_wallet DECIMAL(10, 2) DEFAULT 0.00,
    new_wallet DECIMAL(10, 2) DEFAULT 0.00,
    description TEXT,
    date DATETIME NOT NULL,
	FOREIGN KEY (wallet_id) REFERENCES Wallets(id) ON DELETE CASCADE
);

INSERT INTO Wallets (user_id, wallet)
VALUES (2, 3000000.00);
