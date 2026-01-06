import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard de Crédito",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILOS CSS CUSTOMIZADOS
# ============================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    .rating-alto { color: #10B981; font-weight: bold; }
    .rating-medio { color: #F59E0B; font-weight: bold; }
    .rating-baixo { color: #EF4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# FUNÇÕES DE TRATAMENTO DE DADOS
# ============================================================
@st.cache_data
def carregar_dados(arquivo):
    """Carrega e trata os dados da planilha"""
    df = pd.read_excel(arquivo, sheet_name='Relatórios de Crédito')
    
    # Renomear colunas de forma flexível (mapeia nomes antigos para novos)
    colunas_map = {
        '##': 'ID',
        'Nome da Empresa na Base': 'Empresa_Base',
        'Relatórios Enviados': 'Relatorio',
        'Empresa / Emissão': 'Tipo',
        'Data de Envio': 'Data',
        'Rating - X/100': 'Rating',
        'Opinião - Independente de pontuação de Rating': 'Opiniao',
        'Conclusão': 'Conclusao'
    }
    df = df.rename(columns=colunas_map)
    
    # Preencher nome da empresa quando vazio
    if 'Relatorio' in df.columns and 'Empresa_Base' in df.columns:
        df['Empresa'] = df['Relatorio'].fillna(df['Empresa_Base'])
    elif 'Relatorio' in df.columns:
        df['Empresa'] = df['Relatorio']
    else:
        df['Empresa'] = df.iloc[:, 1].fillna(df.iloc[:, 0])
    
    # Criar faixas de rating
    def faixa_rating(r):
        if pd.isna(r): return 'Sem Rating'
        if r >= 80: return 'Alto (≥80)'
        if r >= 65: return 'Médio (65-79)'
        return 'Baixo (<65)'
    
    df['Faixa_Rating'] = df['Rating'].apply(faixa_rating)
    
    # Agregar opiniões em categorias principais
    def agregar_opiniao(op):
        if pd.isna(op): return 'Não Avaliado'
        op_lower = str(op).lower()
        if 'positivo' in op_lower: return 'Positivo'
        if 'negativo' in op_lower or 'default' in op_lower: return 'Negativo'
        if 'neutro' in op_lower: return 'Neutro'
        if 'atenção' in op_lower or 'requer' in op_lower: return 'Atenção'
        return 'Outros'
    
    df['Opiniao_Agregada'] = df['Opiniao'].apply(agregar_opiniao)
    
    # Extrair mês/ano
    df['Mes_Ano'] = pd.to_datetime(df['Data']).dt.to_period('M').astype(str)
    
    # Resumo da conclusão para tooltip
    df['Resumo'] = df['Conclusao'].apply(
        lambda x: (str(x)[:300] + '...') if pd.notna(x) and len(str(x)) > 300 else x
    )
    
    return df

# ============================================================
# CARREGAR DADOS
# ============================================================
# Tentar carregar arquivo local ou permitir upload
try:
    df = carregar_dados('data/base_credito.xlsx')
except:
    df = None

# Sidebar para upload
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=60)
    st.markdown("## 📊 Dashboard de Crédito")
    st.markdown("---")
    
    arquivo_upload = st.file_uploader(
        "📁 Carregar planilha",
        type=['xlsx'],
        help="Faça upload da planilha de relatórios de crédito"
    )
    
    if arquivo_upload:
        df = carregar_dados(arquivo_upload)
        st.success("✅ Dados carregados!")

# ============================================================
# VERIFICAR SE HÁ DADOS
# ============================================================
if df is None:
    st.markdown('<p class="main-header">📊 Dashboard de Avaliações de Crédito</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Trinus.Co - Análise de Risco</p>', unsafe_allow_html=True)
    st.info("👈 Faça upload da planilha de relatórios de crédito na barra lateral para começar.")
    st.stop()

# ============================================================
# FILTROS NA SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 🎯 Filtros")
    
    # Filtro por tipo
    tipos = ['Todos'] + list(df['Tipo'].dropna().unique())
    tipo_selecionado = st.selectbox("Tipo de Análise", tipos)
    
    # Filtro por opinião agregada
    opinioes = ['Todas'] + list(df['Opiniao_Agregada'].unique())
    opiniao_selecionada = st.selectbox("Opinião", opinioes)
    
    # Filtro por faixa de rating
    faixas = ['Todas'] + list(df['Faixa_Rating'].unique())
    faixa_selecionada = st.selectbox("Faixa de Rating", faixas)
    
    # Filtro por período
    if df['Data'].notna().any():
        min_data = df['Data'].min().date()
        max_data = df['Data'].max().date()
        periodo = st.date_input(
            "Período",
            value=(min_data, max_data),
            min_value=min_data,
            max_value=max_data
        )

# Aplicar filtros
df_filtrado = df.copy()

if tipo_selecionado != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_selecionado]

