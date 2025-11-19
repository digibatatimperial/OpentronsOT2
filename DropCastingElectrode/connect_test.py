import requests
from config import BASE_URL

print("Sending request to:", BASE_URL)

r = requests.get(BASE_URL + "/health")
print("Robot response:", r.json())