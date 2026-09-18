import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("FIGMA_TOKEN")

headers = {
    "X-Figma-Token": token
}

response = requests.get(
    "https://api.figma.com/v1/me",
    headers=headers
)

print(response.status_code)
print(response.json())