# =============================================================================
#  Dashboard Vigilância Nutricional · PBF Tocantins — Streamlit
#  Programa Bolsa Família · SISVAN · 2015–2024
# =============================================================================
#  Instalar:
#      pip install streamlit plotly pandas openpyxl
#
#  Rodar:
#      streamlit run app.py
# =============================================================================

import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Dashboard PBF · Vigilância Nutricional · Tocantins",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado
st.markdown("""
<style>
    /* Fundo geral */
    .stApp { background-color: #06101e; }
    section[data-testid="stSidebar"] { background-color: #0d1b2e; border-right: 1px solid #1e3350; }

    /* Textos */
    html, body, [class*="css"] { color: #e2eaf4; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #e2eaf4 !important; }
    label, .stSelectbox label, .stMultiSelect label { color: #7a99b8 !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 0.06em; }

    /* Cards de métricas */
    [data-testid="metric-container"] {
        background-color: #111f33;
        border: 1px solid #1e3350;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="stMetricValue"] { color: #00d4aa; font-weight: 800; }
    [data-testid="stMetricLabel"] { color: #7a99b8; font-size: 0.7rem; }

    /* Dropdowns e selects */
    .stSelectbox > div > div { background-color: #111f33 !important; border: 1px solid #1e3350 !important; color: #e2eaf4 !important; }

    /* Dividers */
    hr { border-color: #1e3350; }

    /* Tabela */
    .dataframe { background-color: #111f33 !important; color: #e2eaf4 !important; }
    thead tr th { background-color: #162540 !important; color: #7a99b8 !important; font-size: 0.72rem !important; }

    /* Sidebar labels */
    .sidebar-section { color: #00d4aa; font-weight: 700; font-size: 0.85rem; margin-bottom: 4px; display: block; }

    /* Info box */
    .info-box {
        background-color: #111f33;
        border: 1px solid #1e3350;
        border-left: 3px solid #00d4aa;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.82rem;
        color: #7a99b8;
        margin-bottom: 20px;
    }
    .info-box strong { color: #00d4aa; }

    /* Section headers */
    .section-header {
        font-size: 1rem;
        font-weight: 700;
        color: #e2eaf4;
        padding-bottom: 6px;
        border-bottom: 1px solid #1e3350;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CAMINHOS DOS ARQUIVOS
# =============================================================================

NOMES_ARQUIVOS = {
    "0-5 Anos":     "Banco Geral + PBF 0-5 Anos.xlsx",
    "5-10 Anos":    "Banco Geral + PBF 5-10 Anos.xlsx",
    "Adolescentes": "Banco Geral + PBF Adolescentes.xlsx",
    "Adultos":      "Banco Geral + PBF Adultos.xlsx",
    "Idosos":       "Banco Geral + PBF Idosos.xlsx",
}

def _encontrar_pasta_data() -> Path:
    """
    Tenta localizar a pasta 'data/' em vários lugares comuns.
    Retorna o Path da primeira pasta encontrada que contenha ao menos um xlsx.
    """
    candidatas = [
        Path.cwd(),                                     # pasta atual (sem subpasta)
        Path(__file__).resolve().parent,               # ao lado do app.py
    ]
    for pasta in candidatas:
        if pasta.exists():
            xlsx_encontrados = list(pasta.glob("Banco Geral + PBF*.xlsx"))
            if xlsx_encontrados:
                return pasta
    return Path.cwd() / "data"   # fallback padrão para exibir mensagem de erro

_pasta_data = _encontrar_pasta_data()
ARQUIVOS = {fase: _pasta_data / nome for fase, nome in NOMES_ARQUIVOS.items()}

# Verificar se os arquivos existem; mostrar erro amigável se não
_faltando = [str(p) for p in ARQUIVOS.values() if not p.exists()]
if _faltando:
    st.set_page_config(page_title="Erro — Dashboard PBF", page_icon="❌", layout="wide")
    st.error("### ❌ Arquivos não encontrados")
    st.markdown(
        f"""
        O dashboard não conseguiu encontrar as planilhas. Verifique se elas estão
        em uma das localizações abaixo:

        **Opção 1 — subpasta `data/` ao lado do `app.py`** *(recomendado)*
        ```
        seu-projeto/
        ├── app.py
        └── data/
            ├── Banco_Geral___PBF_0-5_Anos.xlsx
            ├── Banco_Geral___PBF_5-10_Anos.xlsx
            ├── Banco_Geral___PBF_Adolescentes.xlsx
            ├── Banco_Geral___PBF_Adultos.xlsx
            └── Banco_Geral___PBF_Idosos.xlsx
        ```

        **Opção 2 — mesma pasta que o `app.py`**
        ```
        seu-projeto/
        ├── app.py
        ├── Banco_Geral___PBF_0-5_Anos.xlsx
        ├── Banco_Geral___PBF_5-10_Anos.xlsx
        ├── ...
        ```

        **Pasta onde o dashboard procurou:** `{_pasta_data}`

        **Arquivos não encontrados:**
        """
    )
    for p in _faltando:
        st.code(p)
    st.info(
        "💡 **Dica:** Rode o Streamlit **dentro da pasta do projeto**:\n"
        "```\ncd seu-projeto\nstreamlit run app.py\n```"
    )
    st.stop()

# =============================================================================
# DICIONÁRIO DE INDICADORES POR FASE DA VIDA
# =============================================================================

INDICADORES = {
    "0-5 Anos": {
        "peso_muito_baixo_idade": {"cols_n": ["PMBI"], "cols_pct": ["PMBI2"], "label": "Peso Muito Baixo p/ Idade",  "grupo": "magreza"},
        "peso_baixo_idade":       {"cols_n": ["PBI"],  "cols_pct": ["PBI2"],  "label": "Peso Baixo p/ Idade",        "grupo": "magreza"},
        "peso_adequado_idade":    {"cols_n": ["PAI"],  "cols_pct": ["PAI2"],  "label": "Peso Adequado p/ Idade",     "grupo": "eutrofia"},
        "peso_elevado_idade":     {"cols_n": ["PEI"],  "cols_pct": ["PEI2"],  "label": "Peso Elevado p/ Idade",      "grupo": "sobrepeso"},
        "alt_muito_baixa_idade":  {"cols_n": ["AMBI"], "cols_pct": ["AMBI2"], "label": "Alt. Muito Baixa p/ Idade",  "grupo": "estatura"},
        "alt_baixa_idade":        {"cols_n": ["ABI"],  "cols_pct": ["ABI2"],  "label": "Alt. Baixa p/ Idade",        "grupo": "estatura"},
        "alt_adequada_idade":     {"cols_n": ["AAI"],  "cols_pct": ["AAI2"],  "label": "Alt. Adequada p/ Idade",     "grupo": "estatura"},
        "magreza_acentuada":      {"cols_n": ["MA"],   "cols_pct": ["MA2"],   "label": "Magreza Acentuada",          "grupo": "magreza"},
        "magreza":                {"cols_n": ["M"],    "cols_pct": ["M2"],    "label": "Magreza",                    "grupo": "magreza"},
        "eutrofia":               {"cols_n": ["E"],    "cols_pct": ["E2"],    "label": "Eutrofia",                   "grupo": "eutrofia"},
        "risco_sobrepeso":        {"cols_n": ["RS"],   "cols_pct": ["RS2"],   "label": "Risco de Sobrepeso",         "grupo": "sobrepeso"},
        "sobrepeso":              {"cols_n": ["S"],    "cols_pct": ["S2"],    "label": "Sobrepeso",                  "grupo": "sobrepeso"},
        "obesidade":              {"cols_n": ["O"],    "cols_pct": ["O2"],    "label": "Obesidade",                  "grupo": "sobrepeso"},
    },
    "5-10 Anos": {
        "peso_muito_baixo_idade": {"cols_n": ["PMBI"], "cols_pct": ["PMBI2"], "label": "Peso Muito Baixo p/ Idade",  "grupo": "magreza"},
        "peso_baixo_idade":       {"cols_n": ["PBI"],  "cols_pct": ["PBI2"],  "label": "Peso Baixo p/ Idade",        "grupo": "magreza"},
        "peso_adequado_idade":    {"cols_n": ["PAI"],  "cols_pct": ["PAI2"],  "label": "Peso Adequado p/ Idade",     "grupo": "eutrofia"},
        "peso_elevado_idade":     {"cols_n": ["PEI"],  "cols_pct": ["PEI2"],  "label": "Peso Elevado p/ Idade",      "grupo": "sobrepeso"},
        "alt_muito_baixa_idade":  {"cols_n": ["AMBI"], "cols_pct": ["AMBI2"], "label": "Alt. Muito Baixa p/ Idade",  "grupo": "estatura"},
        "alt_baixa_idade":        {"cols_n": ["ABI"],  "cols_pct": ["ABI2"],  "label": "Alt. Baixa p/ Idade",        "grupo": "estatura"},
        "alt_adequada_idade":     {"cols_n": ["AAI"],  "cols_pct": ["AAI2"],  "label": "Alt. Adequada p/ Idade",     "grupo": "estatura"},
        "magreza_acentuada":      {"cols_n": ["MA"],   "cols_pct": ["MA2"],   "label": "Magreza Acentuada",          "grupo": "magreza"},
        "magreza":                {"cols_n": ["M"],    "cols_pct": ["M2"],    "label": "Magreza",                    "grupo": "magreza"},
        "eutrofia":               {"cols_n": ["E"],    "cols_pct": ["E2"],    "label": "Eutrofia",                   "grupo": "eutrofia"},
        "sobrepeso":              {"cols_n": ["S"],    "cols_pct": ["S2"],    "label": "Sobrepeso",                  "grupo": "sobrepeso"},
        "obesidade":              {"cols_n": ["O"],    "cols_pct": ["O2"],    "label": "Obesidade",                  "grupo": "sobrepeso"},
        "obesidade_grave":        {"cols_n": ["OG"],   "cols_pct": ["OG2"],   "label": "Obesidade Grave",            "grupo": "sobrepeso"},
    },
    "Adolescentes": {
        "alt_muito_baixa_idade":  {"cols_n": ["AMBI"], "cols_pct": ["AMBI2"], "label": "Alt. Muito Baixa p/ Idade",  "grupo": "estatura"},
        "alt_baixa_idade":        {"cols_n": ["ABI"],  "cols_pct": ["ABI2"],  "label": "Alt. Baixa p/ Idade",        "grupo": "estatura"},
        "alt_adequada_idade":     {"cols_n": ["AAI"],  "cols_pct": ["AAI2"],  "label": "Alt. Adequada p/ Idade",     "grupo": "estatura"},
        "magreza_acentuada":      {"cols_n": ["MA"],   "cols_pct": ["MA2"],   "label": "Magreza Acentuada",          "grupo": "magreza"},
        "magreza":                {"cols_n": ["M"],    "cols_pct": ["M2"],    "label": "Magreza",                    "grupo": "magreza"},
        "eutrofia":               {"cols_n": ["E"],    "cols_pct": ["E2"],    "label": "Eutrofia",                   "grupo": "eutrofia"},
        "sobrepeso":              {"cols_n": ["S"],    "cols_pct": ["S2"],    "label": "Sobrepeso",                  "grupo": "sobrepeso"},
        "obesidade":              {"cols_n": ["O"],    "cols_pct": ["O2"],    "label": "Obesidade",                  "grupo": "sobrepeso"},
        "obesidade_grave":        {"cols_n": ["OG"],   "cols_pct": ["OG2"],   "label": "Obesidade Grave",            "grupo": "sobrepeso"},
    },
    "Adultos": {
        "baixo_peso": {"cols_n": ["BP"],    "cols_pct": ["BP%"],   "label": "Baixo Peso",         "grupo": "magreza"},
        "eutrofia":   {"cols_n": ["E"],     "cols_pct": ["E%"],    "label": "Eutrofia",            "grupo": "eutrofia"},
        "sobrepeso":  {"cols_n": ["S"],     "cols_pct": ["S%"],    "label": "Sobrepeso",           "grupo": "sobrepeso"},
        "obesidade_g1": {"cols_n": ["OGI"], "cols_pct": ["OGI%"], "label": "Obesidade Grau I",    "grupo": "sobrepeso"},
        "obesidade_g2": {"cols_n": ["OGII"],"cols_pct": ["OGII%"],"label": "Obesidade Grau II",   "grupo": "sobrepeso"},
        "obesidade_g3": {"cols_n": ["OGIII"],"cols_pct":["OGIII%"],"label": "Obesidade Grau III", "grupo": "sobrepeso"},
    },
    "Idosos": {
        "baixo_peso": {"cols_n": ["BP"], "cols_pct": ["BP%"], "label": "Baixo Peso", "grupo": "magreza"},
        "eutrofia":   {"cols_n": ["E"],  "cols_pct": ["E%"],  "label": "Eutrofia",   "grupo": "eutrofia"},
        "sobrepeso":  {"cols_n": ["S"],  "cols_pct": ["S%"],  "label": "Sobrepeso",  "grupo": "sobrepeso"},
    },
}

GRUPO_CORES = {
    "magreza":   "#f43f5e",
    "sobrepeso": "#f59e0b",
    "eutrofia":  "#10b981",
    "estatura":  "#818cf8",
}

REGIAO_CORES = {
    "Cantão":                     "#7c3aed",
    "Bico do Papagaio":           "#0891b2",
    "Ilha do Bananal":            "#059669",
    "Sudeste":                    "#d97706",
    "Capim Dourado":              "#dc2626",
    "Médio Norte Araguaia":       "#db2777",
    "Cerrado Tocantins Araguaia": "#2563eb",
    "Amor Perfeito":              "#65a30d",
}

FASE_DESCRICAO = {
    "0-5 Anos":     "Crianças de 0 a 5 anos. Indicadores de peso e estatura para a idade, além de magreza, eutrofia, risco de sobrepeso, sobrepeso e obesidade.",
    "5-10 Anos":    "Crianças de 5 a 10 anos. Indicadores de estatura para a idade e IMC (magreza acentuada, magreza, eutrofia, sobrepeso, obesidade e obesidade grave).",
    "Adolescentes": "Adolescentes (10–19 anos). Indicadores de estatura para a idade e IMC (magreza acentuada, magreza, eutrofia, sobrepeso, obesidade e obesidade grave).",
    "Adultos":      "Adultos (20–59 anos). Classificação pelo IMC: baixo peso, eutrofia, sobrepeso e obesidade graus I, II e III.",
    "Idosos":       "Idosos (60+ anos). Classificação pelo IMC adaptado: baixo peso, eutrofia e sobrepeso.",
}

PLOTLY_BASE = dict(
    paper_bgcolor="#111f33",
    plot_bgcolor="#111f33",
    font=dict(color="#7a99b8", family="Inter, sans-serif", size=12),
    margin=dict(t=50, b=40, l=60, r=20),
    xaxis=dict(gridcolor="#1e3350", linecolor="#1e3350", zerolinecolor="#1e3350"),
    yaxis=dict(gridcolor="#1e3350", linecolor="#1e3350", zerolinecolor="#1e3350"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e3350", font=dict(size=11)),
    hoverlabel=dict(bgcolor="#162540", font_color="#e2eaf4", bordercolor="#1e3350"),
)

# =============================================================================
# CARREGAMENTO DOS DADOS (com cache)
# =============================================================================

@st.cache_data(show_spinner="Carregando planilhas...")
def carregar_dados():
    dfs = {}
    for fase, path in ARQUIVOS.items():
        df = pd.read_excel(path)
        df = df.fillna(0)
        df["REGIÃO DE SAÚDE"] = df["REGIÃO DE SAÚDE"].astype(str).str.strip()
        df["MUNICIPIO"] = df["MUNICIPIO"].astype(str).str.strip()
        dfs[fase] = df
    return dfs

DFS = carregar_dados()

MUNICIPIOS  = sorted(DFS["0-5 Anos"]["MUNICIPIO"].unique().tolist())
ANOS        = sorted(DFS["0-5 Anos"]["Ano"].unique().tolist())
REGIOES     = sorted(DFS["0-5 Anos"]["REGIÃO DE SAÚDE"].unique().tolist())

# =============================================================================
# FUNÇÕES DE CÁLCULO
# =============================================================================

def calcular_pct(df, fase, indicador, use_pbf=False):
    """
    Calcula o percentual de um indicador no DataFrame recebido.
      use_pbf=False  -> colunas originais + TOTAL       (todos os avaliados)
      use_pbf=True   -> colunas _PBF      + TOTAL_PBF   (somente beneficiários PBF)
    """
    ind = INDICADORES[fase][indicador]
    if use_pbf:
        cols  = [c + "_PBF" for c in ind["cols_n"] if c + "_PBF" in df.columns]
        total = df["TOTAL_PBF"].sum()
    else:
        cols  = [c for c in ind["cols_n"] if c in df.columns]
        total = df["TOTAL"].sum()
    if not cols or total == 0:
        return 0.0
    return round(float(sum(df[c].sum() for c in cols) / total) * 100, 2)


def serie_temporal(df_fase, fase, use_pbf=False):
    """Retorna DataFrame com percentuais por ano para todos os indicadores."""
    total_col = "TOTAL_PBF" if use_pbf else "TOTAL"
    rows = []
    for ano in ANOS:
        df_a = df_fase[df_fase["Ano"] == ano]
        row  = {"Ano": ano, "Total": int(df_a[total_col].sum())}
        for k in INDICADORES[fase]:
            row[k] = calcular_pct(df_a, fase, k, use_pbf)
        rows.append(row)
    return pd.DataFrame(rows)


def tabela_municipios(df_fase, fase, ano, use_pbf=False):
    """Retorna DataFrame por município para o ano selecionado."""
    total_col = "TOTAL_PBF" if use_pbf else "TOTAL"
    df_a  = df_fase[df_fase["Ano"] == ano]
    rows  = []
    for mun, grp in df_a.groupby("MUNICIPIO"):
        row = {
            "Município": mun,
            "Região":    grp["REGIÃO DE SAÚDE"].iloc[0],
            "Total":     int(grp[total_col].sum()),
        }
        for k, v in INDICADORES[fase].items():
            row[v["label"]] = calcular_pct(grp, fase, k, use_pbf)
        rows.append(row)
    return pd.DataFrame(rows)

# =============================================================================
# SIDEBAR — FILTROS
# =============================================================================

with st.sidebar:
    st.markdown("## 📊 Filtros")
    st.markdown("---")

    fase = st.selectbox("🧒 Fase da Vida", list(ARQUIVOS.keys()))

    st.markdown("---")

    regiao_opcoes = ["Todas as Regiões"] + REGIOES
    regiao = st.selectbox("🗺 Região de Saúde", regiao_opcoes)

    # Municípios filtrados pela região
    df_atual = DFS[fase]
    if regiao != "Todas as Regiões":
        muns_disp = sorted(df_atual[df_atual["REGIÃO DE SAÚDE"] == regiao]["MUNICIPIO"].unique().tolist())
    else:
        muns_disp = MUNICIPIOS

    municipio_opcoes = ["Todo o Estado (Tocantins)"] + muns_disp
    municipio = st.selectbox("🏙 Município", municipio_opcoes)

    st.markdown("---")

    ano_ref = st.selectbox("📅 Ano de Referência (KPIs)", list(reversed(ANOS)))

    st.markdown("---")

    # Indicador para o heatmap
    inds_fase = INDICADORES[fase]
    ind_labels = {k: v["label"] for k, v in inds_fase.items()}
    hm_key = st.selectbox(
        "🌡 Indicador — Heatmap",
        list(ind_labels.keys()),
        format_func=lambda k: ind_labels[k],
    )

    st.markdown("---")

    pbf_modo = st.radio(
        "👁 Recorte populacional",
        options=["Total (todos avaliados)", "Somente Beneficiários PBF", "Comparar Total vs PBF"],
        index=0,
        help=(
            "**Total** — considera todos os indivíduos avaliados.\n\n"
            "**Somente PBF** — considera apenas os beneficiários do Programa Bolsa Família.\n\n"
            "**Comparar** — exibe ambas as séries sobrepostas nos gráficos e lado a lado nos KPIs."
        ),
    )
    use_pbf   = pbf_modo == "Somente Beneficiários PBF"
    comparar  = pbf_modo == "Comparar Total vs PBF"

    st.markdown("---")
    st.markdown(
        "<small style='color:#4a6a88'>PBF · SISVAN · 2015–2024<br>139 municípios · 8 regiões</small>",
        unsafe_allow_html=True,
    )

# =============================================================================
# FILTRAR DATAFRAME CONFORME SELEÇÃO
# =============================================================================

df_f = df_atual.copy()
if regiao != "Todas as Regiões":
    df_f = df_f[df_f["REGIÃO DE SAÚDE"] == regiao]
if municipio != "Todo o Estado (Tocantins)":
    df_f = df_f[df_f["MUNICIPIO"] == municipio]

escopo_label = municipio if municipio != "Todo o Estado (Tocantins)" else (
    regiao if regiao != "Todas as Regiões" else "Tocantins (Estado)"
)

# =============================================================================
# CABEÇALHO
# =============================================================================

st.markdown(
    f"""
    <div style='padding:4px 0 18px 0'>
        <h1 style='margin:0;font-size:1.6rem;color:#00d4aa;font-weight:800'>
            📊 Dashboard Vigilância Nutricional · PBF Tocantins
        </h1>
        <p style='color:#7a99b8;font-size:0.8rem;margin:6px 0 0 0;font-family:monospace'>
            Programa Bolsa Família · SISVAN · 2015–2024 · 139 municípios · 8 regiões de saúde
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Info da fase
st.markdown(
    f"<div class='info-box'><strong>Fase: {fase}</strong> — {FASE_DESCRICAO[fase]}</div>",
    unsafe_allow_html=True,
)

# =============================================================================
# KPIs
# =============================================================================

st.markdown("<div class='section-header'>📌 Indicadores — " + str(ano_ref) + "</div>", unsafe_allow_html=True)

df_ano = df_f[df_f["Ano"] == ano_ref]
total_col_kpi = "TOTAL_PBF" if use_pbf else "TOTAL"
total_ano     = int(df_ano[total_col_kpi].sum())
total_ano_pbf = int(df_ano["TOTAL_PBF"].sum())
total_ano_all = int(df_ano["TOTAL"].sum())

kpi_keys = list(inds_fase.keys())

# ── Linha de totais ────────────────────────────────────────────────────────
cols_kpi0 = st.columns(3 if comparar else 2)
with cols_kpi0[0]:
    st.metric("👥 Total Avaliados (Geral)", f"{total_ano_all:,}".replace(",", "."))
with cols_kpi0[1]:
    st.metric("🎯 Total Avaliados (PBF)", f"{total_ano_pbf:,}".replace(",", "."))
if comparar:
    with cols_kpi0[2]:
        cobertura = round(total_ano_pbf / total_ano_all * 100, 1) if total_ano_all > 0 else 0
        st.metric("📊 Cobertura PBF", f"{cobertura:.1f}%", help="% dos avaliados que são beneficiários PBF")

st.markdown("")

# ── Linhas de indicadores ──────────────────────────────────────────────────
# Em modo Comparar exibimos Total | PBF | Δ para cada indicador
if comparar:
    for k in kpi_keys:
        val_total = calcular_pct(df_ano, fase, k, use_pbf=False)
        val_pbf   = calcular_pct(df_ano, fase, k, use_pbf=True)
        delta     = round(val_pbf - val_total, 1)
        label     = inds_fase[k]["label"]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(f"📊 {label} · Total",  f"{val_total:.1f}%")
        with c2:
            st.metric(f"🎯 {label} · PBF",    f"{val_pbf:.1f}%")
        with c3:
            sinal = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
            cor   = "🔴" if delta > 0.5 else ("🟢" if delta < -0.5 else "🟡")
            st.metric(f"{cor} Diferença (PBF − Total)", f"{delta:+.1f} p.p.")
else:
    # Linha 1: primeiros 4
    cols_kpi1 = st.columns(min(len(kpi_keys), 4))
    for i, k in enumerate(kpi_keys[:4]):
        val = calcular_pct(df_ano, fase, k, use_pbf)
        with cols_kpi1[i]:
            st.metric(inds_fase[k]["label"], f"{val:.1f}%")
    # Linha 2: restantes
    if len(kpi_keys) > 4:
        restantes = kpi_keys[4:]
        cols_kpi2 = st.columns(min(len(restantes), 4))
        for i, k in enumerate(restantes[:4]):
            val = calcular_pct(df_ano, fase, k, use_pbf)
            with cols_kpi2[i]:
                st.metric(inds_fase[k]["label"], f"{val:.1f}%")

st.markdown("---")

# =============================================================================
# SÉRIE TEMPORAL
# =============================================================================

st.markdown(f"<div class='section-header'>📈 Evolução Histórica — {escopo_label}</div>", unsafe_allow_html=True)

serie      = serie_temporal(df_f, fase, use_pbf=use_pbf or False)
serie_pbf  = serie_temporal(df_f, fase, use_pbf=True)   # sempre calculado para o modo Comparar
serie_all  = serie_temporal(df_f, fase, use_pbf=False)

col1, col2 = st.columns(2)

def _add_dual_traces(fig, ind_keys, serie_total, serie_pbf_, shades, comparar_):
    """Adiciona traces ao gráfico: se comparar_, linha Total + linha PBF; senão só série ativa."""
    for i, k in enumerate(ind_keys):
        cor = shades[i % len(shades)]
        if comparar_:
            # Linha Total — sólida
            fig.add_trace(go.Scatter(
                x=serie_total["Ano"], y=serie_total[k],
                name=f"{INDICADORES[fase][k]['label']} · Total",
                mode="lines+markers",
                line=dict(width=2.5, color=cor),
                marker=dict(size=5),
                legendgroup=k,
            ))
            # Linha PBF — tracejada, mesma cor mais clara
            fig.add_trace(go.Scatter(
                x=serie_pbf_["Ano"], y=serie_pbf_[k],
                name=f"{INDICADORES[fase][k]['label']} · PBF",
                mode="lines+markers",
                line=dict(width=2, color=cor, dash="dot"),
                marker=dict(size=4, symbol="diamond"),
                legendgroup=k,
            ))
        else:
            fig.add_trace(go.Scatter(
                x=serie["Ano"], y=serie[k],
                name=INDICADORES[fase][k]["label"],
                mode="lines+markers",
                line=dict(width=2.5, color=cor),
                marker=dict(size=5),
                fill="tozeroy" if i == 0 else "none",
                fillcolor=f"rgba({int(cor[1:3],16)},{int(cor[3:5],16)},{int(cor[5:7],16)},0.10)" if i == 0 else "rgba(0,0,0,0)",
            ))

# ── Magreza ────────────────────────────────────────────────────────────────
with col1:
    fig_mag = go.Figure(layout=PLOTLY_BASE)
    fig_mag.update_layout(
        title=dict(text="📉 Magreza / Baixo Peso", font=dict(color="#e2eaf4", size=13)),
        height=340,
        legend=dict(orientation="h", y=-0.30, font=dict(size=10)) if comparar else dict(),
    )
    inds_mag = [k for k, v in inds_fase.items() if v["grupo"] == "magreza"]
    shades_m = ["#f43f5e", "#fb7185", "#fda4af", "#fecdd3"]
    _add_dual_traces(fig_mag, inds_mag, serie_all, serie_pbf, shades_m, comparar)
    fig_mag.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_mag, use_container_width=True)

