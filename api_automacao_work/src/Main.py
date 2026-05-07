import streamlit as st
from src.etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")

st.title("📊 Dashboard Mercado Livre - Análise Temporal")

df = buscar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado")
    st.stop()

st.dataframe(df)

# =========================
# MÉTRICAS GERAIS
# =========================
col1, col2 = st.columns(2)

col1.metric("Total Vendas", len(df))
col2.metric("Faturamento Total", f"R$ {df['Faturamento'].sum():.2f}")

# =========================
# 📅 POR DIA
# =========================
st.subheader("📅 Faturamento por Dia")

dia = df.groupby("Dia")["Faturamento"].sum()
st.line_chart(dia)

# =========================
# 📆 POR MÊS
# =========================
st.subheader("📆 Faturamento por Mês")

mes = df.groupby("Mes")["Faturamento"].sum()
st.bar_chart(mes)

# =========================
# 🗓 POR ANO
# =========================
st.subheader("🗓 Faturamento por Ano")

ano = df.groupby("Ano")["Faturamento"].sum()
st.bar_chart(ano)

# =========================
# 🧾 ITENS VENDIDOS
# =========================
st.subheader("📦 Produtos mais vendidos")

prod = df.groupby("Produto")["Quantidade"].sum().sort_values(ascending=False).head(10)
st.bar_chart(prod)

# =========================
# EXCEL
# =========================
arquivo = exportar_excel(df)

with open(arquivo, "rb") as file:
    st.download_button(
        "📥 Baixar Excel",
        file,
        file_name="vendas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )