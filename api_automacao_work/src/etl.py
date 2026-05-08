import requests
import os
import pandas as pd
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass 

def buscar_dados():
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    USER_ID = os.getenv("USER_ID")

    url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    response = requests.get(url, headers=headers)
    dados = response.json()
    vendas = []

    for order in dados.get("results", []):
        try:
            data_raw = order.get("date_created")
            if not data_raw:
                continue

            data_obj = datetime.fromisoformat(data_raw.replace("Z", ""))
            if data_obj.year < 2022:
                continue

            vendas.append({
                "Data": data_obj.strftime("%d/%m/%Y"),
                "Ano": data_obj.year,
                "Mes": data_obj.month,
                "Dia": data_obj.day,
                "Faturamento": float(order.get("total_amount", 0)),
                "Pedidos": order.get("id")
            })
        except:
            continue

    return pd.DataFrame(vendas)

def exportar_excel(df):
    caminho = "vendas.xlsx"
    df.to_excel(caminho, index=False)
    return caminho