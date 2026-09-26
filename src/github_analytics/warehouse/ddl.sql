-- 1. Dimensón Fecha
CREATE TABLE IF NOT EXISTS dim_fecha (
    fecha_key DATE PRIMARY KEY,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    nombre_mes VARCHAR NOT NULL,
    dia INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    dia_semana INTEGER NOT NULL,
    nombre_dia VARCHAR NOT NULL,
    es_fin_de_semana BOOLEAN NOT NULL,
    semana_anio INTEGER NOT NULL
);

-- 2. Dimensión Repositorio
CREATE TABLE IF NOT EXISTS dim_repo (
    repo_key VARCHAR PRIMARY KEY,
    repo_id BIGINT NOT NULL,
    nombre VARCHAR NOT NULL,
    nombre_completo VARCHAR NOT NULL,
    organizacion VARCHAR NOT NULL,
    lenguaje_principal VARCHAR NOT NULL,
    es_privado BOOLEAN NOT NULL,
    html_url VARCHAR NOT NULL,
    descripcion VARCHAR,
    fecha_creacion_utc TIMESTAMP WITH TIME ZONE
);

-- 3. Dimensión Usuario / Colaborador
CREATE TABLE IF NOT EXISTS dim_usuario (
    user_key VARCHAR PRIMARY KEY,
    username VARCHAR NOT NULL,
    tipo_usuario VARCHAR NOT NULL,
    es_asignable BOOLEAN NOT NULL
);

--4. Tabla de Hechos: Issues y Pull Requests
CREATE TABLE IF NOT EXISTS fct_issue (
    issue_key VARCHAR PRIMARY KEY,
    issue_id BIGINT NOT NULL,
    issue_numero INTEGER NOT NULL,
    repo_key VARCHAR NOT NULL,
    autor_user_key VARCHAR NOT NULL,
    asignado_user_key VARCHAR NOT NULL,
    fecha_creacion_key DATE NOT NULL,
    fecha_cierre_key DATE,
    titulo VARCHAR NOT NULL,
    estado VARCHAR NOT NULL,
    es_pull_request BOOLEAN NOT NULL,
    cant_comentarios INTEGER NOT NULL,
    lead_time_horas DOUBLE,
    lead_time_dias DOUBLE,
    created_at_utc TIMESTAMP WITH TIME ZONE NOT NULL,
    closed_at_utc TIMESTAMP WITH TIME ZONE,
    updated_at_utc TIMESTAMP WITH TIME ZONE
);

-- 5. Tabla de Hechos: Commits
CREATE TABLE IF NOT EXISTS fct_commit (
    commit_key VARCHAR PRIMARY KEY,
    commit_sha VARCHAR NOT NULL,
    repo_key VARCHAR NOT NULL,
    autor_user_key VARCHAR NOT NULL,
    fecha_commit_key DATE NOT NULL,
    autor_nombre VARCHAR,
    autor_email VARCHAR,
    mensaje_resumen VARCHAR NOT NULL,
    commit_timestamp_utc TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Indice analiticos para optimización de filtros comunes
CREATE INDEX IF NOT EXISTS idx_fct_issue_repo ON fct_issue(repo_key);
CREATE INDEX IF NOT EXISTS idx_fct_issue_fecha ON fct_issue(fecha_creacion_key);
CREATE INDEX IF NOT EXISTS idx_fct_commit_repo ON fct_commit(repo_key);
CREATE INDEX IF NOT EXISTS idx_fct_commit_fecha ON fct_commit(fecha_commit_key);