# ── Sobrepeso ───────────────────────────────────────────────────────────────
with col2:
    fig_sob = go.Figure(layout=PLOTLY_BASE)
    fig_sob.update_layout(
        title=dict(text="📈 Sobrepeso & Obesidade", font=dict(color="#e2eaf4", size=13)),
        height=340,
        legend=dict(orientation="h", y=-0.30, font=dict(size=10)) if comparar else dict(),
    )
    inds_sob = [k for k, v in inds_fase.items() if v["grupo"] == "sobrepeso"]
    shades_s = ["#f59e0b", "#ef4444", "#dc2626", "#a855f7", "#7c3aed"]
    _add_dual_traces(fig_sob, inds_sob, serie_all, serie_pbf, shades_s, comparar)
    fig_sob.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_sob, use_container_width=True)

# ── Distribuição completa ────────────────────────────────────────────────────
fig_dist = go.Figure(layout=PLOTLY_BASE)
subtitulo_dist = " · Somente PBF" if use_pbf else (" · Total vs PBF" if comparar else " · Total")
fig_dist.update_layout(
    title=dict(text=f"📊 Distribuição Nutricional Completa{subtitulo_dist}",
               font=dict(color="#e2eaf4", size=13)),
    barmode="group",
    height=400,
    legend=dict(orientation="h", y=-0.28, font=dict(size=10)),
    margin=dict(t=50, b=90, l=60, r=20),
)
paleta = ["#10b981","#f43f5e","#f59e0b","#ef4444","#818cf8",
          "#0891b2","#db2777","#65a30d","#d97706","#a855f7","#059669","#dc2626"]
