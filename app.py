import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# CONFIGURACION DE LA PAGINA (Sin iconos)
st.set_page_config(
    page_title="MONITOR DE MORTALIDAD (MOMO) - ESPAÑA",
    layout="wide",
    initial_sidebar_state="collapsed"  # <-- ESTO HACE QUE APAREZCA CERRADO
)

# ESTILO CSS PARA FORMALIDAD Y SERIEDAD
st.markdown("""
    <style>



    .main {
        background-color: #F8F9FA;
    }
    .stMetric {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 5px;
    border: none !important;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 600;

        color: #bbb !important;  /* Color para tabs inactivos */
    }
    
    /* Estilo para el tab activo */
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;  /* Color para tab activo */


    }
    </style>
    """, unsafe_allow_html=True)

# PALETA DE COLORES FORMAL
PALETTE = ['#4C78A8', '#72B7B2', '#59A14F', '#2c17c8', '#a36191', '#9C755F']

@st.cache_data
def load_data():
    # Carga de datos con delimitador punto y coma
    df = pd.read_csv('consulta_momo.csv', sep=';')
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['Año'] = df['fecha'].dt.year
    df['Mes_Num'] = df['fecha'].dt.month
    
    # Mapeo de meses en español
    meses_es = {
        1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
        5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
        9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
    }
    df['Mes_Nombre'] = df['Mes_Num'].map(meses_es)
    
    # Ordenar meses cronológicamente para los gráficos
    meses_orden = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 
                   'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    df['Mes_Nombre'] = pd.Categorical(df['Mes_Nombre'], categories=meses_orden, ordered=True)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"ERROR AL CARGAR LOS DATOS: {e}")
    st.stop()

# --- SIDEBAR / BARRA LATERAL ---
st.sidebar.title("CONFIGURACIÓN")
st.sidebar.markdown("FILTROS Y VARIABLES")

variables = [
    'defunciones_observadas', 
    'defunciones_estimadas_base', 
    'exceso_todas_causas', 
    'atribuibles_temperatura'
]
var_label = {
    'defunciones_observadas': 'Defunciones observadas',
    'defunciones_estimadas_base': 'Defunciones estimadas (base)',
    'exceso_todas_causas': 'Exceso de mortalidad',
    'atribuibles_temperatura': 'Atribuibles a temperatura'
}

selected_var = st.sidebar.selectbox(
    "SELECCIONE VARIABLE:", 
    variables, 
    format_func=lambda x: var_label[x]
)

st.sidebar.divider()
st.sidebar.info("Panel técnico de análisis de mortalidad (sistema MOMO) del Instituto de Salud Carlos III (www.isciii.es)")

# --- PANEL PRINCIPAL ---
st.markdown("<p style='color: #888; font-size: 0.9rem;'>← Despliega el menú lateral para cambiar filtros</p>", unsafe_allow_html=True)
st.title("ANÁLISIS DE MORTALIDAD EN ESPAÑA (MOMO)")

# METRICAS RAPIDAS
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("TOTAL REGISTROS", f"{len(df)} MESES")
with col2:
    promedio_total = df[selected_var].mean()
    st.metric("MEDIA MENSUAL HISTÓRICA", f"{promedio_total:,.0f}")
with col3:
    max_val = df[selected_var].max()
    st.metric("PICO MÁXIMO", f"{max_val:,.0f}")

st.write(" ")

# PESTAÑAS EN MAYUSCULAS Y SIN ICONOS
tab_evolucion, tab_anual, tab_mensual, tab_cruces = st.tabs([
    "EVOLUCIÓN TEMPORAL", 
    "MEDIAS ANUALES", 
    "MEDIAS MENSUALES", 
    "COMPARATIVA CRUZADA"
])

# 1. EVOLUCIÓN TEMPORAL
with tab_evolucion:
    st.subheader(f"SERIE HISTÓRICA: {var_label[selected_var]}")
    fig_time = px.line(
        df, x='fecha', y=selected_var,
        line_shape='spline',
        color_discrete_sequence=[PALETTE[0]]
    )
    fig_time.update_layout(
        xaxis_title="FECHA", yaxis_title="VALOR",
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig_time, use_container_width=True)

# 2. MEDIAS ANUALES
with tab_anual:
    st.subheader(f"PROMEDIO MENSUAL POR AÑO: {var_label[selected_var]}")
    df_anual = df.groupby('Año')[selected_var].mean().reset_index()
    
    fig_anual = px.bar(
        df_anual, x='Año', y=selected_var,
        color=selected_var,
        color_continuous_scale='Greys',
        text_auto='.0f'
    )
    fig_anual.update_layout(
        xaxis_title="AÑO", yaxis_title="MEDIA MENSUAL",
        template="plotly_white",
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_anual, use_container_width=True)

# 3. MEDIAS MENSUALES (Todos los eneros juntos, todos los febreros juntos...)
with tab_mensual:
    st.subheader(f"ANÁLISIS ESTACIONAL: Medias de {var_label[selected_var]}")
    st.markdown("Agregación de datos por mes calendario (promedio de toda la serie).")
    
    # Aquí es donde se recogen todos los meses iguales de la serie
    df_mensual_hist = df.groupby('Mes_Nombre', observed=False)[selected_var].mean().reset_index()
    
    fig_mensual = px.line(
        df_mensual_hist, x='Mes_Nombre', y=selected_var,
        markers=True,
        color_discrete_sequence=[PALETTE[0]]
    )
    fig_mensual.update_layout(
        xaxis_title="MES", yaxis_title="VALOR MEDIO HISTÓRICO",
        template="plotly_white"
    )
    st.plotly_chart(fig_mensual, use_container_width=True)

# 4. COMPARATIVA CRUZADA
with tab_cruces:
    st.subheader("CRUCE DE DATOS: AÑO VS MEDIA HISTÓRICA")
    
    anos_disponibles = sorted(df['Año'].unique(), reverse=True)
    sel_ano = st.selectbox("SELECCIONE AÑO PARA COMPARAR:", anos_disponibles)
    
    media_hist_mensual = df.groupby('Mes_Nombre', observed=False)[selected_var].mean()
    datos_ano_sel = df[df['Año'] == sel_ano].set_index('Mes_Nombre')[selected_var]
    
    comparativa = pd.DataFrame({
        'Mes': media_hist_mensual.index,
        'MEDIA HISTÓRICA': media_hist_mensual.values,
        f'VALOR {sel_ano}': datos_ano_sel.reindex(media_hist_mensual.index).values
    })
    
    fig_cruce = go.Figure()
    fig_cruce.add_trace(go.Scatter(
        x=comparativa['Mes'], y=comparativa['MEDIA HISTÓRICA'],
        name='PROMEDIO HISTÓRICO', line=dict(color='#A0A0A0', dash='dash')
    ))
    fig_cruce.add_trace(go.Bar(
        x=comparativa['Mes'], y=comparativa[f'VALOR {sel_ano}'],
        name=f'VALORES {sel_ano}', marker_color=PALETTE[0], opacity=0.8
    ))
    
    fig_cruce.update_layout(
        template="plotly_white",
        xaxis_title="MES", yaxis_title="VALOR",
        barmode='overlay',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_cruce, use_container_width=True)

# FOOTER
st.markdown("---")
st.caption("FUENTE: SISTEMA MOMO. VISUALIZACIÓN TÉCNICA.")