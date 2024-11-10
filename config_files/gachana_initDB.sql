DROP DATABASE IF EXISTS Gachana_DB;

CREATE DATABASE Gachana_DB;
USE Gachana_DB;

DROP TABLE IF EXISTS Transaction_History;
DROP TABLE IF EXISTS Offers;
DROP TABLE IF EXISTS Market;
DROP TABLE IF EXISTS Collection;
DROP TABLE IF EXISTS Gacha;
DROP TABLE IF EXISTS User;

CREATE TABLE User (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    psw VARCHAR(100) NOT NULL,
    id_image INT,
    wallet DECIMAL(10, 2) DEFAULT 0.00
);


CREATE TABLE Gacha (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    id_img INT,
    rarity ENUM('Common','Uncommon', 'Rare', 'Super Rare', 'Legendary') NOT NULL
);


CREATE TABLE Collection (
    user_id INT,
    gacha_id INT,
    quantity INT DEFAULT 1,
    PRIMARY KEY (user_id, gacha_id),
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (gacha_id) REFERENCES Gacha(id) ON DELETE CASCADE
);


CREATE TABLE Market (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gacha_id INT NOT NULL,
    user_id INT NOT NULL,
    value_last_offer DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    FOREIGN KEY (gacha_id) REFERENCES Gacha(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);


CREATE TABLE Offers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    market_id INT NOT NULL,
    user_id INT NOT NULL,
    offer_value DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (market_id) REFERENCES Market(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);


CREATE TABLE Transaction_History (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_seller_id INT NOT NULL,
    user_buyer_id INT NOT NULL,
    gacha_value DECIMAL(10, 2) NOT NULL,
    id_gacha INT NOT NULL,
    date DATETIME NOT NULL,
    FOREIGN KEY (user_seller_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (user_buyer_id) REFERENCES User(id) ON DELETE CASCADE,
    FOREIGN KEY (id_gacha) REFERENCES Gacha(id) ON DELETE CASCADE
);
