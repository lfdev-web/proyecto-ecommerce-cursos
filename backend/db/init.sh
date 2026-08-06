#!/bin/bash
# Script de inicialización para la base de datos PostgreSQL.
# Se ejecuta automáticamente por la imagen oficial de postgres al arrancar
# el contenedor por primera vez (docker-entrypoint-initdb.d).
#
# Usa un heredoc de bash (no un .sql plano) para poder inyectar
# POWERBI_READONLY_PASSWORD desde el entorno en vez de dejarlo hardcodeado.
set -e

: "${POWERBI_READONLY_PASSWORD:?POWERBI_READONLY_PASSWORD no está definida — revisa el .env}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- 1. Crear el rol de solo lectura para Power BI
    DO
    \$do\$
    BEGIN
       IF NOT EXISTS (
          SELECT FROM pg_catalog.pg_roles
          WHERE  rolname = 'powerbi_readonly') THEN
          CREATE ROLE powerbi_readonly LOGIN PASSWORD '$POWERBI_READONLY_PASSWORD';
       END IF;
    END
    \$do\$;

    -- 2. Conceder permisos de conexión a la base de datos
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO powerbi_readonly;

    -- 3. Conceder uso del esquema público
    GRANT USAGE ON SCHEMA public TO powerbi_readonly;

    -- 4. Conceder permisos de lectura a las tablas actuales
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO powerbi_readonly;

    -- 5. Conceder permisos de lectura automáticamente a cualquier tabla futura
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO powerbi_readonly;
EOSQL
