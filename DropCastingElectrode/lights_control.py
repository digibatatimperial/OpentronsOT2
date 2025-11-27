import requests
from config import BASE_URL, HEADERS


def lights_on():
    r = requests.post(
        BASE_URL + "/robot/lights",
        headers=HEADERS,
        json={"on": True}
    )
    print("Lights ON:", r.json())


def lights_off():
    r = requests.post(
        BASE_URL + "/robot/lights",
        headers=HEADERS,
        json={"on": False}
    )
    print("Lights OFF:", r.json())


if __name__ == "__main__":
    print("1 = ON, 0 = OFF")
    choice = input("Select (1/0): ").strip()
    if choice == "1":
        lights_on()1
    elif choice == "0":
        lights_off()
    else:
        print("Invalid input")
