import requests
from config import BASE_URL, HEADERS

print("Sending request to:", BASE_URL)

r = requests.get(
    BASE_URL + "/health",
    headers=HEADERS
)

print("Robot response:", r.json())
