import requests
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

os.makedirs("reports", exist_ok=True)


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
        try:
            item = order["order_items"][0]

            produto = item["item"]["title"]
            quantidade = item["quantity"]
            valor_total = order["total_amount"]

            # 📅 pega data do pedido
            data = order.get("date_created", "")
            data_obj = datetime.fromisoformat(data.replace("Z", ""))

            dia = data_obj.date()
            mes = data_obj.month
            ano = data_obj.year

            if produto not in produtos:
                produtos[produto] = {
                    "Quantidade": 0,
                    "Faturamento": 0,
                    "Dia": dia,
                    "Mes": mes,
                    "Ano": ano
                }

            produtos[produto]["Quantidade"] += quantidade
            produtos[produto]["Faturamento"] += valor_total

        except:
            continue

    lista = []

    for p, d in produtos.items():
        lista.append({
            "Produto": p,
            "Quantidade": d["Quantidade"],
            "Faturamento": d["Faturamento"],
            "Dia": d["Dia"],
            "Mes": d["Mes"],
            "Ano": d["Ano"]
        })

    return pd.DataFrame(lista)


def exportar_excel(df):
    caminho = "reports/vendas.xlsx"

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Vendas", index=False)

    return caminho