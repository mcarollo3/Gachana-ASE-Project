DROP DATABASE IF EXISTS UserService;

CREATE DATABASE UserService;
USE UserService;

DROP TABLE IF EXISTS UserData;

CREATE TABLE UserData (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    role ENUM('Admin','Player') NOT NULL,
    psw VARCHAR(100) NOT NULL,
    id_image INT
);


CREATE TABLE TokenBlacklist (
    token VARCHAR(512) PRIMARY KEY,
    blacklisted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


