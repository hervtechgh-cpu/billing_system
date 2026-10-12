
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# QUICKBOOKS CONFIGURATION
# ============================================================

CLIENT_ID = os.getenv("QB_CLIENT_ID")
CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("QB_REFRESH_TOKEN")
REALM_ID = os.getenv("QB_REALM_ID")

TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
BASE_URL = f"https://sandbox-quickbooks.api.intuit.com/v3/company/{REALM_ID}"

print("CLIENT_ID loaded:", bool(CLIENT_ID))
print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
print("REFRESH_TOKEN loaded:", bool(REFRESH_TOKEN))
print()

# ============================================================
# AUTHENTICATION
# ============================================================

def get_access_token():

    response = requests.post(
        TOKEN_URL,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={
            "Accept": "application/json"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        }
    )

    if response.status_code != 200:
        print("Authentication failed!")
        print(response.text)
        raise SystemExit

    data = response.json()

    print("Authentication successful!")
    print("Access token received successfully.")
    print("Token length:", len(data.get("access_token", "")))

    if data.get("refresh_token"):
        print("A new refresh token was returned.")

    return data["access_token"]


ACCESS_TOKEN = get_access_token()

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json"
}

# ============================================================
# QUICKBOOKS QUERY FUNCTION
# ============================================================

def qb_query(query):

    url = f"{BASE_URL}/query"

    response = requests.get(
        url,
        headers=HEADERS,
        params={
            "query": query
        }
    )

    if response.status_code != 200:
        print()
        print("QUICKBOOKS API ERROR")
        print(response.status_code)
        print(response.text)
        raise SystemExit

    return response.json()


# ============================================================
# GET CUSTOMERS
# ============================================================

def get_customers():

    query = """
        SELECT *
        FROM Customer
        MAXRESULTS 1000
    """

    data = qb_query(query)

    return data.get("QueryResponse", {}).get("Customer", [])


# ============================================================
# GET INVOICES
# ============================================================

def get_invoices():

    query = """
        SELECT *
        FROM Invoice
        MAXRESULTS 1000
    """

    data = qb_query(query)

    return data.get("QueryResponse", {}).get("Invoice", [])


# ============================================================
# GET PAYMENTS
# ============================================================

def get_payments():

    query = """
        SELECT *
        FROM Payment
        MAXRESULTS 1000
    """

    data = qb_query(query)

    return data.get("QueryResponse", {}).get("Payment", [])


# ============================================================
# MAIN INVESTIGATION
# ============================================================

print()
print("=" * 70)
print("QUICKBOOKS DEEP BALANCE INVESTIGATION")
print("=" * 70)

customers = get_customers()
invoices = get_invoices()
payments = get_payments()

print()
print("Customers retrieved:", len(customers))
print("Invoices retrieved:", len(invoices))
print("Payments retrieved:", len(payments))

# ============================================================
# CUSTOMER LOOKUP
# ============================================================

customer_map = {}

for customer in customers:

    customer_id = str(customer.get("Id"))

    customer_map[customer_id] = {
        "name": customer.get("DisplayName"),
        "balance": customer.get("Balance"),
        "active": customer.get("Active")
    }


# ============================================================
# CUSTOMER BALANCES
# ============================================================

print()
print("=" * 70)
print("CUSTOMER BALANCES")
print("=" * 70)

for customer in customers:

    print("-" * 70)

    print("Customer:", customer.get("DisplayName"))
    print("QuickBooks ID:", customer.get("Id"))
    print("Customer Balance:", customer.get("Balance"))
    print("Active:", customer.get("Active"))

# ============================================================
# INVOICE DETAILS
# ============================================================

print()
print("=" * 70)
print("ALL INVOICES")
print("=" * 70)

if not invoices:

    print("NO INVOICES FOUND.")

else:

    for invoice in invoices:

        customer_ref = invoice.get("CustomerRef", {})
        customer_id = str(customer_ref.get("value", ""))

        customer_name = customer_map.get(
            customer_id,
            {}
        ).get(
            "name",
            customer_ref.get("name", "UNKNOWN")
        )

        print("-" * 70)

        print("Invoice ID:", invoice.get("Id"))
        print("Invoice Number:", invoice.get("DocNumber"))
        print("Customer:", customer_name)
        print("Customer ID:", customer_id)

        print("Transaction Date:", invoice.get("TxnDate"))
        print("Due Date:", invoice.get("DueDate"))

        print("Total Amount:", invoice.get("TotalAmt"))
        print("Balance:", invoice.get("Balance"))

        print("Email Status:", invoice.get("EmailStatus"))
        print("Private Note:", invoice.get("PrivateNote"))

        print("MetaData:", invoice.get("MetaData"))

        # ----------------------------------------------------
        # LINKED TRANSACTIONS
        # ----------------------------------------------------

        linked = invoice.get("LinkedTxn", [])

        if linked:

            print("Linked Transactions:")

            for txn in linked:

                print(
                    "   Type:",
                    txn.get("TxnType"),
                    "| ID:",
                    txn.get("TxnId")
                )

        else:

            print("Linked Transactions: NONE")


