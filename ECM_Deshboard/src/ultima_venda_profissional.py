import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def buscar_ultima_venda():
    token = os.getenv("ACCESS_TOKEN")
    user_id = os.getenv("USER_ID")
    
    # URL profissional: filtrando por seller e ordenando por data decrescente
    # date_desc garante que o índice [0] seja sempre a última venda realizada
    url = f"https://api.mercadolibre.com/orders/search?seller={user_id}&sort=date_desc&limit=1"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança erro se o status não for 200
        
        dados = response.json()
        results = dados.get('results', [])

        if not results:
            print("ℹ️ Nenhuma venda encontrada para este usuário.")
            return

        # Acessando a venda mais recente (índice 0 após o sort date_desc)
        ultima_venda = results[0]
        data_iso = ultima_venda.get('date_created')
        
        # Formatando a data para o padrão brasileiro
        data_obj = datetime.fromisoformat(data_iso.replace('Z', '+00:00'))
        data_formatada = data_obj.strftime('%d/%m/%Y às %H:%M:%S')

        # Extraindo informações dos itens (pode haver mais de um item na mesma venda)
        itens = ultima_venda.get('order_items', [])
        
        print("-" * 50)
        print(f"🔥 ÚLTIMA VENDA REALIZADA: {data_formatada}")
        print("-" * 50)

        for i, item in enumerate(itens, 1):
            titulo = item.get('item', {}).get('title')
            quantidade = item.get('quantity')
            preco = item.get('unit_price')
            print(f"Item {i}: {titulo}")
            print(f"Qtd: {quantidade} | Preço Un: R$ {preco:,.2f}")
        
        print(f"\n💰 Valor Total do Pedido: R$ {ultima_venda.get('total_amount'):,.2f}")
        print("-" * 50)

    except requests.exceptions.HTTPError as e:
        print(f"❌ Erro de permissão ou API: {e.response.status_code}")
        print(e.response.json())
    except Exception as e:
        print(f"⚠️ Erro inesperado: {e}")

if __name__ == "__main__":
    buscar_ultima_venda()