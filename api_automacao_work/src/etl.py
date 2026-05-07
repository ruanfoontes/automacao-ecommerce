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

    lista = []

    for order in dados.get("results", []):
        try:
            item = order["order_items"][0]

            produto = item["item"]["title"]
            quantidade = item["quantity"]
            valor_total = order["total_amount"]

            # 📅 DATA DO PEDIDO
            data = order.get("date_created", None)
            data = pd.to_datetime(data)

            lista.append({
                "Produto": produto,
                "Quantidade": quantidade,
                "Faturamento": valor_total,
                "Data": data
            })

        except:
            continue

    df = pd.DataFrame(lista)

    # criar colunas de tempo
    df["Dia"] = df["Data"].dt.date
    df["Mes"] = df["Data"].dt.to_period("M").astype(str)
    df["Ano"] = df["Data"].dt.year

    return df