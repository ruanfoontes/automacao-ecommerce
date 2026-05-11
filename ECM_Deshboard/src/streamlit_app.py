import pandas as pd
import streamlit as st

from etl import buscar_dados_meli


st.set_page_config(page_title="Meu Dashboard Meli", layout="wide")

st.title("🚀 Dashboard de Vendas - Mercado Livre")

if st.button("Atualizar Dados"):
    df, mensagem = buscar_dados_meli()

    if df is not None and not df.empty:
        df = df.copy()
        df["Total_Venda"] = df["Preco_Unitario"] * df["Quantidade"]

        total_faturado = df["Total_Venda"].sum()
        total_itens = df["Quantidade"].sum()
        ticket_medio = total_faturado / len(df) if len(df) > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {total_faturado:,.2f}")
        col2.metric("Itens Vendidos", int(total_itens))
        col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

        st.subheader("Lista de Produtos Vendidos")
        st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Não foi possível carregar os dados: {mensagem}")

