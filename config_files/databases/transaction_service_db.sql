DROP DATABASE IF EXISTS TransactionService;

CREATE DATABASE TransactionService;
USE TransactionService;

DROP TABLE IF EXISTS Transaction_History;

CREATE TABLE Transaction_History (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_seller_id INT NOT NULL,
    user_buyer_id INT NOT NULL,
    gacha_value DECIMAL(10, 2) NOT NULL,
    id_gacha INT NOT NULL,
    date DATETIME NOT NULL
);

