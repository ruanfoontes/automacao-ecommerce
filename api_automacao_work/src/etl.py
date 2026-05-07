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

    vendas = []

    for order in dados.get("results", []):
        try:
            data_raw = order.get("date_created")

            if not data_raw:
                continue

            # converte data real da API
            data_obj = datetime.fromisoformat(data_raw.replace("Z", ""))

            # filtro: desde 01/01/2022
            if data_obj.year < 2022:
                continue

            data_br = data_obj.strftime("%d/%m/%Y")

            vendas.append({
                "Data": data_br,
                "Ano": data_obj.year,
                "Mes": data_obj.month,
                "Dia": data_obj.day,
                "Faturamento": float(order.get("total_amount", 0)),
                "Pedido": order.get("id")
            })

        except:
            continue

    return pd.DataFrame(vendas)


def exportar_excel(df):
    caminho = "reports/vendas.xlsx"

    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    return caminho