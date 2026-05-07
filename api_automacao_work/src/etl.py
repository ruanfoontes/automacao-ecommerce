import requests
import os
import pandas as pd
import streamlit as st


def buscar_dados():
    ACCESS_TOKEN = st.secrets["ACCESS_TOKEN"]
    USER_ID = st.secrets["USER_ID"]

    url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)
    dados = response.json()

    produtos = {}

    for order in dados.get("results", []):
        try:
            item = order["order_items"][0]

            produto = item["item"]["title"]
            quantidade = item["quantity"]
            valor_total = order["total_amount"]

            plataforma = order.get("payments", [{}])[0].get("payment_type", "Desconhecida")

            key = (produto, plataforma)

            if key not in produtos:
                produtos[key] = {
                    "Produto": produto,
                    "Plataforma": plataforma,
                    "Quantidade": 0,
                    "Faturamento": 0
                }

            produtos[key]["Quantidade"] += quantidade
            produtos[key]["Faturamento"] += valor_total

        except:
            continue

    return pd.DataFrame(list(produtos.values()))


def exportar_excel(df):
    os.makedirs("reports", exist_ok=True)

    caminho = "reports/vendas.xlsx"

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Vendas")

    return caminho