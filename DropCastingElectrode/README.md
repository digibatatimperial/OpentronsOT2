# OT-2 Control Project (DIGIBAT)

This folder provides a clean Python workspace for controlling an Opentrons OT-2
from your laptop using the REST API.

## 1. Create virtual environment (recommended)

Windows:
    py -m venv ot2_env
    ot2_env\Scripts\activate

Mac/Linux:
    python3 -m venv ot2_env
    source ot2_env/bin/activate

## 2. Install required packages

pip install -r requirements.txt

## 3. Update robot IP

Edit `config.py` and put your OT-2 IP address.

## 4. Test connection

python connect_test.py

You should see:
{"status": "ok"}

## 5. Upload a protocol

python upload_protocol.py example_protocol.py

## 6. Run the uploaded protocol

python run_protocol.py

## 7. Check run status

python get_status.py

## 8. Stop or cancel a run

python stop_run.py
