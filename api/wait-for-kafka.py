#!/usr/bin/env python3
"""Script simple para esperar a que Kafka esté disponible."""
import sys
import time
import os
from kafka import KafkaProducer

def wait_for_kafka():
    kafka_host = os.getenv("KAFKA_HOST", "localhost:9092")
    max_retries = 30
    
    print(f"🔍 Verificando Kafka en {kafka_host}")
    
    for attempt in range(1, max_retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[kafka_host],
                request_timeout_ms=5000,
                retries=0
            )
            producer.close()
            print("✅ Kafka está listo!")
            return True
            
        except Exception as e:
            print(f"⏳ Intento {attempt}/{max_retries} - Kafka no está listo: {e}")
            if attempt < max_retries:
                time.sleep(2)
    
    print("❌ No se pudo conectar a Kafka")
    return False

if __name__ == "__main__":
    sys.exit(0 if wait_for_kafka() else 1)