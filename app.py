# =============================================================================
#  Dashboard Vigilância Nutricional · PBF Tocantins — Streamlit (Multi-página)
#  Programa Bolsa Família · SISVAN · 2019–2025
# =============================================================================
#  Instalar:
#      pip install streamlit plotly pandas openpyxl requests scipy
#
#  Rodar:
#      streamlit run app.py
# =============================================================================

import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import requests
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

st.markdown("""
<style>
    /* Fundo geral */
    .stApp { background-color: #06101e; }
    section[data-testid="stSidebar"] { background-color: #0d1b2e; border-right: 1px solid #1e3350; }

    /* Textos */
    html, body, [class*="css"] { color: #000000; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #e2eaf4 !important; }
    label, .stSelectbox label, .stMultiSelect label, .stRadio label {
        color: #7a99b8 !important; font-size: 0.75rem !important;
        text-transform: uppercase; letter-spacing: 0.06em;
    }

    /* Cards de métricas */
    [data-testid="metric-container"] {
        background-color: #e2eaf4;
        border: 1px solid #1e3350;
        border-radius: 10px;
        padding: 16px 20px;
    }
    [data-testid="stMetricValue"] { color: #00d4aa; font-weight: 800; }
    [data-testid="stMetricLabel"] { color: #7a99b8; font-size: 0.7rem; }

    /* Dropdowns */
    .stSelectbox > div > div {
        background-color: #111f33 !important;
        border: 1px solid #1e3350 !important;
        color: #e2eaf4 !important;
    }

    /* Dividers */
    hr { border-color: #1e3350; }

    /* Tabela */
    .dataframe { background-color: #111f33 !important; color: #e2eaf4 !important; }
    thead tr th { background-color: #162540 !important; color: #7a99b8 !important; font-size: 0.72rem !important; }

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

    /* Navegação — rótulo do grupo */
    .nav-label {
        color: #4a6a88;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.10em;
        font-weight: 700;
        margin: 6px 0 4px 4px;
    }

    /* Botão de navegação ativo */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #00d4aa22 !important;
        border: 1px solid #00d4aa !important;
        color: #00d4aa !important;
        font-weight: 700;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #1e3350 !important;
        color: #7a99b8 !important;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #00d4aa88 !important;
        color: #000000 !important;
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
    candidatas = [
        Path.cwd() / "data",
        Path.cwd(),
        Path(__file__).resolve().parent / "data",
        Path(__file__).resolve().parent,
    ]
    for pasta in candidatas:
        if pasta.exists() and list(pasta.glob("Banco*PBF*.xlsx")):
            return pasta
    return Path.cwd() / "data"

_pasta_data = _encontrar_pasta_data()
ARQUIVOS    = {fase: _pasta_data / nome for fase, nome in NOMES_ARQUIVOS.items()}

_faltando = [str(p) for p in ARQUIVOS.values() if not p.exists()]
if _faltando:
    st.error("### ❌ Arquivos de dados não encontrados")
    st.markdown(f"""
Verifique se as planilhas estão em uma subpasta `data/` ao lado do `app.py`:
```
seu-projeto/
├── app.py
└── data/
    ├── Banco Geral + PBF 0-5 Anos.xlsx
    ├── ...
```
**Pasta onde o dashboard procurou:** `{_pasta_data}`
""")
    for p in _faltando:
        st.code(p)
    st.stop()

# =============================================================================
# DICIONÁRIO DE INDICADORES
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
        "baixo_peso":   {"cols_n": ["BP"],    "cols_pct": ["BP%"],    "label": "Baixo Peso",         "grupo": "magreza"},
        "eutrofia":     {"cols_n": ["E"],     "cols_pct": ["E%"],     "label": "Eutrofia",            "grupo": "eutrofia"},
        "sobrepeso":    {"cols_n": ["S"],     "cols_pct": ["S%"],     "label": "Sobrepeso",           "grupo": "sobrepeso"},
        "obesidade_g1": {"cols_n": ["OGI"],  "cols_pct": ["OGI%"],  "label": "Obesidade Grau I",    "grupo": "sobrepeso"},
        "obesidade_g2": {"cols_n": ["OGII"], "cols_pct": ["OGII%"], "label": "Obesidade Grau II",   "grupo": "sobrepeso"},
        "obesidade_g3": {"cols_n": ["OGIII"],"cols_pct": ["OGIII%"],"label": "Obesidade Grau III",  "grupo": "sobrepeso"},
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
    paper_bgcolor="#000000",
    plot_bgcolor="#ffffff",
    font=dict(color="#000000", family="Inter, sans-serif", size=12),
    margin=dict(t=50, b=40, l=60, r=20),
    xaxis=dict(gridcolor="#1e3350", linecolor="#1e3350", zerolinecolor="#1e3350"),
    yaxis=dict(gridcolor="#1e3350", linecolor="#1e3350", zerolinecolor="#1e3350"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#000000", font=dict(size=11)),
    hoverlabel=dict(bgcolor="#000000", font_color="#000000", bordercolor="#000000"),
)

PALETA = ["#10b981","#f43f5e","#f59e0b","#ef4444","#818cf8",
          "#0891b2","#db2777","#65a30d","#d97706","#a855f7","#059669","#dc2626"]

# =============================================================================
# PÁGINAS — definição
# =============================================================================

PAGINAS = {
    "visao_geral":    ("🏠", "Visão Geral"),
    "serie_temporal": ("📈", "Série Temporal"),
    "heatmap":        ("🌡", "Heatmap Municipal"),
    "mapa":           ("🗺️", "Mapa Coroplético"),
    "rankings":       ("🏆", "Rankings"),
    "correlacao":     ("🔗", "Correlações"),
    "tabela":         ("📋", "Tabela de Dados"),
}

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "visao_geral"

# =============================================================================
# CARREGAMENTO DOS DADOS
# =============================================================================

@st.cache_data(show_spinner="Carregando planilhas...")
def carregar_dados():
    dfs = {}
    for fase, path in ARQUIVOS.items():
        df = pd.read_excel(path).fillna(0)
        df["REGIÃO DE SAÚDE"] = df["REGIÃO DE SAÚDE"].astype(str).str.strip()
        df["MUNICIPIO"]       = df["MUNICIPIO"].astype(str).str.strip()
        dfs[fase] = df
    return dfs

@st.cache_data(show_spinner="Carregando mapa do IBGE...")
def carregar_geojson_tocantins():
    """
    Baixa o GeoJSON dos municípios do Tocantins via API do IBGE.
    Mantém o código de 7 dígitos completo para coincidir com a planilha.
    """
    url = (
        "https://servicodados.ibge.gov.br/api/v3/malhas/estados/17"
        "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio"
    )
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        geojson = resp.json()
        for feat in geojson["features"]:
            cod = str(feat["properties"].get("codarea", "")).strip()
            # ── CORREÇÃO: usa os 7 dígitos completos ──
            feat["id"] = int(cod) if cod.isdigit() else None
        return geojson
    except Exception:
        return None

DFS       = carregar_dados()
MUNICIPIOS = sorted(DFS["0-5 Anos"]["MUNICIPIO"].unique().tolist())
ANOS       = sorted(DFS["0-5 Anos"]["Ano"].unique().tolist())
REGIOES    = sorted(DFS["0-5 Anos"]["REGIÃO DE SAÚDE"].unique().tolist())

# =============================================================================
# FUNÇÕES DE CÁLCULO
# =============================================================================

def calcular_pct(df, fase, indicador, use_pbf=False):
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

def _add_dual_traces(fig, fase, ind_keys, serie_total, serie_pbf, serie_ativa,
                     shades, comparar):
    for i, k in enumerate(ind_keys):
        cor = shades[i % len(shades)]
        lbl = INDICADORES[fase][k]["label"]
        if comparar:
            fig.add_trace(go.Scatter(
                x=serie_total["Ano"], y=serie_total[k],
                name=f"{lbl} · Total",
                mode="lines+markers",
                line=dict(width=2.5, color=cor),
                marker=dict(size=5),
                legendgroup=k,
            ))
            fig.add_trace(go.Scatter(
                x=serie_pbf["Ano"], y=serie_pbf[k],
                name=f"{lbl} · PBF",
                mode="lines+markers",
                line=dict(width=2, color=cor, dash="dot"),
                marker=dict(size=4, symbol="diamond"),
                legendgroup=k,
            ))
        else:
            r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
            fig.add_trace(go.Scatter(
                x=serie_ativa["Ano"], y=serie_ativa[k],
                name=lbl,
                mode="lines+markers",
                line=dict(width=2.5, color=cor),
                marker=dict(size=5),
                fill="tozeroy" if i == 0 else "none",
                fillcolor=f"rgba({r},{g},{b},0.10)" if i == 0 else "rgba(0,0,0,0)",
            ))

# =============================================================================
# CABEÇALHO PADRÃO
# =============================================================================

def _cabecalho(fase, pagina_label):
    st.markdown(f"""
    <div style='padding:4px 0 12px 0'>
        <h1 style='margin:0;font-size:1.5rem;color:#00d4aa;font-weight:800'>
            📊 Dashboard Vigilância Nutricional · PBF Tocantins
        </h1>
        <p style='color:#7a99b8;font-size:0.78rem;margin:4px 0 0 0;font-family:monospace'>
            Programa Bolsa Família · SISVAN · 2019–2025 · 139 municípios · 8 regiões &nbsp;·&nbsp;
            <span style='color:#00d4aa'>{pagina_label}</span>
        </p>
    </div>""", unsafe_allow_html=True)
    st.markdown(
        f"<div class='info-box'><strong>Fase: {fase}</strong> — {FASE_DESCRICAO[fase]}</div>",
        unsafe_allow_html=True,
    )

# =============================================================================
# PÁGINA 1 — VISÃO GERAL (KPIs)
# =============================================================================

def pagina_visao_geral(fase, df_f, inds_fase, ano_ref, use_pbf, comparar, escopo_label):
    _cabecalho(fase, "🏠 Visão Geral")
    st.markdown(f"<div class='section-header'>📌 Indicadores — {ano_ref} · {escopo_label}</div>",
                unsafe_allow_html=True)

    df_ano        = df_f[df_f["Ano"] == ano_ref]
    total_ano_all = int(df_ano["TOTAL"].sum())
    total_ano_pbf = int(df_ano["TOTAL_PBF"].sum())
    kpi_keys      = list(inds_fase.keys())

    cols0 = st.columns(3 if comparar else 2)
    with cols0[0]:
        st.metric("👥 Total Avaliados (Geral)", f"{total_ano_all:,}".replace(",", "."))
    with cols0[1]:
        st.metric("🎯 Total Avaliados (PBF)", f"{total_ano_pbf:,}".replace(",", "."))
    if comparar:
        with cols0[2]:
            cob = round(total_ano_pbf / total_ano_all * 100, 1) if total_ano_all else 0
            st.metric("📊 Cobertura PBF", f"{cob:.1f}%")

    st.markdown("")

    if comparar:
        for k in kpi_keys:
            vt  = calcular_pct(df_ano, fase, k, False)
            vp  = calcular_pct(df_ano, fase, k, True)
            dlt = round(vp - vt, 1)
            lbl = inds_fase[k]["label"]
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(f"📊 {lbl} · Total", f"{vt:.1f}%")
            with c2:
                st.metric(f"🎯 {lbl} · PBF",   f"{vp:.1f}%")
            with c3:
                cor = "🔴" if dlt > 0.5 else ("🟢" if dlt < -0.5 else "🟡")
                st.metric(f"{cor} Diferença (PBF − Total)", f"{dlt:+.1f} p.p.")
    else:
        cols1 = st.columns(min(len(kpi_keys), 4))
        for i, k in enumerate(kpi_keys[:4]):
            with cols1[i]:
                st.metric(inds_fase[k]["label"],
                          f"{calcular_pct(df_ano, fase, k, use_pbf):.1f}%")
        if len(kpi_keys) > 4:
            restantes = kpi_keys[4:]
            cols2 = st.columns(min(len(restantes), 4))
            for i, k in enumerate(restantes[:4]):
                with cols2[i]:
                    st.metric(inds_fase[k]["label"],
                              f"{calcular_pct(df_ano, fase, k, use_pbf):.1f}%")

# =============================================================================
# PÁGINA 2 — SÉRIE TEMPORAL
# =============================================================================

def pagina_serie_temporal(fase, df_f, inds_fase, use_pbf, comparar, escopo_label):
    _cabecalho(fase, "📈 Série Temporal")
    subtit = " · Somente PBF" if use_pbf else (" · Total vs PBF" if comparar else " · Total")
    st.markdown(f"<div class='section-header'>📈 Evolução Histórica — {escopo_label}{subtit}</div>",
                unsafe_allow_html=True)

    serie_ativa = serie_temporal(df_f, fase, use_pbf=use_pbf)
    serie_all   = serie_temporal(df_f, fase, use_pbf=False)
    serie_pbf   = serie_temporal(df_f, fase, use_pbf=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure(layout=PLOTLY_BASE)
        fig.update_layout(
            title=dict(text="📉 Magreza / Baixo Peso", font=dict(color="#000000", size=13)),
            height=340,
            legend=dict(orientation="h", y=-0.32, font=dict(size=10)) if comparar else {},
        )
        inds_m = [k for k, v in inds_fase.items() if v["grupo"] == "magreza"]
        _add_dual_traces(fig, fase, inds_m, serie_all, serie_pbf, serie_ativa,
                         ["#f43f5e","#fb7185","#fda4af","#fecdd3"], comparar)
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = go.Figure(layout=PLOTLY_BASE)
        fig.update_layout(
            title=dict(text="📈 Sobrepeso & Obesidade", font=dict(color="#000000", size=13)),
            height=340,
            legend=dict(orientation="h", y=-0.32, font=dict(size=10)) if comparar else {},
        )
        inds_s = [k for k, v in inds_fase.items() if v["grupo"] == "sobrepeso"]
        _add_dual_traces(fig, fase, inds_s, serie_all, serie_pbf, serie_ativa,
                         ["#f59e0b","#ef4444","#dc2626","#a855f7","#7c3aed"], comparar)
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Distribuição completa
    fig_d = go.Figure(layout=PLOTLY_BASE)
    fig_d.update_layout(
        title=dict(text=f"📊 Distribuição Nutricional Completa{subtit}",
                   font=dict(color="#000000", size=13)),
        barmode="group", height=400,
        legend=dict(orientation="h", y=-0.28, font=dict(size=10)),
        margin=dict(t=50, b=90, l=60, r=20),
    )
    for i, (k, v) in enumerate(inds_fase.items()):
        cor = PALETA[i % len(PALETA)]
        if comparar:
            fig_d.add_trace(go.Bar(x=serie_all["Ano"], y=serie_all[k],
                                   name=f"{v['label']} · Total",
                                   marker_color=cor + "88", marker_line_color=cor,
                                   marker_line_width=1, legendgroup=k))
            fig_d.add_trace(go.Bar(x=serie_pbf["Ano"], y=serie_pbf[k],
                                   name=f"{v['label']} · PBF",
                                   marker_color=cor, marker_line_color=cor,
                                   marker_line_width=1, legendgroup=k))
        else:
            fig_d.add_trace(go.Bar(x=serie_ativa["Ano"], y=serie_ativa[k],
                                   name=v["label"], marker_color=cor))
    fig_d.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig_d, use_container_width=True)

# =============================================================================
# PÁGINA 3 — HEATMAP MUNICIPAL
# =============================================================================

def pagina_heatmap(fase, df_atual, inds_fase, hm_key, ano_ref, regiao, use_pbf):
    _cabecalho(fase, "🌡 Heatmap Municipal")
    recorte = " · PBF" if use_pbf else " · Total"
    st.markdown(
        f"<div class='section-header'>🌡 Heatmap por Município — "
        f"{inds_fase[hm_key]['label']}{recorte} ({ano_ref})</div>",
        unsafe_allow_html=True,
    )

    df_base = df_atual.copy()
    if regiao != "Todas as Regiões":
        df_base = df_base[df_base["REGIÃO DE SAÚDE"] == regiao]
    df_ano = df_base[df_base["Ano"] == ano_ref]

    total_col = "TOTAL_PBF" if use_pbf else "TOTAL"
    rows = []
    for mun, grp in df_ano.groupby("MUNICIPIO"):
        rows.append({
            "MUNICIPIO": mun,
            "REGIÃO":    grp["REGIÃO DE SAÚDE"].iloc[0],
            "Total":     int(grp[total_col].sum()),
            hm_key:      calcular_pct(grp, fase, hm_key, use_pbf),
        })
    df_hm = pd.DataFrame(rows).sort_values(hm_key, ascending=True)

    grupo = inds_fase[hm_key]["grupo"]
    colorscales = {
        "eutrofia":  [[0,"#1e3350"],[0.5,"#059669"],[1,"#10b981"]],
        "magreza":   [[0,"#1e3350"],[0.5,"#f87171"],[1,"#f43f5e"]],
        "sobrepeso": [[0,"#1e3350"],[0.5,"#fbbf24"],[1,"#f59e0b"]],
        "estatura":  [[0,"#1e3350"],[0.5,"#818cf8"],[1,"#6366f1"]],
    }
    cs = colorscales.get(grupo, [[0,"#1e3350"],[0.5,"#60a5fa"],[1,"#3b82f6"]])

    fig = go.Figure(layout=PLOTLY_BASE)
    fig.update_layout(
        height=max(500, len(df_hm) * 19),
        margin=dict(t=30, b=20, l=170, r=110),
        yaxis=dict(tickfont=dict(size=9.5)),
    )
    fig.add_trace(go.Bar(
        x=df_hm[hm_key], y=df_hm["MUNICIPIO"],
        orientation="h",
        marker=dict(color=df_hm[hm_key], colorscale=cs, showscale=True,
                    colorbar=dict(title="%", ticksuffix="%",
                                  tickfont=dict(color="#7a99b8"),
                                  title_font=dict(color="#7a99b8"),
                                  bgcolor="#111f33", bordercolor="#1e3350")),
        customdata=df_hm[["REGIÃO","Total"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"{inds_fase[hm_key]['label']}: %{{x:.1f}}%<br>"
            "Região: %{customdata[0]}<br>"
            "Total: %{customdata[1]:,}<extra></extra>"
        ),
    ))
    fig.update_xaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# PÁGINA 4 — MAPA COROPLÉTICO
# =============================================================================

def pagina_mapa(fase, df_atual, inds_fase, mapa_key, ano_ref, regiao, use_pbf):
    _cabecalho(fase, "🗺️ Mapa Coroplético")
    recorte = " · PBF" if use_pbf else " · Total"
    st.markdown(
        f"<div class='section-header'>🗺️ Mapa Coroplético — "
        f"{inds_fase[mapa_key]['label']}{recorte} ({ano_ref})</div>",
        unsafe_allow_html=True,
    )

    geojson = carregar_geojson_tocantins()
    if geojson is None:
        st.warning("⚠️ Não foi possível carregar o GeoJSON do IBGE. Verifique sua conexão.", icon="🌐")
        return

    df_base = df_atual[df_atual["Ano"] == ano_ref].copy()
    if regiao != "Todas as Regiões":
        df_base = df_base[df_base["REGIÃO DE SAÚDE"] == regiao]

    total_col = "TOTAL_PBF" if use_pbf else "TOTAL"
    rows = []
    for mun, grp in df_base.groupby("MUNICIPIO"):
        # Código IBGE com 7 dígitos — coincide com feat["id"] no GeoJSON
        codigo = int(str(grp["Código IBGE"].iloc[0]).strip())
        rows.append({
            "MUNICIPIO":   mun,
            "codigo_ibge": codigo,
            "REGIÃO":      grp["REGIÃO DE SAÚDE"].iloc[0],
            "Total":       int(grp[total_col].sum()),
            "valor":       calcular_pct(grp, fase, mapa_key, use_pbf),
        })
    df_mapa = pd.DataFrame(rows)

    grupo = inds_fase[mapa_key]["grupo"]
    cs_mapa = {
        "eutrofia":  [[0,"#0d2a1a"],[0.5,"#059669"],[1,"#10b981"]],
        "magreza":   [[0,"#1a0d0d"],[0.5,"#dc2626"],[1,"#f43f5e"]],
        "sobrepeso": [[0,"#1a1200"],[0.5,"#d97706"],[1,"#f59e0b"]],
        "estatura":  [[0,"#0d0d2a"],[0.5,"#6366f1"],[1,"#818cf8"]],
    }.get(grupo, [[0,"#0d1b2e"],[0.5,"#2563eb"],[1,"#3b82f6"]])

    vmax = float(df_mapa["valor"].quantile(0.95)) if not df_mapa.empty else 100.0

    fig = go.Figure(go.Choroplethmapbox(
        geojson=geojson,
        locations=df_mapa["codigo_ibge"],
        z=df_mapa["valor"],
        featureidkey="id",
        colorscale=cs_mapa,
        zmin=0, zmax=vmax,
        marker_opacity=0.82,
        marker_line_width=0.6,
        marker_line_color="#0d1b2e",
        colorbar=dict(
            title=dict(text="%", font=dict(color="#7a99b8", size=13)),
            ticksuffix="%",
            tickfont=dict(color="#7a99b8", size=11),
            bgcolor="#111f33", bordercolor="#1e3350",
            borderwidth=1, len=0.75, thickness=14,
        ),
        text=df_mapa["MUNICIPIO"],
        customdata=df_mapa[["REGIÃO","Total","MUNICIPIO"]].values,
        hovertemplate=(
            "<b>%{customdata[2]}</b><br>"
            f"<b>{inds_fase[mapa_key]['label']}:</b> %{{z:.1f}}%<br>"
            "<b>Região:</b> %{customdata[0]}<br>"
            "<b>Total avaliados:</b> %{customdata[1]:,}"
            "<extra></extra>"
        ),
    ))
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        mapbox_zoom=5.6,
        mapbox_center={"lat": -10.18, "lon": -48.15},
        height=640,
        paper_bgcolor="#111f33",
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Legenda de regiões
    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;gap:10px;margin-top:6px'>"
        + "".join(
            f"<span style='font-size:0.72rem;font-family:monospace;color:{cor};"
            f"background:rgba(0,0,0,0.3);border:1px solid {cor}44;"
            f"padding:2px 10px;border-radius:12px'>⬤ {reg}</span>"
            for reg, cor in REGIAO_CORES.items()
        )
        + "</div>",
        unsafe_allow_html=True,
    )

# =============================================================================
# PÁGINA 5 — RANKINGS
# =============================================================================

def pagina_rankings(fase, df_atual, inds_fase, regiao, use_pbf):
    _cabecalho(fase, "🏆 Rankings")
    st.markdown(f"<div class='section-header'>🏆 Ranking de Municípios — {max(ANOS)}</div>",
                unsafe_allow_html=True)

    df_base = df_atual[df_atual["Ano"] == max(ANOS)].copy()
    if regiao != "Todas as Regiões":
        df_base = df_base[df_base["REGIÃO DE SAÚDE"] == regiao]

    total_col = "TOTAL_PBF" if use_pbf else "TOTAL"
    rows = []
    for mun, grp in df_base.groupby("MUNICIPIO"):
        row = {"MUNICIPIO": mun, "REGIÃO": grp["REGIÃO DE SAÚDE"].iloc[0],
               "Total": int(grp[total_col].sum())}
        for k in inds_fase:
            row[k] = calcular_pct(grp, fase, k, use_pbf)
        rows.append(row)
    df_rank = pd.DataFrame(rows)

    ind_mag = next((k for k, v in inds_fase.items() if v["grupo"] == "magreza"), None)
    ind_sob = next((k for k, v in inds_fase.items() if v["grupo"] == "sobrepeso"), None)

    col1, col2 = st.columns(2)

    def _bar_ranking(col, key, titulo, cor_titulo):
        if key is None or df_rank.empty:
            return
        top = df_rank.nlargest(15, key).sort_values(key, ascending=True)
        fig = go.Figure(layout=PLOTLY_BASE)
        fig.update_layout(
            title=dict(text=titulo, font=dict(color=cor_titulo, size=12)),
            height=420, margin=dict(t=50, b=20, l=165, r=20),
        )
        fig.add_trace(go.Bar(
            x=top[key],
            y=top["MUNICIPIO"].apply(lambda x: x[:22] + "…" if len(x) > 22 else x),
            orientation="h",
            marker_color=[REGIAO_CORES.get(r, "#94a3b8") for r in top["REGIÃO"]],
            customdata=top[["REGIÃO","Total"]].values,
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<br>%{customdata[0]}<extra></extra>",
        ))
        fig.update_xaxes(ticksuffix="%")
        fig.update_yaxes(tickfont=dict(size=10))
        col.plotly_chart(fig, use_container_width=True)

    _bar_ranking(col1, ind_mag, f"🔴 Top 15 — {inds_fase[ind_mag]['label']}" if ind_mag else "", "#f87171")
    _bar_ranking(col2, ind_sob, f"🟡 Top 15 — {inds_fase[ind_sob]['label']}" if ind_sob else "", "#fbbf24")

    # Legenda de regiões
    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;gap:10px;margin-top:6px'>"
        + "".join(
            f"<span style='font-size:0.72rem;font-family:monospace;color:{cor};"
            f"background:rgba(0,0,0,0.3);border:1px solid {cor}44;"
            f"padding:2px 8px;border-radius:12px'>⬤ {reg}</span>"
            for reg, cor in REGIAO_CORES.items()
        )
        + "</div>",
        unsafe_allow_html=True,
    )

# =============================================================================
# PÁGINA 6 — CORRELAÇÕES
# =============================================================================

def pagina_correlacao(fase, df_atual, inds_fase, regiao, use_pbf, corr_escopo, corr_metodo):
    _cabecalho(fase, "🔗 Correlações")
    recorte = " · PBF" if use_pbf else " · Total"
    st.markdown(
        f"<div class='section-header'>🔗 Correlação entre Indicadores — "
        f"{fase}{recorte} · {corr_metodo}</div>",
        unsafe_allow_html=True,
    )

    df_base = df_atual.copy()
    if regiao != "Todas as Regiões":
        df_base = df_base[df_base["REGIÃO DE SAÚDE"] == regiao]
    df_base = df_base[df_base["Ano"] == int(corr_escopo)]

    obs_rows = []
    for _, grp in df_base.groupby(["MUNICIPIO", "Ano"]):
        row = {}
        for k, v in inds_fase.items():
            row[v["label"]] = calcular_pct(grp, fase, k, use_pbf)
        obs_rows.append(row)

    df_obs = pd.DataFrame(obs_rows).dropna()
    n_obs  = len(df_obs)

    if df_obs.shape[0] < 3 or df_obs.shape[1] < 2:
        st.warning("Dados insuficientes para calcular correlação com os filtros atuais.")
        return

    metodo_str  = "pearson" if corr_metodo == "Pearson" else "spearman"
    corr_matrix = df_obs.corr(method=metodo_str)
    labels      = list(corr_matrix.columns)
    n           = len(labels)
    corr_vals   = corr_matrix.values

    annotations = []
    for i in range(n):
        for j in range(n):
            val = corr_vals[i, j]
            if i == j:
                txt, icone = "1.00", "◼"
            elif val > 0:
                txt, icone = f"+{val:.2f}", "▲"
            elif val < 0:
                txt, icone = f"{val:.2f}", "▼"
            else:
                txt, icone = "0.00", "○"
            annotations.append(dict(
                x=j, y=i,
                text=f"<b>{txt}</b><br><span style='font-size:9px'>{icone}</span>",
                showarrow=False,
                font=dict(color="#000000" if abs(val) > 0.35 else "#7a99b8",
                          size=11, family="IBM Plex Mono, monospace"),
                xref="x", yref="y",
            ))

    colorscale_corr = [
        [0.00,"#7f1d1d"],[0.20,"#dc2626"],[0.35,"#f87171"],
        [0.50,"#162540"],[0.65,"#34d399"],[0.80,"#059669"],[1.00,"#064e3b"],
    ]

    BASE = {k: v for k, v in PLOTLY_BASE.items() if k not in ("xaxis","yaxis","margin")}
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=corr_vals, x=labels, y=labels,
        zmin=-1, zmax=1, zmid=0,
        colorscale=colorscale_corr,
        showscale=True,
        colorbar=dict(
            title=dict(text="r", font=dict(color="#7a99b8", size=13)),
            tickvals=[-1,-.75,-.5,-.25,0,.25,.5,.75,1],
            ticktext=["-1.00","-0.75","-0.50","-0.25","0","+0.25","+0.50","+0.75","+1.00"],
            tickfont=dict(color="#7a99b8", size=10),
            bgcolor="#111f33", bordercolor="#1e3350",
            borderwidth=1, len=0.9, thickness=14,
        ),
        hovertemplate="<b>%{y}</b><br>× <b>%{x}</b><br>Correlação: <b>%{z:.3f}</b><extra></extra>",
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        **BASE,
        height=max(480, n * 58),
        annotations=annotations,
        margin=dict(t=30, b=120, l=180, r=100),
    )
    fig.update_xaxes(tickangle=-35, tickfont=dict(size=10.5, color="#e2eaf4"),
                     showgrid=False, side="bottom", linecolor="#1e3350")
    fig.update_yaxes(tickfont=dict(size=10.5, color="#e2eaf4"),
                     showgrid=False, autorange="reversed", linecolor="#1e3350")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div style='display:flex;flex-wrap:wrap;gap:16px;margin-top:4px;
                font-size:0.72rem;font-family:IBM Plex Mono,monospace;color:#7a99b8'>
        <span>▲ <b style='color:#34d399'>positiva</b> — indicadores sobem juntos</span>
        <span>▼ <b style='color:#f87171'>negativa</b> — um sobe quando o outro desce</span>
        <span>○ <b style='color:#94a3b8'>nula</b> — sem relação linear</span>
        <span style='color:#4a6a88'>
            Método: {corr_metodo} &nbsp;|&nbsp; n = {n_obs} observações &nbsp;|&nbsp;
            Recorte: {'PBF' if use_pbf else 'Total'} &nbsp;|&nbsp; Ano: {corr_escopo}
        </span>
    </div>""", unsafe_allow_html=True)

# =============================================================================
# PÁGINA 7 — TABELA DE DADOS
# =============================================================================

def pagina_tabela(fase, df_f, inds_fase, ano_ref, use_pbf, comparar):
    _cabecalho(fase, "📋 Tabela de Dados")
    modo  = "Beneficiários PBF" if use_pbf else ("Total vs PBF" if comparar else "Todos os Avaliados")
    st.markdown(f"<div class='section-header'>📋 Tabela Detalhada — {fase} · {ano_ref} · {modo}</div>",
                unsafe_allow_html=True)

    df_tab     = tabela_municipios(df_f, fase, ano_ref, use_pbf=use_pbf)
    df_fmt     = df_tab.copy()
    cols_pct   = [v["label"] for v in inds_fase.values()]
    for col in cols_pct:
        if col in df_fmt.columns:
            df_fmt[col] = df_fmt[col].apply(lambda x: f"{x:.1f}%")
    df_fmt["Total"] = df_fmt["Total"].apply(lambda x: f"{int(x):,}".replace(",", "."))

    st.dataframe(
        df_fmt, use_container_width=True, height=460,
        column_config={
            "Município": st.column_config.TextColumn("Município", width="medium"),
            "Região":    st.column_config.TextColumn("Região",    width="medium"),
            "Total":     st.column_config.TextColumn("Total",     width="small"),
        },
    )

    sufixo = "_pbf" if use_pbf else "_total"
    csv    = df_tab.to_csv(index=False, decimal=",", sep=";").encode("utf-8-sig")
    st.download_button(
        label="⬇️ Baixar tabela como CSV",
        data=csv,
        file_name=f"pbf_{fase.replace(' ','_')}_{ano_ref}{sufixo}.csv",
        mime="text/csv",
    )

