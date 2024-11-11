DROP DATABASE IF EXISTS MarketService;

CREATE DATABASE MarketService;
USE MarketService;

DROP TABLE IF EXISTS Offers;
DROP TABLE IF EXISTS Market;

CREATE TABLE Market (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gacha_id INT NOT NULL,
    user_id INT NOT NULL,
    value_last_offer DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE
);


CREATE TABLE Offers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market_id INT NOT NULL,
    user_id INT NOT NULL,
    offer_value DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (market_id) REFERENCES Market(id) ON DELETE CASCADE
);
