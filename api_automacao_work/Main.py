from dotenv import load_dotenv
import os
import requests
import pandas as pd

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(url, headers=headers)

dados = response.json()

pedidos = []
produtos = {}

quantidade_vendas_ml = 0
faturamento_ml = 0

for order in dados["results"]:

    item = order["order_items"][0]

    produto = item["item"]["title"]
    quantidade = item["quantity"]
    valor_total = order["total_amount"]

    quantidade_vendas_ml += 1
    faturamento_ml += valor_total

    pedidos.append({
        "Plataforma": "Mercado Livre",
        "Pedido": order["id"],
        "Produto": produto,
        "SKU": item["item"]["seller_sku"],
        "Quantidade": quantidade,
        "Valor Total": valor_total,
        "Cliente": order["buyer"]["nickname"],
        "Status": order["status"]
    })

    # MÉTRICAS DOS PRODUTOS
    if produto not in produtos:
        produtos[produto] = {
            "Quantidade Vendida": 0,
            "Faturamento": 0
        }

    produtos[produto]["Quantidade Vendida"] += quantidade
    produtos[produto]["Faturamento"] += valor_total

# DATAFRAME PEDIDOS
df_pedidos = pd.DataFrame(pedidos)

# DATAFRAME PRODUTOS
lista_produtos = []

for produto, dados_produto in produtos.items():
    lista_produtos.append({
        "Produto": produto,
        "Quantidade Vendida": dados_produto["Quantidade Vendida"],
        "Faturamento": dados_produto["Faturamento"]
    })

df_produtos = pd.DataFrame(lista_produtos)

# RESUMO PLATAFORMA
df_resumo = pd.DataFrame([
    {
        "Plataforma": "Mercado Livre",
        "Quantidade de Vendas": quantidade_vendas_ml,
        "Faturamento": faturamento_ml
    }
])

# EXPORTAR EXCEL
with pd.ExcelWriter("relatorio_ecommerce.xlsx") as writer:

    df_resumo.to_excel(
        writer,
        sheet_name="Resumo Plataforma",
        index=False
    )

    df_pedidos.to_excel(
        writer,
        sheet_name="Pedidos",
        index=False
    )

    df_produtos.to_excel(
        writer,
        sheet_name="Produtos",
        index=False
    )

print("\nRelatório gerado com sucesso!")