# =============================================================================
# SIDEBAR — NAVEGAÇÃO + FILTROS
# =============================================================================

with st.sidebar:

    # ── Navegação ─────────────────────────────────────────────────────────────
    st.markdown("<div class='nav-label'>Navegação</div>", unsafe_allow_html=True)
    pagina_atual = st.session_state["pagina"]

    for pkey, (emoji, plabel) in PAGINAS.items():
        tipo = "primary" if pkey == pagina_atual else "secondary"
        if st.button(f"{emoji}  {plabel}", key=f"nav_{pkey}",
                     use_container_width=True, type=tipo):
            st.session_state["pagina"] = pkey
            st.rerun()

    st.markdown("---")

    # ── Filtros comuns ─────────────────────────────────────────────────────────
    st.markdown("<div class='nav-label'>Filtros</div>", unsafe_allow_html=True)

    fase = st.selectbox("🧒 Fase da Vida", list(ARQUIVOS.keys()))

    regiao_opcoes = ["Todas as Regiões"] + REGIOES
    regiao = st.selectbox("🗺 Região de Saúde", regiao_opcoes)

    df_atual = DFS[fase]
    if regiao != "Todas as Regiões":
        muns_disp = sorted(df_atual[df_atual["REGIÃO DE SAÚDE"] == regiao]["MUNICIPIO"].unique())
    else:
        muns_disp = MUNICIPIOS

    municipio = st.selectbox("🏙 Município", ["Todo o Estado (Tocantins)"] + muns_disp)
    ano_ref   = st.selectbox("📅 Ano de Referência", list(reversed(ANOS)))

    inds_fase = INDICADORES[fase]
    ind_labels = {k: v["label"] for k, v in inds_fase.items()}

    st.markdown("---")

    # ── Recorte PBF (todas as páginas) ────────────────────────────────────────
    pbf_modo = st.radio(
        "👁 Recorte populacional",
        ["Total (todos avaliados)", "Somente Beneficiários PBF", "Comparar Total vs PBF"],
        index=0,
        help=(
            "**Total** — todos os avaliados.\n\n"
            "**Somente PBF** — apenas beneficiários PBF.\n\n"
            "**Comparar** — exibe as duas séries sobrepostas."
        ),
    )
    use_pbf  = pbf_modo == "Somente Beneficiários PBF"
    comparar = pbf_modo == "Comparar Total vs PBF"

    # ── Indicador — sempre visível (Heatmap e Mapa usam este valor) ──────────
    st.markdown("---")
    st.markdown("<div class='nav-label'>Indicador visualizado</div>", unsafe_allow_html=True)
    indicador_sel = st.selectbox(
        "🎯 Indicador",
        list(ind_labels.keys()),
        format_func=lambda k: ind_labels[k],
        key="indicador_global",
        help="Usado no Heatmap Municipal, no Mapa Coroplético e no destaque do Ranking.",
    )
    hm_key   = indicador_sel
    mapa_key = indicador_sel

    # ── Filtros extras de Correlação (só quando relevante, mas sempre acessíveis) ──
    st.markdown("---")
    st.markdown("<div class='nav-label'>Correlação</div>", unsafe_allow_html=True)
    corr_escopo = st.selectbox(
        "📅 Ano (correlação)",
        [str(a) for a in sorted(ANOS, reverse=True)],
        key="corr_ano",
    )
    corr_metodo = st.radio(
        "Método",
        ["Pearson", "Spearman"],
        horizontal=True,
        key="corr_met",
        help="**Pearson** — correlação linear.\n\n**Spearman** — por postos, mais robusto a outliers.",
    )

    # atualiza referência da página corrente após possível st.rerun()
    pagina_atual = st.session_state["pagina"]

    st.markdown("---")
    st.markdown(
        "<small style='color:#4a6a88'>PBF · SISVAN · 2019–2025<br>"
        "139 municípios · 8 regiões</small>",
        unsafe_allow_html=True,
    )

