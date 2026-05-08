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

    # Endpoint para buscar ordens do vendedor
    url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    response = requests.get(url, headers=headers)
    
    # Verificação de erro da API
    if response.status_code != 200:
        return pd.DataFrame() # Retorna vazio se der erro no Token/Conexão

    dados = response.json()
    vendas_detalhadas = []

    for order in dados.get("results", []):
        for item in order.get("order_items", []):
            try:
                preco_unitario = float(item.get("unit_price", 0))
                quantidade = int(item.get("quantity", 0))
                subtotal = preco_unitario * quantidade

                # Tratamento simples da data
                data_api = order.get("date_created", "")
                data_formatada = data_api[:10] if data_api else "N/A"

                vendas_detalhadas.append({
                    "ID_Pedido": order.get("id"),
                    "Produto": item.get("item", {}).get("title"),
                    "Preco_Unit": preco_unitario,
                    "Quantidade": quantidade,
                    "Faturamento_Item": subtotal,
                    "Data": data_formatada
                })
            except Exception:
                continue

    return pd.DataFrame(vendas_detalhadas)

def exportar_excel(df):
    caminho = "vendas_detalhadas.xlsx"
    df.to_excel(caminho, index=False)
    return caminho