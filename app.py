import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# Configuração da página
st.set_page_config(page_title="Painel Nutricional Tocantins", layout="wide")

st.title("📊 Painel Interativo: Vigilância Alimentar e Nutricional")
st.markdown("Analise os índices de saúde por município e região.")

# Carregar os dados
@st.cache_data # Isso faz o site carregar muito mais rápido
def load_data():
    df = pd.read_excel('C:/Users/walte/Documents/SISVAN/Banco Geral + PBF 0-5 Anos.xlsx')
    return df

df = load_data()

# --- BARRA LATERAL (Filtros) ---
st.sidebar.header("Filtros de Pesquisa")
regiao_selecionada = st.sidebar.selectbox("Selecione a Região de Saúde", df['REGIÃO DE SAÚDE'].unique())

# Filtrar o DataFrame com base na região
df_filtrado = df[df['REGIÃO DE SAÚDE'] == regiao_selecionada]

municipio_selecionado = st.sidebar.selectbox("Selecione o Município", df_filtrado['MUNICIPIO'].unique())
df_municipio = df_filtrado[df_filtrado['MUNICIPIO'] == municipio_selecionado]

# --- PAINEL PRINCIPAL ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"Evolução: {municipio_selecionado}")
    # Gráfico de evolução da Obesidade (O2)
    fig, ax = plt.subplots()
    sns.lineplot(data=df_municipio, x='Ano', y='O2', marker='o', ax=ax, color='teal')
    ax.set_title("Evolução do Índice de Obesidade (O2)")
    st.pyplot(fig)

with col2:
    st.subheader("Comparativo Regional")
    # Comparar o município selecionado com a média da sua região
    media_regiao = df_filtrado.groupby('Ano')['O2'].mean().reset_index()

    fig2, ax2 = plt.subplots()
    sns.lineplot(data=media_regiao, x='Ano', y='O2', label='Média da Região', linestyle='--', ax=ax2)
    sns.lineplot(data=df_municipio, x='Ano', y='O2', label=municipio_selecionado, linewidth=3, ax=ax2)
    ax2.set_title("Município vs. Média da Região")
    st.pyplot(fig2)

st.divider()
st.write("### Dados Detalhados do Município", df_municipio)
