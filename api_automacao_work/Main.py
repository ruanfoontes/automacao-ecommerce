from dotenv import load_dotenv
import os

load_dotenv()

app_id = os.getenv("APP_ID")
client_secret = os.getenv("CLIENT_SECRET")

print("APP_ID:", app_id)
print("CLIENT_SECRET:", client_secret)