# =============================================================================
# FILTRO GLOBAL DO DATAFRAME
# =============================================================================

df_f = df_atual.copy()
if regiao != "Todas as Regiões":
    df_f = df_f[df_f["REGIÃO DE SAÚDE"] == regiao]
if municipio != "Todo o Estado (Tocantins)":
    df_f = df_f[df_f["MUNICIPIO"] == municipio]

escopo_label = (
    municipio if municipio != "Todo o Estado (Tocantins)"
    else (regiao if regiao != "Todas as Regiões" else "Tocantins (Estado)")
)

# =============================================================================
# ROTEAMENTO DE PÁGINAS
# =============================================================================

p = st.session_state["pagina"]

if p == "visao_geral":
    pagina_visao_geral(fase, df_f, inds_fase, ano_ref, use_pbf, comparar, escopo_label)

elif p == "serie_temporal":
    pagina_serie_temporal(fase, df_f, inds_fase, use_pbf, comparar, escopo_label)

elif p == "heatmap":
    pagina_heatmap(fase, df_atual, inds_fase, hm_key, ano_ref, regiao, use_pbf)

elif p == "mapa":
    pagina_mapa(fase, df_atual, inds_fase, mapa_key, ano_ref, regiao, use_pbf)

elif p == "rankings":
    pagina_rankings(fase, df_atual, inds_fase, regiao, use_pbf)

elif p == "correlacao":
    pagina_correlacao(fase, df_atual, inds_fase, regiao, use_pbf, corr_escopo, corr_metodo)

elif p == "tabela":
    pagina_tabela(fase, df_f, inds_fase, ano_ref, use_pbf, comparar)