for i, (k, v) in enumerate(inds_fase.items()):
    cor = paleta[i % len(paleta)]
    if comparar:
        fig_dist.add_trace(go.Bar(
            x=serie_all["Ano"], y=serie_all[k],
            name=f"{v['label']} · Total",
            marker_color=cor,
            marker_line_color=cor, marker_line_width=1,
            legendgroup=k,
        ))
        fig_dist.add_trace(go.Bar(
            x=serie_pbf["Ano"], y=serie_pbf[k],
            name=f"{v['label']} · PBF",
            marker_color=cor,
            marker_line_color=cor, marker_line_width=1,
            legendgroup=k,
        ))
    else:
        fig_dist.add_trace(go.Bar(
            x=serie["Ano"], y=serie[k],
            name=v["label"],
            marker_color=cor,
        ))
fig_dist.update_yaxes(ticksuffix="%")
st.plotly_chart(fig_dist, use_container_width=True)

st.markdown("---")

# =============================================================================
# HEATMAP POR MUNICÍPIO
# =============================================================================

recorte_hm = " · PBF" if use_pbf else (" · Total" if not comparar else " · Total")
st.markdown(f"<div class='section-header'>🌡 Heatmap por Município — {inds_fase[hm_key]['label']}{recorte_hm} ({ano_ref})</div>",
            unsafe_allow_html=True)

