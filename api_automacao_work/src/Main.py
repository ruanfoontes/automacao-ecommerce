import streamlit as st
from etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")

st.title("📊 Dashboard Mercado Livre")

# ========================
# DADOS
# ========================
df = buscar_dados()

if df.empty:
    st.warning("Nenhum dado retornado da API")
    st.stop()

st.write("📌 Dados brutos")
st.dataframe(df)

# ========================
# MÉTRICAS GERAIS
# ========================
col1, col2 = st.columns(2)

col1.metric("Total Linhas (Produto x Plataforma)", len(df))
col2.metric("Faturamento Total", f"R$ {df['Faturamento'].sum():.2f}")

# ========================
# POR PLATAFORMA
# ========================
st.subheader("📦 Faturamento por Plataforma")

st.bar_chart(df.groupby("Plataforma")["Faturamento"].sum())

# ========================
# ITENS VENDIDOS
# ========================
st.subheader("📊 Quantidade por Produto")

st.bar_chart(df.groupby("Produto")["Quantidade"].sum())

# ========================
# TOP PRODUTOS
# ========================
st.subheader("🔥 Top Produtos")

top = df.groupby("Produto")["Quantidade"].sum().sort_values(ascending=False).head(10)
st.bar_chart(top)

# ========================
# EXCEL DOWNLOAD (CLOUD)
# ========================
arquivo = exportar_excel(df)

with open(arquivo, "rb") as file:
    st.download_button(
        label="📥 Baixar Excel",
        data=file,
        file_name="vendas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )