-- Consultas

-- 1. Resumen
-- Parámetros: :repo_filter (VARCHAR o NULL), :start_date (DATE), :end_date (DATE)

WITH issue_scoped AS(
    SELECT
        i.*,
        r.nombre as repo_name,
    FROM fct_issue i
    JOIN dim_repo r ON i.repo_key = r.repo_key
    WHERE (:repo_filter IS NULL OR r.nombre = :repo_filter)
    AND i.fecha_creacion_key BETWEEN :start_date AND :end_date
)
SELECT
    COUNT(*) as total_creados,
    COUNT(CASE WHEN estado = 'closed' THEN 1 END) as total_cerrados,
    COUNT(CASE WHEN estado = 'open' THEN 1 END) as total_abiertos,
    ROUND(
        (COUNT(CASE WHEN estado = 'closed' THEN 1 END)::DOUBLE / NULLIF(COUNT(*), 0)) * 100.0, 2
    ) as tasa_cierre_pct,
    ROUND(AVG(CASE WHEN estado = 'closed' THEN lead_time_dias END), 2) as lead_time_promedio_dias,
    ROUND(PERCENTILE_COUNT(0.85) WITHIN GROUP (ORDERY BY lead_times_dias), 2) as lead_time_p85_dias,
    ROUND(AVG(cant_comentarios),2) as promedio_cometarios_por_isue
FROM issue_scoped;

-- 2. Throughput Semanal (Issues cerrados por semana de calendario)
SELECT
    df.anio,
    df.semana_anio,
    MIN(df.fecha_key) as inicio_semana,
    COUNT(i.issue_key) as issues_cerrados,
FROM fct_issue i
JOIN dim_fecha df ON i.fecha_cierre_key = df.fecha_key
JOIN dim_repo r ON i.repo_key = r.repo_key
WHERE i.estado = 'closed'
  AND (:repo_filter IS NULL OR r.nombre = :repo_filter)
  AND df.fecha_key BETWEEN :start_date AND :end_date
GROUP BY df.anio, df.semana_anio
ORDER BY df.anio, df.semana_anio;

-- 3. Histograma y Distribución de Lead Time
SELECT 
    CASE
        WHEN lead_time_dias < 1.0 THEN '1. Menos de 24h'
        WHEN lead_time_dias < 3.0 THEN '2. 1-3 días'
        WHEN lead_time_dias < 7.0 THEN '3. 3-7 días'
        WHEN lead_time_dias < 14.0 THEN '4. 1-2 semanas'
        ELSE '5. > 2 semanas'
    END as rango_resolucion,
    COUNT(*) as cantidad_issues,
    ROUND(COUNT(*)::DOUBLE * 100.0 / SUM(COUNT(*)) OVER (), 2) as porcentaje
FROM fct_issue i
JOIN dim_repo r ON i.repo_key = r.repo_key
WHERE i.estado = 'closed'
  AND (:repo_filter IS NULL OR r.nombre = :repo_filter)
  AND i.fecha_creacion_key BETWEEN :start_date AND :end_date
GROUP BY 1
ORDER BY 1;

-- 4. Contribucion y Actividad por Colaborador
WITH issues_cerrados_autor AS(
    SELECT
        autor_user_key,
        COUNT(*) as issues_cerrados,
        COUNT( CASE WHEN estado = 'closed' THEN 1 END) as issues_resueltos,
        AVG(CASE WHEN estado = 'closed' THEN lead_time_dias END) as lead_time_avg
    FROM fct_issue
    GROUP BY autor_user_key
),
commits_autor AS(
    SELECT
        autor_user_key,
        COUNT(*) as total_commits,
    FROM fct_commit
    GROUP BY autor_user_key
)
SELECT
    u.username,
    COALESCE(ca.total_commits, 0) as total_commits
    COALESCE(ica.issues_creados, 0) as issues_creados,
    COALESCE(ica.issues_resueltos, 0) as issues_resueltos,
    ROUND(COALESCE(ica.lead_time_avg, 0.0), 2) as lead_time_promedio_dias
FROM dim_usuario u
LEFT JOIN commits_autor ca ON u.user_key = ca.autor_user_key
LEFT JOIN issues_cerrados_autor ica ON u.user_key = ica.autor_user_key
WHERE COALESCE(ca.total_commits, 0) > 0 OR COALESCE(ica.issues_creados, 0) > 0
ORDER BY total_commits DESC, issues_resueltos DESC;