df_hm_base = df_atual.copy()
if regiao != "Todas as Regiões":
    df_hm_base = df_hm_base[df_hm_base["REGIÃO DE SAÚDE"] == regiao]
df_hm_ano = df_hm_base[df_hm_base["Ano"] == ano_ref]

total_col_hm = "TOTAL_PBF" if use_pbf else "TOTAL"
hm_rows = []
for mun, grp in df_hm_ano.groupby("MUNICIPIO"):
    hm_rows.append({
        "MUNICIPIO": mun,
        "REGIÃO":    grp["REGIÃO DE SAÚDE"].iloc[0],
        "Total":     int(grp[total_col_hm].sum()),
        hm_key:      calcular_pct(grp, fase, hm_key, use_pbf),
    })
df_hm = pd.DataFrame(hm_rows).sort_values(hm_key, ascending=True)

grupo_hm = inds_fase[hm_key]["grupo"]
if grupo_hm == "eutrofia":
    colorscale = [[0, "#1e3350"], [0.5, "#059669"], [1, "#10b981"]]
elif grupo_hm == "magreza":
    colorscale = [[0, "#1e3350"], [0.5, "#f87171"], [1, "#f43f5e"]]
elif grupo_hm == "sobrepeso":
    colorscale = [[0, "#1e3350"], [0.5, "#fbbf24"], [1, "#f59e0b"]]
