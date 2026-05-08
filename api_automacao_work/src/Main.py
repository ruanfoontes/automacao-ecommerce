import streamlit as st
import pandas as pd
import os
from etl import buscar_dados, exportar_excel

# Configuração da página
st.set_page_config(page_title="Dashboard Meli", layout="wide")

st.title("📊 Monitor de Vendas Mercado Livre")

# Chamada da função
df = buscar_dados()

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado. Verifique se o Token no 'Secrets' é novo!")
    st.info("Dica: Tokens do Mercado Livre expiram a cada 6 horas.")
else:
    # --- CÁLCULOS FEITOS PELO APP ---
    total_vendas_qtd = df["Quantidade"].sum()
    faturamento_total = df["Faturamento_Item"].sum()
    ticket_medio = faturamento_total / total_vendas_qtd if total_vendas_qtd > 0 else 0

    # --- EXIBIÇÃO DAS MÉTRICAS ---
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Qtd Produtos Vendidos", int(total_vendas_qtd))
    col2.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
    col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

    st.divider()

    # --- TABELA DETALHADA ---
    st.subheader("📋 Detalhamento por Item")
    st.dataframe(
        df[["Data", "Produto", "Quantidade", "Preco_Unit", "Faturamento_Item", "ID_Pedido"]],
        use_container_width=True
    )

    # --- BOTÃO DE DOWNLOAD ---
    caminho_arquivo = exportar_excel(df)
    with open(caminho_arquivo, "rb") as f:
        st.download_button(
            label="📥 Baixar Relatório em Excel",
            data=f,
            file_name="relatorio_vendas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )