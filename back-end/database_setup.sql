-- Updated database schema (removed weight_kg, category, source)
CREATE DATABASE IF NOT EXISTS stunting_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE stunting_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create predictions table (updated - removed weight_kg, category, source)
CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    child_name VARCHAR(100) NOT NULL,
    age_months INT NOT NULL,
    height_cm FLOAT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    algorithm VARCHAR(10) NOT NULL,
    prediction_code INT NOT NULL,
    prediction_status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_prediction_user ON predictions(user_id);
CREATE INDEX idx_prediction_created ON predictions(created_at);

-- Insert sample admin user (password: admin123)
INSERT INTO users (name, email, password_hash, role) VALUES 
('Administrator', 'admin@stunting.com', 'pbkdf2:sha256:600000$salt$hash', 'admin')
ON DUPLICATE KEY UPDATE name=name;
