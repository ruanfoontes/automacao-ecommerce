import requests
import os
import pandas as pd

def buscar_dados(ACCESS_TOKEN, USER_ID):

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

            if produto not in produtos:
                produtos[produto] = {"Quantidade": 0, "Faturamento": 0}

            produtos[produto]["Quantidade"] += quantidade
            produtos[produto]["Faturamento"] += valor_total
        except:
            pass

    lista = [
        {
            "Produto": p,
            "Quantidade": d["Quantidade"],
            "Faturamento": d["Faturamento"]
        }
        for p, d in produtos.items()
    ]

    return pd.DataFrame(lista)


def exportar_excel(df):
    os.makedirs("reports", exist_ok=True)
    caminho = "reports/vendas.xlsx"

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    return caminho