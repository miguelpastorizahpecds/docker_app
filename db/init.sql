-- Inicialización simple de la base de datos
CREATE TABLE IF NOT EXISTS mensajes (
    id SERIAL PRIMARY KEY,
    contenido TEXT NOT NULL CHECK (length(trim(contenido)) > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice para mejorar las consultas
CREATE INDEX IF NOT EXISTS idx_mensajes_created_at ON mensajes (created_at DESC);

-- Mensaje de bienvenida
INSERT INTO mensajes (contenido) 
SELECT 'Bienvenido a Docker App! Este es un mensaje de ejemplo.'
WHERE NOT EXISTS (SELECT 1 FROM mensajes LIMIT 1);
