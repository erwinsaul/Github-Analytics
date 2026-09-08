# Esquema Dimensional en Estrella (Star Schema)

El data warehouse analítico se estructura bajo un esquema en estrella con 3 dimensiones y 2 tablas de hechos:

```mermaid
erDiagram
    DIM_REPO ||--o{ FCT_ISSUE : "contiene"
    DIM_USUARIO ||--o{ FCT_ISSUE : "crea / asigna"
    DIM_FECHA ||--o{ FCT_ISSUE : "fecha creacion"

    DIM_REPO ||--o{ FCT_COMMIT : "pertenece"
    DIM_USUARIO ||--o{ FCT_COMMIT : "autor"
    DIM_FECHA ||--o{ FCT_COMMIT : "fecha commit"

    DIM_REPO {
        VARCHAR repo_key PK
        BIGINT repo_id
        VARCHAR nombre
        VARCHAR organizacion
        VARCHAR url
        VARCHAR lenguaje_principal
        BOOLEAN es_privado
        TIMESTAMP_NTZ fecha_creacion
    }

    DIM_USUARIO {
        VARCHAR user_key PK
        BIGINT user_id
        VARCHAR username
        VARCHAR tipo_usuario
        VARCHAR perfil_url
        VARCHAR email
    }

    DIM_FECHA {
        DATE fecha_key PK
        INTEGER anio
        INTEGER mes
        INTEGER dia
        INTEGER trimestre
        INTEGER dia_semana
        VARCHAR nombre_dia
        BOOLEAN es_fin_de_semana
    }

    FCT_ISSUE {
        VARCHAR issue_key PK
        BIGINT issue_id
        INTEGER issue_numero
        VARCHAR repo_key FK
        VARCHAR autor_user_key FK
        VARCHAR asignado_user_key FK
        DATE fecha_creacion_key FK
        DATE fecha_cierre_key FK
        VARCHAR estado
        VARCHAR titulo
        INTEGER cant_comentarios
        DOUBLE lead_time_horas
        DOUBLE lead_time_dias
        TIMESTAMP_NTZ created_at
        TIMESTAMP_NTZ closed_at
    }

    FCT_COMMIT {
        VARCHAR commit_key PK
        VARCHAR commit_sha
        VARCHAR repo_key FK
        VARCHAR autor_user_key FK
        DATE fecha_commit_key FK
        VARCHAR mensaje_resumen
        INTEGER cant_lineas_modificadas
        TIMESTAMP_NTZ commit_timestamp
    }
```

### Granularidad de las Tablas
1. **`dim_repo`**: Un registro por repositorio de GitHub administrado.
2. **`dim_usuario`**: Un registro único por usuario/colaborador identificado en GitHub.
3. **`dim_fecha`**: Un registro por cada día calendario desde el año 2020 hasta 2030.
4. **`fct_issue`**: Un registro por cada Issue o Pull Request registrado en el ciclo de vida.
5. **`fct_commit`**: Un registro por cada commit registrado en las ramas principales de los repositorio.

