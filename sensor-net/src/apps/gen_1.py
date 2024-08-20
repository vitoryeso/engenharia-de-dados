from pymongo import MongoClient
import psycopg2
import subprocess
import json
import pandas as pd
import random
from datetime import datetime
import argparse

def create_table_if_not_exists(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                sensor_type VARCHAR(50),
                measurement FLOAT,
                timestamp TIMESTAMP
            );
        """)
        conn.commit()


# Configurações de conexão para MongoDB
mongo_client = MongoClient('mongodb://localhost:27017/sensor_db.sensor_data')
mongo_db = mongo_client['sensor_db']
mongo_collection = mongo_db['sensor_data']

# Configurações de conexão para Postgres
postgres_conn = psycopg2.connect(
    dbname="sensor_db",
    user="vyeso",
    password="qweqwe000",
    host="localhost",
    port="5432"
)
postgres_cursor = postgres_conn.cursor()

# Função para gerar dados de sensores
def generate_data(n, type_data):
    data = []
    for _ in range(n):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if type_data == 'anomaly':
            measurement = random.choice([-1, None])
        else:
            measurement = random.randint(80, 100)
            if random.random() < 0.05:  # 5% de chance de valor atípico
                measurement = random.randint(20, 45)
        sensor_data = {
            'sensor_type': 'temperature_sensor',
            'measurement': measurement,
            'timestamp': timestamp
        }
        data.append(sensor_data)
    return data

# Função para salvar dados no formato JSON no HDFS
def save_to_json_hdfs(data, hdfs_path):
    # Salvar o arquivo JSON localmente primeiro
    local_path = "/tmp/data.json"
    with open(local_path, 'w') as f:
        json.dump(data, f)

    # Criar o diretório no HDFS, se não existir
    subprocess.run(["hdfs", "dfs", "-mkdir", "-p", hdfs_path])

    # Mover o arquivo local para o HDFS
    subprocess.run(["hdfs", "dfs", "-put", local_path, hdfs_path])

    # (Opcional) Remover o arquivo local após o upload
    subprocess.run(["rm", local_path])

# Função para salvar dados no formato CSV no HDFS
def save_to_csv_hdfs(data, hdfs_path):
    # Salvar o arquivo CSV localmente primeiro
    local_path = "/tmp/data.csv"
    df = pd.DataFrame(data)
    df.to_csv(local_path, index=False)

    # Criar o diretório no HDFS, se não existir
    subprocess.run(["hdfs", "dfs", "-mkdir", "-p", hdfs_path])

    # Mover o arquivo local para o HDFS
    subprocess.run(["hdfs", "dfs", "-put", local_path, hdfs_path])

    # (Opcional) Remover o arquivo local após o upload
    subprocess.run(["rm", local_path])

# Função para salvar dados no MongoDB
def save_to_mongo(data):
    mongo_collection.insert_many(data)

# Função para salvar dados no Postgres
def save_to_postgres(data):
    # Conecte-se ao banco de dados Postgres
    conn = psycopg2.connect(dbname="sensor_db", user="vyeso", password="qweqwe000", host="localhost", port="5432")
    create_table_if_not_exists(conn)  # Criar a tabela, se não existir

    with conn.cursor() as postgres_cursor:
        # Inserir os dados na tabela sensor_data
        postgres_cursor.executemany(
            """
            INSERT INTO sensor_data (sensor_type, measurement, timestamp)
            VALUES (%s, %s, %s);
            """,
            [(d['sensor_type'], d['measurement'], d['timestamp']) for d in data]
        )
        conn.commit()

    conn.close()

# Função principal
def main(n, type_data):
    data = generate_data(n, type_data)
    save_to_json_hdfs(data, '/user/sensor_corp/')

    data = generate_data(n, type_data)
    save_to_csv_hdfs(data, '/user/sensor_corp/')

    data = generate_data(n, type_data)
    save_to_mongo(data)

    data = generate_data(n, type_data)
    save_to_postgres(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script para gerar dados sintéticos de sensores.')
    parser.add_argument('-n', type=int, help='Número de medições a serem geradas', required=True)
    parser.add_argument('--type-data', type=str, choices=['good', 'anomaly'], help='Tipo de dados a serem gerados', required=True)
    
    args = parser.parse_args()
    main(args.n, args.type_data)
