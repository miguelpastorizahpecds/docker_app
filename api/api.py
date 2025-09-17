"""
Flask API simple para ejercicio de Docker.
Incluye endpoints para PostgreSQL y Kafka con manejo básico de errores.
"""
import os
import sys
import time
import json
import logging
from flask import Flask, request, jsonify
import psycopg2
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración desde variables de entorno
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "user")
DB_PASS = os.getenv("DB_PASS", "password")
KAFKA_HOST = os.getenv("KAFKA_HOST", "localhost:9092")

# Inicializar Kafka Producer con reintentos
def create_kafka_producer():
    """Crear productor de Kafka con manejo de errores."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_HOST],
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            logger.info("Kafka producer inicializado correctamente")
            return producer
        except Exception as e:
            logger.warning(f"Intento {attempt + 1}/{max_retries} falló: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("No se pudo conectar a Kafka")
                raise

producer = create_kafka_producer()

def get_db_connection():
    """Crear conexión a la base de datos."""
    try:
        return psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise

@app.route("/health", methods=["GET"])
def health_check():
    """Endpoint de health check."""
    db_healthy = False
    kafka_healthy = False
    
    # Verificar base de datos
    try:
        conn = get_db_connection()
        conn.close()
        db_healthy = True
    except:
        pass
    
    # Verificar Kafka
    try:
        producer.bootstrap_connected()
        kafka_healthy = True
    except:
        pass
    
    status = "healthy" if (db_healthy and kafka_healthy) else "unhealthy"
    status_code = 200 if status == "healthy" else 503
    
    return jsonify({
        "status": status,
        "database": "ok" if db_healthy else "error",
        "kafka": "ok" if kafka_healthy else "error"
    }), status_code

@app.route("/insert", methods=["POST"])
def insert_message():
    """Insertar mensaje en PostgreSQL."""
    try:
        data = request.get_json()
        if not data or "contenido" not in data:
            return jsonify({"error": "Campo 'contenido' requerido"}), 400
        
        contenido = data["contenido"].strip()
        if not contenido:
            return jsonify({"error": "El contenido no puede estar vacío"}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO mensajes (contenido) VALUES (%s) RETURNING id", (contenido,))
        message_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"Mensaje insertado con ID: {message_id}")
        return jsonify({"status": "inserted", "id": message_id}), 201
        
    except Exception as e:
        logger.error(f"Error insertando mensaje: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/publish", methods=["POST"])
def publish_event():
    """Publicar evento en Kafka."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos requeridos"}), 400
        
        producer.send("test-topic", data)
        producer.flush()
        
        logger.info("Evento publicado en Kafka")
        return jsonify({"status": "published"}), 200
        
    except KafkaError as e:
        logger.error(f"Error publicando en Kafka: {e}")
        return jsonify({"error": "Error publicando evento"}), 503
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route("/messages", methods=["GET"])
def get_messages():
    """Obtener mensajes de PostgreSQL."""
    try:
        limit = min(int(request.args.get("limit", 100)), 1000)
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, contenido, created_at FROM mensajes ORDER BY id DESC LIMIT %s", (limit,))
        messages = cur.fetchall()
        cur.close()
        conn.close()
        
        result = [
            {"id": msg[0], "contenido": msg[1], "created_at": msg[2].isoformat() if msg[2] else None}
            for msg in messages
        ]
        
        return jsonify({"messages": result, "count": len(result)}), 200
        
    except Exception as e:
        logger.error(f"Error obteniendo mensajes: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.errorhandler(404)
def not_found(error):
    """Manejar rutas no encontradas."""
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejar errores internos."""
    logger.error(f"Error interno: {error}")
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == "__main__":
    logger.info("Iniciando aplicación Flask")
    app.run(host="0.0.0.0", port=5000, debug=False)