# ============================================================
# PAYMENTS
# ============================================================

print()
print("=" * 70)
print("ALL PAYMENTS")
print("=" * 70)

if not payments:

    print("NO PAYMENTS FOUND.")

else:

    for payment in payments:

        customer_ref = payment.get("CustomerRef", {})

        customer_id = str(
            customer_ref.get("value", "")
        )

        customer_name = customer_map.get(
            customer_id,
            {}
        ).get(
            "name",
            customer_ref.get("name", "UNKNOWN")
        )

        print("-" * 70)

        print("Payment ID:", payment.get("Id"))
        print("Customer:", customer_name)
        print("Customer ID:", customer_id)

        print("Payment Date:", payment.get("TxnDate"))
        print("Total Payment:", payment.get("TotalAmt"))

        print("Unapplied Amount:", payment.get("UnappliedAmt"))

        print()
        print("Payment Linked Transactions:")

        linked = payment.get("Line", [])

        if not linked:

            print("   NONE")

        else:

            found_link = False

            for line in linked:

                linked_txns = line.get(
                    "LinkedTxn",
                    []
                )

                if linked_txns:

                    found_link = True

                    for txn in linked_txns:

                        print(
                            "   Transaction Type:",
                            txn.get("TxnType"),
                            "| Transaction ID:",
                            txn.get("TxnId")
                        )

                else:

                    print("   Payment line has no linked invoice.")

            if not found_link:

                print("   NO INVOICE LINK FOUND")


# ============================================================
# SPECIAL PAULSEN INVESTIGATION
# ============================================================

print()
print("=" * 70)
print("PAULSEN MEDICAL SUPPLIES INVESTIGATION")
print("=" * 70)

paulsen_id = None

for customer in customers:

    if (
        customer.get("DisplayName", "").strip().lower()
        == "paulsen medical supplies"
    ):

        paulsen_id = str(customer.get("Id"))

        print("Paulsen Customer ID:", paulsen_id)
        print("Customer Balance:", customer.get("Balance"))

        break


if paulsen_id:

    print()
    print("PAULSEN INVOICES:")

    paulsen_invoices = []

    for invoice in invoices:

        customer_ref = invoice.get(
            "CustomerRef",
            {}
        )

        if str(customer_ref.get("value")) == paulsen_id:

            paulsen_invoices.append(invoice)

            print("-" * 60)
            print("Invoice ID:", invoice.get("Id"))
            print("Invoice Number:", invoice.get("DocNumber"))
            print("Date:", invoice.get("TxnDate"))
            print("Due Date:", invoice.get("DueDate"))
            print("Total:", invoice.get("TotalAmt"))
            print("Balance:", invoice.get("Balance"))
            print("LinkedTxn:", invoice.get("LinkedTxn"))


    print()
    print("PAULSEN PAYMENTS:")

    paulsen_payments = []

    for payment in payments:

        customer_ref = payment.get(
            "CustomerRef",
            {}
        )

        if str(customer_ref.get("value")) == paulsen_id:

            paulsen_payments.append(payment)

            print("-" * 60)

            print("Payment ID:", payment.get("Id"))
            print("Payment Date:", payment.get("TxnDate"))
            print("Total:", payment.get("TotalAmt"))
            print("Unapplied:", payment.get("UnappliedAmt"))

            print("Lines:")

            for line in payment.get("Line", []):

                print(
                    "   Amount:",
                    line.get("Amount")
                )

                print(
                    "   LinkedTxn:",
                    line.get("LinkedTxn")
                )

else:

    print("Paulsen Medical Supplies was not found.")


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("INVESTIGATION SUMMARY")
print("=" * 70)

print("Customers:", len(customers))
print("Invoices:", len(invoices))
print("Payments:", len(payments))

print()
print("The most important fields to check are:")
print()
print("Invoice Balance")
print("Invoice TotalAmt")
print("Invoice LinkedTxn")
print("Payment UnappliedAmt")
print("Payment LinkedTxn")
print()
print("=" * 70)
print("INVESTIGATION COMPLETE")
print("=" * 70)