if opiniao_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Opiniao_Agregada'] == opiniao_selecionada]

if faixa_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Faixa_Rating'] == faixa_selecionada]

if 'periodo' in dir() and len(periodo) == 2:
    df_filtrado = df_filtrado[
        (df_filtrado['Data'].dt.date >= periodo[0]) & 
        (df_filtrado['Data'].dt.date <= periodo[1])
    ]

# ============================================================
# CABEÇALHO PRINCIPAL
# ============================================================
st.markdown('<p class="main-header">📊 Dashboard de Avaliações de Crédito</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Análise de Risco | Atualizado em: ' + datetime.now().strftime('%d/%m/%Y') + '</p>', unsafe_allow_html=True)

# ============================================================
# MÉTRICAS PRINCIPAIS (KPIs)
# ============================================================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="📋 Total de Análises",
        value=len(df_filtrado)
    )

with col2:
    empresas = len(df_filtrado[df_filtrado['Tipo'] == 'Empresa'])
    st.metric(
        label="🏢 Empresas",
        value=empresas
    )

with col3:
    emissoes = len(df_filtrado[df_filtrado['Tipo'] == 'Emissão'])
    st.metric(
        label="📄 Emissões",
        value=emissoes
    )

with col4:
    rating_medio = df_filtrado['Rating'].mean()
    st.metric(
        label="⭐ Rating Médio",
        value=f"{rating_medio:.1f}" if pd.notna(rating_medio) else "N/A"
    )

with col5:
    negativos = len(df_filtrado[df_filtrado['Opiniao_Agregada'] == 'Negativo'])
    pct_neg = (negativos / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    st.metric(
        label="⚠️ % Negativos",
        value=f"{pct_neg:.1f}%"
    )

st.markdown("---")

# ============================================================
# GRÁFICOS - LINHA 1
# ============================================================
col_graf1, col_graf2 = st.columns(2)

# Gráfico 1: Distribuição por Opinião
with col_graf1:
    st.markdown("### 📊 Distribuição por Opinião")
    
    opiniao_counts = df_filtrado['Opiniao_Agregada'].value_counts().reset_index()
    opiniao_counts.columns = ['Opinião', 'Quantidade']
    
    cores_opiniao = {
        'Positivo': '#10B981',
        'Neutro': '#6B7280',
        'Negativo': '#EF4444',
        'Atenção': '#F59E0B',
        'Não Avaliado': '#9CA3AF',
        'Outros': '#8B5CF6'
    }
    
    fig_opiniao = px.pie(
        opiniao_counts,
        values='Quantidade',
        names='Opinião',
        color='Opinião',
        color_discrete_map=cores_opiniao,
        hole=0.4
    )
    fig_opiniao.update_traces(textposition='outside', textinfo='percent+label')
    fig_opiniao.update_layout(
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        height=350
    )
    st.plotly_chart(fig_opiniao, use_container_width=True)

# Gráfico 2: Distribuição por Faixa de Rating
with col_graf2:
    st.markdown("### 📈 Distribuição por Faixa de Rating")
    
    faixa_counts = df_filtrado['Faixa_Rating'].value_counts().reset_index()
    faixa_counts.columns = ['Faixa', 'Quantidade']
    
    cores_faixa = {
        'Alto (≥80)': '#10B981',
        'Médio (65-79)': '#F59E0B',
        'Baixo (<65)': '#EF4444',
        'Sem Rating': '#9CA3AF'
    }
    
    fig_faixa = px.bar(
        faixa_counts,
        x='Faixa',
        y='Quantidade',
        color='Faixa',
        color_discrete_map=cores_faixa,
        text='Quantidade'
    )
    fig_faixa.update_traces(textposition='outside')
    fig_faixa.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Quantidade",
        margin=dict(t=20, b=20, l=20, r=20),
        height=350
    )
    st.plotly_chart(fig_faixa, use_container_width=True)

