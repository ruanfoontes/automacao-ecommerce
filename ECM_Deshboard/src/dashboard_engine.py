import requests
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class MeliAnalytics:
    def __init__(self):
        self.token = os.getenv("ACCESS_TOKEN")
        self.user_id = os.getenv("USER_ID")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.df = pd.DataFrame()

    def fetch_data(self, limit=50):
        """Busca os dados brutos da API"""
        url = f"https://api.mercadolibre.com/orders/search?seller={self.user_id}&sort=date_desc&limit={limit}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            vendas = response.json().get('results', [])
            self._process_to_dataframe(vendas)
        else:
            print(f"Erro ao buscar dados: {response.status_code}")

    def _process_to_dataframe(self, vendas):
        """Transforma o JSON em uma tabela estruturada (Dataframe)"""
        dados_processados = []
        for v in vendas:
            for item in v.get('order_items', []):
                dados_processados.append({
                    "id": v.get('id'),
                    "data": pd.to_datetime(v.get('date_created')),
                    "produto": item.get('item', {}).get('title'),
                    "quantidade": int(item.get('quantity', 0)),
                    "preco_unitario": float(item.get('unit_price', 0)),
                    "total_pedido": float(v.get('total_amount', 0)),
                    "status": v.get('status')
                })
        self.df = pd.DataFrame(dados_processados)

    def get_kpis(self):
        """Calcula os números reais do negócio"""
        if self.df.empty:
            return "Nenhum dado carregado."

        faturamento_total = self.df['total_pedido'].unique().sum() # Soma única por ID de pedido
        total_itens = self.df['quantidade'].sum()
        ticket_medio = faturamento_total / len(self.df['id'].unique())
        
        return {
            "faturamento_total": faturamento_total,
            "total_itens": total_itens,
            "ticket_medio": ticket_medio,
            "qtd_pedidos": len(self.df['id'].unique())
        }

    def ranking_produtos(self):
        """Retorna os produtos que mais trazem dinheiro"""
        return self.df.groupby('produto')['total_pedido'].sum().sort_values(ascending=False)

# --- EXECUÇÃO DE TESTE (NÍVEL PROFISSIONAL) ---
if __name__ == "__main__":
    analytics = MeliAnalytics()
    analytics.fetch_data(limit=50) # Pegando as últimas 50 para o teste
    
    metrics = analytics.get_kpis()
    
    print("\n" + "="*40)
    print("📈 RELATÓRIO EXECUTIVO DE VENDAS")
    print("="*40)
    print(f"💰 FATURAMENTO BRUTO: R$ {metrics['faturamento_total']:,.2f}")
    print(f"📦 TOTAL DE PEDIDOS:  {metrics['qtd_pedidos']}")
    print(f"🛒 TICKET MÉDIO:      R$ {metrics['ticket_medio']:,.2f}")
    print(f"🔢 ITENS VENDIDOS:    {metrics['total_itens']}")
    print("-" * 40)
    print("\n🏆 TOP 3 PRODUTOS POR RECEITA:")
    print(analytics.ranking_produtos().head(3))
    print("="*40)