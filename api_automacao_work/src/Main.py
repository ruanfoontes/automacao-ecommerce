import streamlit as st
from etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")

st.title("📊 Dashboard Mercado Livre")

ACCESS_TOKEN = st.secrets.get("ACCESS_TOKEN")
USER_ID = st.secrets.get("USER_ID")

st.write("DEBUG TOKEN:", ACCESS_TOKEN)
st.write("DEBUG USER:", USER_ID)

if not ACCESS_TOKEN or not USER_ID:
    st.error("Secrets não configurados no Streamlit Cloud")
    st.stop()

df = buscar_dados(ACCESS_TOKEN, USER_ID)

if df is None or df.empty:
    st.warning("Nenhum dado retornado da API")
    st.stop()

col1, col2 = st.columns(2)

col1.metric("Total Produtos", len(df))
col2.metric("Faturamento Total", f"R$ {df['Faturamento'].sum():.2f}")

st.dataframe(df)

if {"Produto", "Quantidade"}.issubset(df.columns):
    st.bar_chart(df.set_index("Produto")["Quantidade"])

if st.button("Gerar Excel"):
    arquivo = exportar_excel(df)
    st.success(f"Excel gerado: {arquivo}")