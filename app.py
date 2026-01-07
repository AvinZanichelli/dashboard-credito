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
# ESTILOS CSS CUSTOMIZADOS - PADRÃO AVIN
# ============================================================
st.markdown("""
<style>
    /* Importar fonte */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset e base */
    .stApp {
        background-color: #FAFAFA;
        font-family: 'Inter', sans-serif;
    }
    
    /* Ajuste do container principal */
    .block-container {
        padding-top: 3rem !important;
    }
    
    /* Header principal */
    .main-header {
        font-size: 2rem;
        font-weight: 600;
        color: #8B7355;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
        margin-top: 0.5rem;
    }
    
    .sub-header {
        font-size: 0.95rem;
        color: #6B7280;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    
    /* Cards de métricas */
    div[data-testid="stMetric"] {
        background: white;
        padding: 1.25rem;
        border-radius: 8px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #6B7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 600;
        color: #2D2D2D;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #8B7355;
        font-weight: 600;
    }
    
    /* Títulos de seção */
    .stMarkdown h3 {
        color: #8B7355;
        font-weight: 600;
        font-size: 1.1rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E5E7EB;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        font-weight: 500;
        color: #2D2D2D;
    }
    
    /* Dataframe */
    .stDataFrame {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
    }
    
    /* Dividers */
    hr {
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 1.5rem 0;
    }
    
    /* Progress bar na tabela - cor verde #4A7C59 */
    [data-testid="stDataFrame"] [role="progressbar"] > div {
        background-color: #4A7C59 !important;
    }
    
    [data-testid="stDataFrame"] progress {
        accent-color: #4A7C59;
    }
    
    [data-testid="stDataFrame"] progress::-webkit-progress-value {
        background-color: #4A7C59 !important;
    }
    
    [data-testid="stDataFrame"] progress::-moz-progress-bar {
        background-color: #4A7C59 !important;
    }
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
# Possíveis nomes do arquivo no repositório
ARQUIVOS_POSSIVEIS = [
    'data/0 - Compilado Relatórios de Crédito.xlsx',
    'data/0_-_Compilado_Relatórios_de_Crédito.xlsx',
    'data/0-Compilado Relatórios de Crédito.xlsx',
    'data/base_credito.xlsx',
    '0 - Compilado Relatórios de Crédito.xlsx',
    '0_-_Compilado_Relatórios_de_Crédito.xlsx'
]

# Sidebar
with st.sidebar:
    st.markdown("## Dashboard de Crédito")
    st.markdown("---")
    
    # Opção de upload alternativo
    usar_upload = st.checkbox("Carregar outra planilha", value=False)
    
    arquivo_upload = None
    if usar_upload:
        arquivo_upload = st.file_uploader(
            "Selecione o arquivo",
            type=['xlsx'],
            help="Faça upload de uma planilha alternativa"
        )

# Carregar dados
df = None
erro_msg = None

if arquivo_upload:
    try:
        df = carregar_dados(arquivo_upload)
        st.sidebar.success("✅ Planilha alternativa carregada!")
    except Exception as e:
        erro_msg = f"Erro no upload: {e}"
else:
    # Tentar carregar de diferentes caminhos possíveis
    import os
    for arquivo in ARQUIVOS_POSSIVEIS:
        if os.path.exists(arquivo):
            try:
                df = carregar_dados(arquivo)
                st.sidebar.success(f"✅ Dados carregados!")
                break
            except Exception as e:
                erro_msg = f"Arquivo encontrado mas erro ao ler: {e}"
    
    if df is None and erro_msg is None:
        # Listar arquivos disponíveis para debug
        arquivos_encontrados = []
        if os.path.exists('data'):
            arquivos_encontrados = os.listdir('data')
        elif os.path.exists('.'):
            arquivos_encontrados = [f for f in os.listdir('.') if f.endswith('.xlsx')]
        erro_msg = f"Arquivo não encontrado. Arquivos na pasta: {arquivos_encontrados}"

# ============================================================
# VERIFICAR SE HÁ DADOS
# ============================================================
if df is None:
    st.markdown('<p class="main-header">Dashboard de Avaliações de Crédito</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Análise de Risco</p>', unsafe_allow_html=True)
    st.error(f"Não foi possível carregar os dados.")
    if erro_msg:
        st.warning(f"Detalhe: {erro_msg}")
    st.info("Marque a opção 'Carregar outra planilha' na barra lateral para fazer upload manual.")
    st.stop()

# ============================================================
# FILTROS NA SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### Filtros")
    
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
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.markdown('<p class="main-header">Dashboard de Avaliações de Crédito</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Análise de Risco | Atualizado em: ' + datetime.now().strftime('%d/%m/%Y') + '</p>', unsafe_allow_html=True)

# ============================================================
# MÉTRICAS PRINCIPAIS (KPIs)
# ============================================================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="TOTAL DE ANÁLISES",
        value=len(df_filtrado)
    )

with col2:
    empresas = len(df_filtrado[df_filtrado['Tipo'] == 'Empresa'])
    st.metric(
        label="EMPRESAS",
        value=empresas
    )

with col3:
    emissoes = len(df_filtrado[df_filtrado['Tipo'] == 'Emissão'])
    st.metric(
        label="EMISSÕES",
        value=emissoes
    )

with col4:
    rating_medio = df_filtrado['Rating'].mean()
    st.metric(
        label="RATING MÉDIO",
        value=f"{rating_medio:.1f}" if pd.notna(rating_medio) else "N/A"
    )

with col5:
    negativos = len(df_filtrado[df_filtrado['Opiniao_Agregada'] == 'Negativo'])
    pct_neg = (negativos / len(df_filtrado) * 100) if len(df_filtrado) > 0 else 0
    st.metric(
        label="% NEGATIVOS",
        value=f"{pct_neg:.1f}%"
    )

st.markdown("---")

# ============================================================
# GRÁFICOS - LINHA 1
# ============================================================
col_graf1, col_graf2 = st.columns(2)

# Gráfico 1: Distribuição por Opinião
with col_graf1:
    st.markdown("### Distribuição por Opinião")
    
    opiniao_counts = df_filtrado['Opiniao_Agregada'].value_counts().reset_index()
    opiniao_counts.columns = ['Opinião', 'Quantidade']
    
    cores_opiniao = {
        'Positivo': '#4A7C59',      # Verde escuro profissional
        'Neutro': '#8B7355',        # Dourado AVIN
        'Negativo': '#A85454',      # Vermelho sóbrio
        'Atenção': '#C9A227',       # Amarelo mostarda
        'Não Avaliado': '#9CA3AF',  # Cinza neutro
        'Outros': '#6B7280'         # Cinza escuro
    }
    
    fig_opiniao = px.pie(
        opiniao_counts,
        values='Quantidade',
        names='Opinião',
        color='Opinião',
        color_discrete_map=cores_opiniao,
        hole=0.5
    )
    fig_opiniao.update_traces(
        textposition='outside', 
        textinfo='percent+label',
        textfont_size=11,
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig_opiniao.update_layout(
        showlegend=False,
        margin=dict(t=30, b=30, l=30, r=30),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#2D2D2D')
    )
    st.plotly_chart(fig_opiniao, use_container_width=True)

# Gráfico 2: Distribuição por Faixa de Rating
with col_graf2:
    st.markdown("### Distribuição por Faixa de Rating")
    
    faixa_counts = df_filtrado['Faixa_Rating'].value_counts().reset_index()
    faixa_counts.columns = ['Faixa', 'Quantidade']
    
    cores_faixa = {
        'Alto (≥80)': '#4A7C59',     # Verde escuro
        'Médio (65-79)': '#8B7355',  # Dourado AVIN
        'Baixo (<65)': '#A85454',    # Vermelho sóbrio
        'Sem Rating': '#D1D5DB'      # Cinza claro
    }
    
    # Calcular valor máximo do eixo Y (maior valor + 5)
    max_valor = faixa_counts['Quantidade'].max()
    eixo_y_max = max_valor + 5
    
    fig_faixa = px.bar(
        faixa_counts,
        x='Faixa',
        y='Quantidade',
        color='Faixa',
        color_discrete_map=cores_faixa,
        text='Quantidade'
    )
    fig_faixa.update_traces(
        textposition='outside',
        textfont_size=12,
        marker_line_color='#FFFFFF',
        marker_line_width=1
    )
    fig_faixa.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="",
        margin=dict(t=30, b=30, l=30, r=30),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#2D2D2D'),
        xaxis=dict(showgrid=False, showline=True, linecolor='#E5E7EB'),
        yaxis=dict(showgrid=True, gridcolor='#F3F4F6', showline=False, range=[0, eixo_y_max])
    )
    st.plotly_chart(fig_faixa, use_container_width=True)

# ============================================================
# GRÁFICO - RATING POR EMPRESA (LARGURA TOTAL)
# ============================================================
st.markdown("### Rating por Empresa")

df_com_rating = df_filtrado[df_filtrado['Rating'].notna()].copy()

if len(df_com_rating) > 0:
    # Calcular altura dinâmica baseada no número de empresas
    num_empresas = len(df_com_rating)
    altura_grafico = max(500, num_empresas * 40)
    
    # Cores do padrão AVIN
    cores_opiniao_grafico = {
        'Positivo': '#4A7C59',
        'Neutro': '#8B7355',
        'Negativo': '#A85454',
        'Atenção': '#C9A227',
        'Não Avaliado': '#9CA3AF',
        'Outros': '#6B7280'
    }
    
    fig_scatter = px.bar(
        df_com_rating.sort_values('Rating', ascending=True),
        x='Rating',
        y='Empresa',
        color='Opiniao_Agregada',
        color_discrete_map=cores_opiniao_grafico,
        orientation='h',
        hover_data=['Tipo', 'Opiniao', 'Data']
    )
    fig_scatter.update_traces(
        marker_line_color='#FFFFFF',
        marker_line_width=1
    )
    fig_scatter.update_layout(
        yaxis_title="",
        xaxis_title="Rating (0-100)",
        legend_title="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        margin=dict(t=50, b=30, l=20, r=20),
        height=altura_grafico,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#2D2D2D'),
        xaxis=dict(
            showgrid=True, 
            gridcolor='#F3F4F6', 
            showline=True, 
            linecolor='#E5E7EB',
            range=[0, 100]
        ),
        yaxis=dict(showgrid=False, showline=False)
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("Nenhum dado com rating disponível para os filtros selecionados.")

st.markdown("---")

# ============================================================
# TABELA DETALHADA
# ============================================================
st.markdown("### Detalhamento das Análises")

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
st.markdown("### Conclusões Detalhadas")

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
    <div style='text-align: center; color: #9CA3AF; padding: 1rem; font-size: 0.85rem;'>
        Dashboard de Crédito | Dados atualizados conforme planilha carregada
    </div>
    """,
    unsafe_allow_html=True
)
