from dotenv import load_dotenv
import os
import webbrowser

load_dotenv()

APP_ID = os.getenv("APP_ID")

redirect_uri = "https://google.com"

auth_url = (
    f"https://auth.mercadolivre.com.br/authorization"
    f"?response_type=code"
    f"&client_id={APP_ID}"
    f"&redirect_uri={redirect_uri}"
)

print("Abrindo navegador...")

webbrowser.open(auth_url)

print("\nSe não abrir automaticamente:")
print(auth_url)