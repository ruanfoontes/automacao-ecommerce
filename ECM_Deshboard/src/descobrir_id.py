import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("ACCESS_TOKEN")
url = "https://api.mercadolibre.com/users/me"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    dados = response.json()
    print(f"✅ Seu ID real é: {dados.get('id')}")
    print(f"👤 Nome da conta: {dados.get('nickname')}")
else:
    print("❌ Erro ao identificar Token. Verifique se o Token no .env está correto.")
    print(response.json())