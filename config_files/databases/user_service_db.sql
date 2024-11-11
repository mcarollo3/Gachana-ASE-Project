DROP DATABASE IF EXISTS UserService;

CREATE DATABASE UserService;
USE UserService;

DROP TABLE IF EXISTS UserData;

CREATE TABLE UserData (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    psw VARCHAR(100) NOT NULL,
    id_image INT,
    wallet DECIMAL(10, 2) DEFAULT 0.00
);

INSERT INTO UserData (username, psw, role)
VALUES ('admin', 'gachana', 'admin');
