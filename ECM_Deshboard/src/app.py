import streamlit as st
import pandas as pd
from etl import buscar_dados_meli

st.set_page_config(page_title="Meu Dashboard Meli", layout="wide")

st.title("🚀 Dashboard de Vendas - Mercado Livre")

if st.button("Atualizar Dados"):
    df, mensagem = buscar_dados_meli()
    
    if not df.empty:
        # --- CÁLCULOS DO APP ---
        # Calculamos o total por linha (Preço * Quantidade)
        df["Total_Venda"] = df["Preco_Unitario"] * df["Quantidade"]
        
        # Totais para os cartões
        total_faturado = df["Total_Venda"].sum()
        total_itens = df["Quantidade"].sum()
        ticket_medio = total_faturado / len(df) if len(df) > 0 else 0

        # --- EXIBIÇÃO ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {total_faturado:,.2f}")
        col2.metric("Itens Vendidos", int(total_itens))
        col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

        st.subheader("Lista de Produtos Vendidos")
        st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Não foi possível carregar os dados: {mensagem}")