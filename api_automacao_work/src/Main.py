import streamlit as st
from etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")

st.title("📊 Dashboard Mercado Livre")

# puxar dados
df = buscar_dados()

st.write(df)

# proteção geral
if df is None or df.empty:
    st.warning("Nenhum dado retornado da API")
    st.stop()

# métricas
col1, col2 = st.columns(2)

col1.metric("Total Produtos", len(df))
col2.metric("Faturamento Total", f"R$ {df['Faturamento'].sum():.2f}")

st.dataframe(df)

# gráfico seguro
if {"Produto", "Quantidade"}.issubset(df.columns):
    st.bar_chart(df.set_index("Produto")["Quantidade"])
else:
    st.warning("Sem dados para gráfico")

# excel opcional
if st.button("Gerar Excel"):
    arquivo = exportar_excel(df)
    st.success("Excel gerado com sucesso!")
