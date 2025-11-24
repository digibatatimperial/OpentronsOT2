import requests
from config import BASE_URL

runs = requests.get(BASE_URL + "/runs").json()["data"]
if not runs:
    print("No runs found.")
    exit()

latest = runs[-1]["id"]
info = requests.get(BASE_URL + f"/runs/{latest}").json()

print("Run status:", info["data"]["status"])
print("Details:")
print(info)