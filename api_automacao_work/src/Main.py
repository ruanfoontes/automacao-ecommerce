import streamlit as st
import pandas as pd
import os
from etl import buscar_dados, exportar_excel

st.set_page_config(page_title="Dashboard Ecommerce", layout="wide")
st.title("📊 Dashboard Mercado Livre - Real")

df = buscar_dados()

st.write(f"Token configurado: {'Sim' if os.getenv('ACCESS_TOKEN') else 'Não'}")
st.write(f"Linhas encontradas no DataFrame: {len(df)}")

if df.empty:

    st.error("⚠️ Nenhum dado encontrado. Verifique seu Token e ID no Secrets.")
    st.stop()

col1, col2 = st.columns(2)
col1.metric("Total Pedidos", df["Pedidos"].nunique())
col2.metric("Faturamento Real", f"R$ {df['Faturamento'].sum():.2f}")

st.dataframe(df)

# Gráficos
st.subheader("📊 Faturamento por Data")
st.line_chart(df.groupby("Data")["Faturamento"].sum())

# Download
arquivo = exportar_excel(df)
with open(arquivo, "rb") as file:
    st.download_button("📥 Baixar Excel", file, file_name="vendas.xlsx")
