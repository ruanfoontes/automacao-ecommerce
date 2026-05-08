import requests
import os
from dotenv import load_dotenv

load_dotenv()

def testar_conexao():
    token = os.getenv("ACCESS_TOKEN")
    user_id = os.getenv("USER_ID")
    
    print("--- Iniciando Teste de Vendas ---")
    
    # URL para buscar as últimas vendas do seu usuário
    url = f"https://api.mercadolibre.com/orders/search?seller={user_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            dados = response.json()
            total_vendas = dados.get('paging', {}).get('total', 0)
            print(f"✅ Sucesso! Conectado à conta ID: {user_id}")
            print(f"📊 Total de vendas encontradas: {total_vendas}")
            
            # Mostra o nome do primeiro produto vendido (se houver vendas)
            if total_vendas > 0:
                primeira_venda = dados['results'][0]['order_items'][0]['item']['title']
                print(f"📦 Último produto vendido: {primeira_venda}")
        else:
            print(f"❌ Erro na API: {response.status_code}")
            print(response.json())
            
    except Exception as e:
        print(f"⚠️ Erro no código: {e}")

if __name__ == "__main__":
    testar_conexao()