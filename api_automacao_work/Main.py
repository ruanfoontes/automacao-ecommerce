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
    sku = item["item"]["seller_sku"]
    quantidade = item["quantity"]

    valor_total = order["total_amount"]
    taxa_ml = item["sale_fee"]

    lucro_bruto = valor_total - taxa_ml

    quantidade_vendas_ml += 1
    faturamento_ml += valor_total

    pedidos.append({
        "Plataforma": "Mercado Livre",
        "Pedido": order["id"],
        "Produto": produto,
        "SKU": sku,
        "Quantidade": quantidade,
        "Valor Total": valor_total,
        "Taxa ML": taxa_ml,
        "Lucro Bruto": lucro_bruto,
        "Cliente": order["buyer"]["nickname"],
        "Status": order["status"]
    })

    # MÉTRICAS DOS PRODUTOS
    if produto not in produtos:

        produtos[produto] = {
            "SKU": sku,
            "Quantidade Vendida": 0,
            "Faturamento": 0,
            "Taxa ML": 0,
            "Lucro Bruto": 0
        }

    produtos[produto]["Quantidade Vendida"] += quantidade
    produtos[produto]["Faturamento"] += valor_total
    produtos[produto]["Taxa ML"] += taxa_ml
    produtos[produto]["Lucro Bruto"] += lucro_bruto

# =========================
# DATAFRAME PEDIDOS
# =========================

df_pedidos = pd.DataFrame(pedidos)

# =========================
# DATAFRAME PRODUTOS
# =========================

lista_produtos = []

for produto, dados_produto in produtos.items():

    ticket_medio = (
        dados_produto["Faturamento"]
        / dados_produto["Quantidade Vendida"]
    )

    lista_produtos.append({
        "Produto": produto,
        "SKU": dados_produto["SKU"],
        "Quantidade Vendida": dados_produto["Quantidade Vendida"],
        "Faturamento": dados_produto["Faturamento"],
        "Taxa ML": dados_produto["Taxa ML"],
        "Lucro Bruto": dados_produto["Lucro Bruto"],
        "Ticket Médio": round(ticket_medio, 2)
    })

df_produtos = pd.DataFrame(lista_produtos)

# ORDENAR MAIS VENDIDOS
df_produtos = df_produtos.sort_values(
    by="Quantidade Vendida",
    ascending=False
)

# =========================
# RESUMO PLATAFORMA
# =========================

df_resumo = pd.DataFrame([
    {
        "Plataforma": "Mercado Livre",
        "Quantidade de Vendas": quantidade_vendas_ml,
        "Faturamento": faturamento_ml
    }
])

# =========================
# EXPORTAR EXCEL
# =========================

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

print("\nRelatório profissional gerado!")