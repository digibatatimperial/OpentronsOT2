import requests
from config import BASE_URL, HEADERS

# get the most recently uploaded protocol
plist = requests.get(BASE_URL + "/protocols").json()
latest_protocol = plist["data"][-1]["id"]

# create run
run_resp = requests.post(
    BASE_URL + "/runs",
    headers=HEADERS,
    json={"data": {"protocolId": latest_protocol}}
).json()

run_id = run_resp["data"]["id"]
print("Created run:", run_id)

# start run
play = requests.post(
    BASE_URL + f"/runs/{run_id}/actions",
    headers=HEADERS,
    json={"data": {"actionType": "play"}}
)

print("Run started:", play.json())