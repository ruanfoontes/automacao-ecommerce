import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def buscar_dados_meli():
    token = os.getenv("ACCESS_TOKEN")
    user_id = os.getenv("USER_ID")
    
    # URL para buscar as ordens recentes
    url = f"https://api.mercadolibre.com/orders/search?seller={user_id}&limit=50"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return pd.DataFrame(), f"Erro API: {response.status_code}"
        
        dados = response.json()
        vendas_brutas = []

        for order in dados.get("results", []):
            for item in order.get("order_items", []):
                preco = float(item.get("unit_price", 0))
                qtd = int(item.get("quantity", 0))
                
                vendas_brutas.append({
                    "Data": order.get("date_created")[:10],
                    "Produto": item.get("item", {}).get("title"),
                    "Preco_Unitario": preco,
                    "Quantidade": qtd,
                    # O cálculo de faturamento será feito no DataFrame
                    "ID_Ordem": order.get("id")
                })
        
        df = pd.DataFrame(vendas_brutas)
        return df, "Sucesso"
    
    except Exception as e:
        return pd.DataFrame(), str(e)