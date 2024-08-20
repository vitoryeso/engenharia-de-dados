-- Criação da tabela sensor_data
CREATE TABLE IF NOT EXISTS sensor_data (
    id SERIAL PRIMARY KEY,
    sensor_type VARCHAR(50),
    measurement FLOAT,
    timestamp TIMESTAMP
);