else:
    colorscale = [[0, "#1e3350"], [0.5, "#818cf8"], [1, "#6366f1"]]

fig_hm = go.Figure(layout=PLOTLY_BASE)
fig_hm.update_layout(
    height=max(500, len(df_hm) * 19),
    margin=dict(t=30, b=20, l=170, r=110),
    yaxis=dict(tickfont=dict(size=9.5)),
)
fig_hm.add_trace(go.Bar(
    x=df_hm[hm_key],
    y=df_hm["MUNICIPIO"],
    orientation="h",
    marker=dict(
        color=df_hm[hm_key],
        colorscale=colorscale,
        showscale=True,
        colorbar=dict(
            title="%", ticksuffix="%",
            tickfont=dict(color="#7a99b8"),
            title_font=dict(color="#7a99b8"),
            bgcolor="#111f33",
            bordercolor="#1e3350",
        ),
    ),
    customdata=df_hm[["REGIÃO", "Total"]].values,
    hovertemplate=(
        "<b>%{y}</b><br>"
        f"{inds_fase[hm_key]['label']}: %{{x:.1f}}%<br>"
        "Região: %{customdata[0]}<br>"
        "Total: %{customdata[1]:,}<extra></extra>"
    ),
))
fig_hm.update_xaxes(ticksuffix="%")
st.plotly_chart(fig_hm, use_container_width=True)

