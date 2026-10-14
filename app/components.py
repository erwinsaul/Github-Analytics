import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_kpi_card(title: str, value: str, subtitle: str="") -> None:
    """Renderiza una tarjeta KPI con estilo personalizado"""

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div style="font-size: 0.8rem; color: #10B981">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def plot_weekly_throughput(df_tp: pd.DataFrame) -> go.Figure:
    """Genera el gráfico de barras y tendencia de Troughput Semanal"""

    if df_tp.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos para el periodo seleccionado")
        return fig
    
    pdf = df_tp.copy()
    pdf["semana_etiqueta"] = pdf["anio"].astype(str) + "-S" + pdf["semana_anio"].astype(str)

    fig = px.bar(
        pdf,
        x="semana_etiqueta",
        y="issues_cerrados",
        labels={"semana_etiqueta": "Semana del Año", "issues_cerrados": "Issues Cerrados"},
        title="<b>Throughput Semanal (Capacidad de Entrega)</b>",
        color_discrete_sequence=["#3B82F6"],
    )

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
    )

    return fig

def plot_lead_time_distribution(df_hist: pd.DataFrame) -> go.Figure:
    """Genera el histograma por categorías de Lead Time."""
    if df_hist.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin Datos")
        return fig
    
    pdf = df_hist.copy()
    fig = px.bar(
        pdf,
        x="rango_resolucion",
        y="cantidad_issues",
        text="cantidad_issues",
        labels={"rango_resolucion": "Rango de Tiempo", "cantidad_issues": "Cantidad de Tickets"},
        title="<b>Distribución de Lead Time (Resolución de Trabajo)</b>",
        color_discrete_sequence=["#10B981"],
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),        
    )
    return fig

def plot_student_contributions(df_students: pd.DataFrame) -> go.Figure:
    """Genera un gráfico de barras horizontal se actividad por colaborador."""
    if df_students.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos de colaboradores")
        return fig
    
    pdf = df_students.copy()
    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=pdf["username"],
        x=pdf["total_commits"],
        name="Commits Realizados",
        orientation="h",
        marker=dict(color="#6366F1")
    ))
    fig.add_trace(go.Bar(
        y=pdf["username"]
        x=pdf["issues_resueltos"],
        name="Issues Resueltos",
        orientation="h",
        marker=dict(color="#EC4899"),
    ))

    fig.update_layout(
        barmode="group",
        title="<b>Actividad de Colaboradores: Commits vs Issues Resueltos</b>",
        template="plotly_white",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=50, b=20),        
    )

    return fig


