import streamlit as st
from etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")

st.title("📊 Dashboard Mercado Livre - Real")

df = buscar_dados()

# 🔐 segurança
if df.empty:
    st.warning("Nenhum dado encontrado")
    st.stop()

# ======================
# MÉTRICAS REAIS
# ======================
col1, col2 = st.columns(2)

col1.metric("Total Pedidos", df["Pedido"].nunique())
col2.metric("Faturamento Real", f"R$ {df['Faturamento'].sum():.2f}")

st.dataframe(df)

# ======================
# 📅 FILTRO VISUAL BR
# ======================
st.subheader("📊 Faturamento por Data")

grafico = df.groupby("Data")["Faturamento"].sum()
st.line_chart(grafico)

# ======================
# 📆 MÊS / ANO REAL
# ======================
st.subheader("📆 Por Mês")

st.bar_chart(df.groupby("Mes")["Faturamento"].sum())

st.subheader("🗓 Por Ano (2022 até hoje)")

st.bar_chart(df.groupby("Ano")["Faturamento"].sum())

# ======================
# EXCEL REAL
# ======================
arquivo = exportar_excel(df)

with open(arquivo, "rb") as file:
    st.download_button(
        "📥 Baixar Excel",
        file,
        file_name="vendas_reais.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )