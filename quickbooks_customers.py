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

    return response.json()["access_token"]


def get_customers():

    access_token = get_access_token()

    query = """
        SELECT * FROM Customer
    """

    url = f"{BASE_URL}/v3/company/{REALM_ID}/query"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    params = {
        "query": query
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    print("Status Code:", response.status_code)

    if response.status_code != 200:
        print("Request failed:")
        print(response.text)
        return

    data = response.json()

    customers = data.get("QueryResponse", {}).get("Customer", [])

    print(f"\nNumber of customers: {len(customers)}")
    print("-" * 70)

    for customer in customers:

        customer_id = customer.get("Id")
        name = customer.get("DisplayName")

        email = customer.get(
            "PrimaryEmailAddr",
            {}
        ).get("Address", "")

        phone = customer.get(
            "PrimaryPhone",
            {}
        ).get("FreeFormNumber", "")

        print(f"ID: {customer_id}")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Phone: {phone}")
        print("-" * 70)


if __name__ == "__main__":
    get_customers()