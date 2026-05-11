import os

from meli_auth import ensure_dotenv_loaded, meli_get

ensure_dotenv_loaded()

def testar_conexao() -> int:
    user_id = os.getenv("USER_ID")
    
    print("--- Iniciando Teste de Vendas ---")
    
    # URL para buscar as últimas vendas do seu usuário
    url = f"https://api.mercadolibre.com/orders/search?seller={user_id}"

    try:
        response = meli_get(url)
        
        if response.status_code == 200:
            dados = response.json()
            total_vendas = dados.get('paging', {}).get('total', 0)
            print(f"[OK] Conectado a conta ID: {user_id}")
            print(f"Total de vendas encontradas: {total_vendas}")

            # Mostra o nome do primeiro produto vendido (se houver vendas)
            if total_vendas > 0:
                primeira_venda = dados["results"][0]["order_items"][0]["item"]["title"]
                print(f"Ultimo produto vendido: {primeira_venda}")
            return 0
        else:
            print(f"[ERRO] API status {response.status_code}")
            try:
                print(response.json())
            except Exception:
                print(response.text)
            return 1

    except Exception as e:
        print(f"[ERRO] {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(testar_conexao())