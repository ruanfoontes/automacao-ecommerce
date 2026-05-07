import streamlit as st
from etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")

st.title("📊 Dashboard Mercado Livre")

df = buscar_dados()

# segurança
if df.empty:
    st.warning("Nenhum dado retornado da API")
    st.stop()

st.write(df)

col1, col2 = st.columns(2)

col1.metric("Total Produtos", len(df))
col2.metric("Faturamento Total", f"R$ {df['Faturamento'].sum():.2f}")

st.dataframe(df)

# gráfico seguro
if {"Produto", "Quantidade"}.issubset(df.columns):
    st.bar_chart(df.set_index("Produto")["Quantidade"])
else:
    st.warning("Colunas do gráfico não encontradas")

# Excel
if st.button("Gerar Excel"):
    arquivo = exportar_excel(df)
    st.success("Excel gerado com sucesso!")
