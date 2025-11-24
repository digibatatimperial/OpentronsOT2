import sys
import requests
from config import BASE_URL, HEADERS

if len(sys.argv) < 2:
    print("Usage: python upload_protocol.py <protocol_file.py>")
    sys.exit(1)

protocol_path = sys.argv[1]

with open(protocol_path, "rb") as f:
    files = {"protocolFile": f}
    resp = requests.post(BASE_URL + "/protocols", headers=HEADERS, files=files)

print("Upload response:")
print(resp.json())