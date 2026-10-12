import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("QB_CLIENT_ID")
CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("QB_REFRESH_TOKEN")
REALM_ID = os.getenv("QB_REALM_ID")

TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

BASE_URL = "https://sandbox-quickbooks.api.intuit.com"


def get_access_token():

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={
            "Accept": "application/json"
        }
    )

    response.raise_for_status()

    token_data = response.json()

    return token_data["access_token"]


def get_company_info():

    access_token = get_access_token()

    url = f"{BASE_URL}/v3/company/{REALM_ID}/companyinfo/{REALM_ID}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    print("Status Code:", response.status_code)

    if response.status_code == 200:

        data = response.json()

        print("\nQuickBooks connection successful!")
        print(data)

    else:

        print("\nRequest failed.")
        print(response.text)


if __name__ == "__main__":
    get_company_info()