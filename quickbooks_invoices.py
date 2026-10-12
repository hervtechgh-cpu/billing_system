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


def get_invoices():

    access_token = get_access_token()

    query = """
        SELECT * FROM Invoice
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

    invoices = data.get(
        "QueryResponse",
        {}
    ).get(
        "Invoice",
        []
    )

    print(f"\nNumber of invoices: {len(invoices)}")
    print("=" * 80)

    for invoice in invoices:

        invoice_id = invoice.get("Id")
        invoice_number = invoice.get("DocNumber")

        customer_ref = invoice.get(
            "CustomerRef",
            {}
        )

        customer_id = customer_ref.get("value")
        customer_name = customer_ref.get("name")

        transaction_date = invoice.get("TxnDate")
        due_date = invoice.get("DueDate")

        total_amount = invoice.get("TotalAmt", 0)
        balance = invoice.get("Balance", 0)

        print(f"Invoice ID:     {invoice_id}")
        print(f"Invoice Number: {invoice_number}")
        print(f"Customer ID:    {customer_id}")
        print(f"Customer Name:  {customer_name}")
        print(f"Invoice Date:   {transaction_date}")
        print(f"Due Date:       {due_date}")
        print(f"Total Amount:   {total_amount}")
        print(f"Balance:        {balance}")
        print("-" * 80)


if __name__ == "__main__":
    get_invoices()