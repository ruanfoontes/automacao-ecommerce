from dotenv import load_dotenv
import os
import requests
import json

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

url = f"https://api.mercadolibre.com/orders/search?seller={USER_ID}"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(url, headers=headers)

dados = response.json()

print(json.dumps(dados, indent=4, ensure_ascii=False))