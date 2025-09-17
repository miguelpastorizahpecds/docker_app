#!/bin/bash
set -e

echo "Iniciando Docker App..."

# Esperar a que PostgreSQL esté listo
echo "Esperando PostgreSQL..."
while ! python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        dbname=os.getenv('DB_NAME', 'appdb'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASS', 'password'),
        connect_timeout=5
    )
    conn.close()
    print('PostgreSQL está listo')
except Exception as e:
    print(f'PostgreSQL no está listo: {e}')
    exit(1)
"; do
    echo "PostgreSQL no está listo, reintentando en 2 segundos..."
    sleep 2
done

# Esperar a que Kafka esté listo
echo "Esperando Kafka..."
python3 wait-for-kafka.py

echo "Todos los servicios están listos, iniciando API..."
python3 api.py