# ============================================================
# GRÁFICO - RATING POR EMPRESA (LARGURA TOTAL)
# ============================================================
st.markdown("### 🎯 Rating por Empresa")

df_com_rating = df_filtrado[df_filtrado['Rating'].notna()].copy()

if len(df_com_rating) > 0:
    # Calcular altura dinâmica baseada no número de empresas
    num_empresas = len(df_com_rating)
    altura_grafico = max(500, num_empresas * 35)
    
    fig_scatter = px.bar(
        df_com_rating.sort_values('Rating', ascending=True),
        x='Rating',
        y='Empresa',
        color='Opiniao_Agregada',
        color_discrete_map=cores_opiniao,
        orientation='h',
        hover_data=['Tipo', 'Opiniao', 'Data']
    )
    fig_scatter.update_layout(
        yaxis_title="",
        xaxis_title="Rating (0-100)",
        legend_title="Opinião",
        margin=dict(t=20, b=20, l=20, r=20),
        height=altura_grafico
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Nenhum dado com rating disponível para os filtros selecionados.")

st.markdown("---")

# ============================================================
# TABELA DETALHADA
# ============================================================
st.markdown("### 📋 Detalhamento das Análises")

# Preparar dados para tabela
df_tabela = df_filtrado[['Empresa', 'Tipo', 'Data', 'Rating', 'Faixa_Rating', 'Opiniao_Agregada', 'Opiniao']].copy()
df_tabela['Data'] = pd.to_datetime(df_tabela['Data']).dt.strftime('%d/%m/%Y')
df_tabela.columns = ['Empresa', 'Tipo', 'Data', 'Rating', 'Faixa', 'Opinião', 'Opinião Detalhada']

# Configurar exibição
st.dataframe(
    df_tabela,
    use_container_width=True,
    height=400,
    column_config={
        "Rating": st.column_config.ProgressColumn(
            "Rating",
            help="Rating de 0 a 100",
            min_value=0,
            max_value=100,
            format="%.0f"
        ),
        "Data": st.column_config.TextColumn("Data"),
    }
)

# ============================================================
# DETALHES EXPANDÍVEIS
# ============================================================
st.markdown("### 📝 Conclusões Detalhadas")

for idx, row in df_filtrado.iterrows():
    if pd.notna(row['Conclusao']):
        with st.expander(f"**{row['Empresa']}** | Rating: {row['Rating'] if pd.notna(row['Rating']) else 'N/A'} | {row['Opiniao_Agregada']}"):
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.markdown(f"**Tipo:** {row['Tipo']}")
            with col_info2:
                st.markdown(f"**Data:** {row['Data'].strftime('%d/%m/%Y') if pd.notna(row['Data']) else 'N/A'}")
            with col_info3:
                st.markdown(f"**Opinião:** {row['Opiniao']}")
            st.markdown("---")
            st.markdown(row['Conclusao'])

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6B7280; padding: 1rem;'>
        📊 Dashboard de Crédito | 
        Dados atualizados conforme planilha carregada
    </div>
    """,
    unsafe_allow_html=True
)
