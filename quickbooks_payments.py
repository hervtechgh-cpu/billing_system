import os
import requests
from dotenv import load_dotenv
from quickbooks_auth import get_access_token

load_dotenv()

REALM_ID = os.getenv("QB_REALM_ID")

BASE_URL = (
    f"https://sandbox-quickbooks.api.intuit.com"
    f"/v3/company/{REALM_ID}"
)


def get_payments():

    access_token = get_access_token()

    if not access_token:
        print("Could not get access token.")
        return

    url = f"{BASE_URL}/query"

    query = "SELECT * FROM Payment"

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

    print("Status:", response.status_code)

    if response.status_code != 200:
        print("Failed to retrieve payments.")
        print(response.text)
        return

    data = response.json()

    payments = data.get("QueryResponse", {}).get("Payment", [])

    print("Number of payments:", len(payments))

    for payment in payments:

        payment_id = payment.get("Id")
        customer = payment.get("CustomerRef", {}).get("name")
        amount = payment.get("TotalAmt")
        payment_date = payment.get("TxnDate")

        print("--------------------------------")
        print("Payment ID:", payment_id)
        print("Customer:", customer)
        print("Amount:", amount)
        print("Payment Date:", payment_date)


if __name__ == "__main__":
    get_payments()