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
        'Rating Escala': 'Rating_Escala',
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
df_tabela = df_filtrado[['Empresa', 'Tipo', 'Data', 'Rating', 'Rating_Escala', 'Faixa_Rating', 'Opiniao_Agregada', 'Opiniao']].copy()
df_tabela['Data'] = pd.to_datetime(df_tabela['Data']).dt.strftime('%d/%m/%Y')
df_tabela['Rating'] = df_tabela['Rating'].apply(lambda x: int(x) if pd.notna(x) else '-')
df_tabela['Rating_Escala'] = df_tabela['Rating_Escala'].fillna('-')
df_tabela.columns = ['Empresa', 'Tipo', 'Data', 'Rating', 'Escala', 'Faixa', 'Opinião', 'Opinião Detalhada']

# Configurar exibição com estilo centralizado
st.markdown("""
<style>
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
    }
    .styled-table thead tr {
        background-color: #F9FAFB;
        text-align: center;
    }
    .styled-table th {
        padding: 12px;
        text-align: center;
        font-weight: 600;
        color: #6B7280;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #E5E7EB;
    }
    .styled-table td {
        padding: 10px 12px;
        text-align: center;
        border-bottom: 1px solid #F3F4F6;
        color: #2D2D2D;
    }
    .styled-table tbody tr:hover {
        background-color: #F9FAFB;
    }
</style>
""", unsafe_allow_html=True)

# Converter para HTML com classe customizada
st.markdown(
    df_tabela.to_html(classes='styled-table', index=False, na_rep='-', escape=False),
    unsafe_allow_html=True
)

# ============================================================
# DETALHES EXPANDÍVEIS
# ============================================================
st.markdown("### Conclusões Detalhadas")

for idx, row in df_filtrado.iterrows():
    if pd.notna(row['Conclusao']):
        rating_escala = row['Rating_Escala'] if 'Rating_Escala' in row and pd.notna(row['Rating_Escala']) else 'N/A'
        with st.expander(f"**{row['Empresa']}** | Rating: {row['Rating'] if pd.notna(row['Rating']) else 'N/A'} ({rating_escala}) | {row['Opiniao_Agregada']}"):
            col_info1, col_info2, col_info3, col_info4 = st.columns(4)
            with col_info1:
                st.markdown(f"**Tipo:** {row['Tipo']}")
            with col_info2:
                st.markdown(f"**Data:** {row['Data'].strftime('%d/%m/%Y') if pd.notna(row['Data']) else 'N/A'}")
            with col_info3:
                st.markdown(f"**Escala:** {rating_escala}")
            with col_info4:
                st.markdown(f"**Opinião:** {row['Opiniao']}")
            st.markdown("---")
            st.markdown(row['Conclusao'])

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")

# Logo em base64
FOOTER_LOGO = "data:image/webp;base64,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"

st.markdown(
    f"""
    <div style='text-align: center; padding: 2rem 1rem 1rem 1rem;'>
        <img src="{FOOTER_LOGO}" alt="AVIN | BTG Pactual" style="max-width: 460px; width: 115%;">
    </div>
    """,
    unsafe_allow_html=True
)
