
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(
    page_title="Monitor de Mortalidad (MoMo) - España",
    page_icon="📊",
    layout="wide"
)

# Estilo CSS para formalidad
st.markdown("""
    <style>
    .main {
        background-color: #F8F9FA;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 5px;
        border: 1px solid #E0E0E0;
    }
    </style>
    """, unsafe_allow_html=True)

# Paleta de colores formal (Muted/Professional)
PALETTE = ['#4C78A8', '#72B7B2', '#59A14F', '#E15759', '#B07AA1', '#9C755F']

@st.cache_data
def load_data():
    df = pd.read_csv('consulta_momo.csv', sep=';')
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['Año'] = df['fecha'].dt.year
    df['Mes_Num'] = df['fecha'].dt.month
    
    # Mapeo de meses en español
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    df['Mes_Nombre'] = df['Mes_Num'].map(meses_es)
    
    # Ordenar meses cronológicamente para los gráficos
    meses_orden = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    df['Mes_Nombre'] = pd.Categorical(df['Mes_Nombre'], categories=meses_orden, ordered=True)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error al cargar los datos: {e}. Asegúrate de que 'consulta_momo.csv' esté en la misma carpeta.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("Configuración")
st.sidebar.markdown("Filtros y Variables")

variables = [
    'defunciones_observadas', 
    'defunciones_estimadas_base', 
    'exceso_todas_causas', 
    'atribuibles_temperatura'
]
var_label = {
    'defunciones_observadas': 'Defunciones Observadas',
    'defunciones_estimadas_base': 'Defunciones Estimadas (Base)',
    'exceso_todas_causas': 'Exceso de Mortalidad',
    'atribuibles_temperatura': 'Atribuibles a Temperatura'
}

selected_var = st.sidebar.selectbox(
    "Selecciona la variable a analizar:", 
    variables, 
    format_func=lambda x: var_label[x]
)

st.sidebar.divider()
st.sidebar.info("""
    Este panel analiza los datos del sistema MoMo en España, 
    calculando tendencias anuales y patrones estacionales mensuales.
""")

# --- MAIN PANEL ---
st.title("📊 Análisis de Mortalidad en España (MoMo)")
st.markdown("---")

# Métricas rápidas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Registros", f"{len(df)} meses")
with col2:
    promedio_total = df[selected_var].mean()
    st.metric("Promedio Mensual Histórico", f"{promedio_total:,.0f}")
with col3:
    max_val = df[selected_var].max()
    st.metric("Pico Máximo Registrado", f"{max_val:,.0f}")

st.write(" ")

# TABS
tab_evolucion, tab_anual, tab_mensual, tab_cruces = st.tabs([
    "📈 Evolución Temporal", 
    "📅 Medias Anuales", 
    "🗓️ Perfil Estacional", 
    "🔄 Comparativa Cruzada"
])

# 1. Evolución Temporal
with tab_evolucion:
    st.subheader(f"Serie Histórica: {var_label[selected_var]}")
    fig_time = px.line(
        df, x='fecha', y=selected_var,
        line_shape='spline',
        color_discrete_sequence=[PALETTE[0]]
    )
    fig_time.update_layout(
        xaxis_title="Año-Mes", yaxis_title="Número de Defunciones",
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig_time, use_container_width=True)

# 2. Medias Anuales
with tab_anual:
    st.subheader("Media de Defunciones por Año")
    df_anual = df.groupby('Año')[selected_var].mean().reset_index()
    
    fig_anual = px.bar(
        df_anual, x='Año', y=selected_var,
        color=selected_var,
        color_continuous_scale='Blues',
        text_auto='.0f'
    )
    fig_anual.update_layout(
        xaxis_title="Año", yaxis_title="Media Mensual",
        template="plotly_white",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_anual, use_container_width=True)

# 3. Medias Mensuales (Perfil Estacional)
with tab_mensual:
    st.subheader("Perfil Estacional: Media Histórica por Mes")
    df_mensual = df.groupby('Mes_Nombre', observed=False)[selected_var].mean().reset_index()
    
    fig_mensual = px.line(
        df_mensual, x='Mes_Nombre', y=selected_var,
        markers=True,
        color_discrete_sequence=[PALETTE[1]]
    )
    fig_mensual.update_layout(
        xaxis_title="Mes", yaxis_title="Media Histórica",
        template="plotly_white"
    )
    st.plotly_chart(fig_mensual, use_container_width=True)

# 4. Posibilidades Cruzadas (Comparativa)
with tab_cruces:
    st.subheader("Cruce de Datos: Año Seleccionado vs Media Histórica")
    
    anos_disponibles = sorted(df['Año'].unique(), reverse=True)
    sel_ano = st.selectbox("Selecciona un año para comparar:", anos_disponibles)
    
    media_hist_mensual = df.groupby('Mes_Nombre', observed=False)[selected_var].mean()
    datos_ano_sel = df[df['Año'] == sel_ano].set_index('Mes_Nombre')[selected_var]
    
    comparativa = pd.DataFrame({
        'Mes': media_hist_mensual.index,
        'Media Histórica': media_hist_mensual.values,
        f'Año {sel_ano}': datos_ano_sel.reindex(media_hist_mensual.index).values
    })
    
    fig_cruce = go.Figure()
    fig_cruce.add_trace(go.Scatter(
        x=comparativa['Mes'], y=comparativa['Media Histórica'],
        name='Promedio Histórico', line=dict(color='grey', dash='dash')
    ))
    fig_cruce.add_trace(go.Bar(
        x=comparativa['Mes'], y=comparativa[f'Año {sel_ano}'],
        name=f'Valores {sel_ano}', marker_color=PALETTE[0], opacity=0.7
    ))
    
    fig_cruce.update_layout(
        template="plotly_white",
        xaxis_title="Mes", yaxis_title="Defunciones",
        barmode='overlay',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_cruce, use_container_width=True)

# Footer
st.markdown("---")
st.caption("Fuente: Datos MoMo. Desarrollado con Streamlit.")