st.markdown("---")

# =============================================================================
# RANKINGS
# =============================================================================

st.markdown(f"<div class='section-header'>🏆 Ranking de Municípios ({max(ANOS)})</div>", unsafe_allow_html=True)

df_rank_base = df_atual[df_atual["Ano"] == max(ANOS)].copy()
if regiao != "Todas as Regiões":
    df_rank_base = df_rank_base[df_rank_base["REGIÃO DE SAÚDE"] == regiao]

total_col_rank = "TOTAL_PBF" if use_pbf else "TOTAL"
rank_rows = []
for mun, grp in df_rank_base.groupby("MUNICIPIO"):
    row = {"MUNICIPIO": mun, "REGIÃO": grp["REGIÃO DE SAÚDE"].iloc[0],
           "Total": int(grp[total_col_rank].sum())}
    for k in inds_fase:
        row[k] = calcular_pct(grp, fase, k, use_pbf)
    rank_rows.append(row)
df_rank = pd.DataFrame(rank_rows)

col_r1, col_r2 = st.columns(2)

# Primeiro indicador de magreza
ind_mag_key = next((k for k, v in inds_fase.items() if v["grupo"] == "magreza"), None)
# Primeiro indicador de sobrepeso
ind_sob_key = next((k for k, v in inds_fase.items() if v["grupo"] == "sobrepeso"), None)

