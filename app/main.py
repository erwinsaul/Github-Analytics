"""Aplicación de Streamlit"""

from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st
from github_analytics.config import settings
from github_analytics.metrics.calculator import MetricsCalculator
from app.components import (
    plot_lead_time_distribution,
    plot_student_contributions,
    plot_weekly_throughput,
    render_kpi_card,
)

st.set_page_config(
    page_title="Github Analytics | Flujo de Desarrollo",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar estilos CSS
css_file = Path(__file__).parent / "styles.css"
if css_file.exists():
    with open(css_file, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_resource
def get_calculator() -> MetricsCalculator:
    """Instancia singleton con cache para el calculador de metricas"""
    return MetricsCalculator()

def main() -> None:
    """Función de renderizado principal"""
    calc = get_calculator()

    # --- SIDEBAR DE FILTROS ---
    st.sidebar.image("https://img.icons8.com/fluency/96/source-code.png", width=64)
    st.sidebar.title("GitHub Analytics")
    st.sidebar.markdown(f"**Organización:** `{settings.github_org}`")

    # Lista de repositorios
    try:
        available_repos = calc.get_available_repositories()
    except Exception:
        available_repos = []
    
    repo_options = ["Todos los repositorios"] + available_repos
    selected_repo_option = st.sidebar.selectbox("Repositorio a Analizar:", repo_options)
    selected_repo = None if selected_repo_option == "Todos los repositorios" else selected_repo_option

    # Rango de Fechas
    default_start = date(2024, 1, 1)
    default_end = date.today() + timedelta(days=30)
    default_range = st.sidebar.date_input(
        "Periodo de Análisis:",
        value=(default_start, default_end),
    )

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, default_end
    
    st.sidebar.divider()
    st.sidebar.info("**Tip:** El Lead Time mide los días desde que se abre un requerimiento hasta su resolución.")

    # --- CABECERA PRINCIPAL ---
    st.markdown('<div class="main-header">Panel de Control de Flujo de Software</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">Métricas de rendimiento para <b>{selected_repo_option}</b>({start_date} al {end_date})</div>',
        unsafe_allow_html=True,
    )

    # --- TARJETAS DE KPIS ---
    try:
        kpis = calc.get_executive_kpis(repo_name=selected_repo, start_date=start_date, end_date=end_date)        
    except Exception as e:
        st.error(f"Error al cargar KPIs: {e}")
        return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Total Issues", str(kpis["total_creados"]), f"{kpis['total_abiertos']} en curso")
    with col2:
        render_kpi_card("Issues Cerrados", str(kpis["total_cerrados"]), "Resueltos")
    with col3:
        render_kpi_card("Tasa de Cierre", f"{kpis['tasa_cierre_pct']}%", "Efectividad de entrega")
    with col4:
        render_kpi_card("Lead Time Medio", f"{kpis['lead_time_promedio_dias']} d", "Tiempo resolución")
    with col5:
        render_kpi_card("Lead Time P85", f"{kpis['lead_time_p85_dias']} d", "85% resuelto en <=")
        
    st.markdown("<br>", unsafe_allow_html=True)

    # --- PESTAÑAS DE VISTA ---
    tab1, tab2, tab3 = st.tabs(["Flujo y Tiempos", "Actividad por Colaborador", "Explorador de Tickets"])

    with tab1:
        c1, c2 = st.columns([3, 2])
        with c1:
            df_tp = calc.get_weekly_throughput(repo_name=selected_repo, start_date=start_date,end_date=end_date)
            st.plotly_chart(plot_weekly_throughput(df_tp), use_container_width=True)
        with c2:
            df_hist = calc.get_lead_time_histogram(repo_name=selected_repo, start_date=start_date, end_date=end_date)
            sp.plotly_chart(plot_lead_time_distribution(df_hist), use_container_width=True)
    
    with tab2:
        df_students = calc.get_student_contributions()
        st.plotly_chart(plot_student_contributions(df_students), use_container_width=True)

        st.subheader("Tabla de Rendimiento Individual")
        st.dataframe(
            df_students,
            use_container_width=True,
            hide_index=True
        )
    
    with tab3:
        st.subheader("Listado Detallado de Issues Registrados")
        with calc._get_conn() as conn:
            df_issues = conn.execute("""
               SELECT 
                   i.issue_numero as "Numero",
                   r.nombre as "Repositorio",
                   i.titulo as "Título",
                   i.estado as "Estado",
                   u.username as "Autor",
                   i.cant_comentarios as "Comentarios",
                   ROUND(i.lead_time_dias,2) as "Lead Time (días)",
                   i.created_at_utc as "Creado el"
               FROM fct_issue i
               JOIN dim_repo r ON i.repo_key = r.repo_key
               JOIN dim_usuario u ON i.autor_user_key = u.user_key
               ORDER BY i.created_at_utc DESC
               LIMIT 100;
            """).df()
        
        st.dataframe(df_issues, use_container_width=True)

if __name__ == "__main__":
    main()