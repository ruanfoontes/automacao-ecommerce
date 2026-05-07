import streamlit as st
from src.etl import buscar_dados
from src.etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")

st.title("📊 Dashboard Mercado Livre")

df = buscar_dados()

col1, col2 = st.columns(2)

col1.metric("Total Produtos", len(df))
col2.metric("Faturamento Total", f"R$ {df['Faturamento'].sum():.2f}")

st.dataframe(df)

st.bar_chart(df.set_index("Produto")["Quantidade"])

df = buscar_dados()

#Exportar automaticamente
arquivo = exportar_excel(df)

st.success(f"Excel gerado: {arquivo}")