with col_r1:
    if ind_mag_key and not df_rank.empty:
        top_m = df_rank.nlargest(15, ind_mag_key).sort_values(ind_mag_key, ascending=True)
        fig_rm = go.Figure(layout=PLOTLY_BASE)
        fig_rm.update_layout(
            title=dict(text=f"🔴 Top 15 — {inds_fase[ind_mag_key]['label']}", font=dict(color="#e2eaf4", size=12)),
            height=400, margin=dict(t=50, b=20, l=160, r=20),
        )
        fig_rm.add_trace(go.Bar(
            x=top_m[ind_mag_key],
            y=top_m["MUNICIPIO"].apply(lambda x: x[:20] + "…" if len(x) > 20 else x),
            orientation="h",
            marker_color=[REGIAO_CORES.get(r, "#94a3b8") for r in top_m["REGIÃO"]],
            marker_line_color=[REGIAO_CORES.get(r, "#94a3b8") for r in top_m["REGIÃO"]],
            marker_line_width=1,
            customdata=top_m[["REGIÃO", "Total"]].values,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<br>%{customdata[0]}<extra></extra>",
        ))
        fig_rm.update_xaxes(ticksuffix="%")
        fig_rm.update_yaxes(tickfont=dict(size=10))
        st.plotly_chart(fig_rm, use_container_width=True)

with col_r2:
    if ind_sob_key and not df_rank.empty:
        top_s = df_rank.nlargest(15, ind_sob_key).sort_values(ind_sob_key, ascending=True)
        fig_rs = go.Figure(layout=PLOTLY_BASE)
        fig_rs.update_layout(
            title=dict(text=f"🟡 Top 15 — {inds_fase[ind_sob_key]['label']}", font=dict(color="#e2eaf4", size=12)),
            height=400, margin=dict(t=50, b=20, l=160, r=20),
        )
        fig_rs.add_trace(go.Bar(
            x=top_s[ind_sob_key],
            y=top_s["MUNICIPIO"].apply(lambda x: x[:20] + "…" if len(x) > 20 else x),
            orientation="h",
            marker_color=[REGIAO_CORES.get(r, "#94a3b8") for r in top_s["REGIÃO"]],
            marker_line_color=[REGIAO_CORES.get(r, "#94a3b8") for r in top_s["REGIÃO"]],
            marker_line_width=1,
            customdata=top_s[["REGIÃO", "Total"]].values,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<br>%{customdata[0]}<extra></extra>",
        ))
        fig_rs.update_xaxes(ticksuffix="%")
        fig_rs.update_yaxes(tickfont=dict(size=10))
        st.plotly_chart(fig_rs, use_container_width=True)

st.markdown("---")

# =============================================================================
# TABELA DETALHADA
# =============================================================================

modo_label = "Beneficiários PBF" if use_pbf else ("Total vs PBF" if comparar else "Todos os Avaliados")
st.markdown(f"<div class='section-header'>📋 Tabela Detalhada — {fase} · {ano_ref} · {modo_label}</div>",
            unsafe_allow_html=True)

df_tab = tabela_municipios(df_f, fase, ano_ref, use_pbf=use_pbf)

# Formatar colunas de percentual
cols_pct = [v["label"] for v in inds_fase.values()]
df_tab_fmt = df_tab.copy()
for col in cols_pct:
    if col in df_tab_fmt.columns:
        df_tab_fmt[col] = df_tab_fmt[col].apply(lambda x: f"{x:.1f}%")
df_tab_fmt["Total"] = df_tab_fmt["Total"].apply(lambda x: f"{int(x):,}".replace(",", "."))

st.dataframe(
    df_tab_fmt,
    use_container_width=True,
    height=420,
    column_config={
        "Município": st.column_config.TextColumn("Município", width="medium"),
        "Região":    st.column_config.TextColumn("Região",    width="medium"),
        "Total":     st.column_config.TextColumn("Total",     width="small"),
    },
)

# Botão de download
sufixo_csv = "_pbf" if use_pbf else "_total"
csv = df_tab.to_csv(index=False, decimal=",", sep=";").encode("utf-8-sig")
st.download_button(
    label="⬇️ Baixar tabela como CSV",
    data=csv,
    file_name=f"pbf_{fase.replace(' ', '_')}_{ano_ref}{sufixo_csv}.csv",
    mime="text/csv",
)


