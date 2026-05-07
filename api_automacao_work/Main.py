from dotenv import load_dotenv
import os
import requests

load_dotenv()

APP_ID = os.getenv("APP_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

CODE = "TG-69fc9d3853fabf0001f3cc0a-3120483679"

url = "https://api.mercadolibre.com/oauth/token"

payload = {
    "grant_type": "authorization_code",
    "client_id": APP_ID,
    "client_secret": CLIENT_SECRET,
    "code": CODE,
    "redirect_uri": "https://google.com"
}

response = requests.post(url, data=payload)

dados = response.json()

print(dados)