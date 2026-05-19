CREATE DATABASE rfid_db;

USE rfid_db;

CREATE TABLE access_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(50),
    status VARCHAR(20),
    timestamp DATETIME
);
