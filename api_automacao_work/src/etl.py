import requests
import os
from dotenv import load_dotenv

load_dotenv()

def buscar_dados():
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    USER_ID = os.getenv("USER_ID")

    url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)
    dados = response.json()

    produtos = {}

    for order in dados.get("results", []):
        item = order["order_items"][0]

        produto = item["item"]["title"]
        quantidade = item["quantity"]
        valor_total = order["total_amount"]

        if produto not in produtos:
            produtos[produto] = {
                "Quantidade": 0,
                "Faturamento": 0
            }

        produtos[produto]["Quantidade"] += quantidade
        produtos[produto]["Faturamento"] += valor_total

    import pandas as pd

    lista = []
    for p, d in produtos.items():
        lista.append({
            "Produto": p,
            "Quantidade": d["Quantidade"],
            "Faturamento": d["Faturamento"]
        })

    return pd.DataFrame(lista)