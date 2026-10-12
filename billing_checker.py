
import time
import requests
import os

from dotenv import load_dotenv
from quickbooks_auth import get_access_token
from billing_logic import process_customer


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

REALM_ID = os.getenv("QB_REALM_ID")


# ============================================================
# QUICKBOOKS SANDBOX URL
# ============================================================

BASE_URL = (
    f"https://sandbox-quickbooks.api.intuit.com"
    f"/v3/company/{REALM_ID}"
)


# ============================================================
# QUICKBOOKS QUERY
# ============================================================

def qb_query(query):
    """
    Execute a QuickBooks Online query.
    """

    access_token = get_access_token()

    if not access_token:

        print("Could not get access token.")

        return {}

    url = f"{BASE_URL}/query"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    params = {
        "query": query
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

    except requests.RequestException as e:

        print(
            "Error connecting to QuickBooks:"
        )

        print(e)

        return {}

    if response.status_code != 200:

        print(
            "QuickBooks API error."
        )

        print(
            "Status code:",
            response.status_code
        )

        print(
            response.text
        )

        return {}

    try:

        data = response.json()

    except ValueError:

        print(
            "QuickBooks returned invalid JSON."
        )

        return {}

    return data.get(
        "QueryResponse",
        {}
    )


# ============================================================
# GET CUSTOMERS
# ============================================================

def get_customers():

    query = """
        SELECT *
        FROM Customer
        MAXRESULTS 1000
    """

    result = qb_query(query)

    return result.get(
        "Customer",
        []
    )


# ============================================================
# GET INVOICES
# ============================================================

def get_invoices():

    query = """
        SELECT *
        FROM Invoice
        MAXRESULTS 1000
    """

    result = qb_query(query)

    return result.get(
        "Invoice",
        []
    )


# ============================================================
# GET PAYMENTS
# ============================================================

def get_payments():

    query = """
        SELECT *
        FROM Payment
        MAXRESULTS 1000
    """

    result = qb_query(query)

    return result.get(
        "Payment",
        []
    )


# ============================================================
# RUN BILLING CHECK
# ============================================================

def run_billing_check():

    print()
    print("================================")
    print("RUNNING BILLING CHECK")
    print("================================")

    # ========================================================
    # GET CUSTOMERS
    # ========================================================

    customers_list = get_customers()

    print(
        "Customers retrieved:",
        len(customers_list)
    )

    if not customers_list:

        print(
            "No customers found."
        )

        return

    # ========================================================
    # GET INVOICES
    # ========================================================

    invoices = get_invoices()

    print(
        "Invoices found:",
        len(invoices)
    )

    # ========================================================
    # GET PAYMENTS
    # ========================================================

    payments = get_payments()

    print(
        "Payments found:",
        len(payments)
    )

    # ========================================================
    # CREATE CUSTOMER STRUCTURE
    # ========================================================

    customers = {}

    for customer in customers_list:

        customer_id = customer.get(
            "Id"
        )

        if not customer_id:
            continue

        customer_name = customer.get(
            "DisplayName",
            "Unknown Customer"
        )

        # ----------------------------------------------------
        # QUICKBOOKS CUSTOMER BALANCE
        # USE BALANCEWITHJOBS FIRST
        # FALL BACK TO BALANCE
        # ----------------------------------------------------

        try:

            customer_balance = float(
                customer.get(
                    "BalanceWithJobs",
                    customer.get(
                        "Balance",
                        0
                    )
                ) or 0
            )

        except (
            TypeError,
            ValueError
        ):

            customer_balance = 0.0

        customers[
            str(customer_id)
        ] = {

            "CustomerID":
                str(customer_id),

            "CustomerName":
                customer_name,

            "CustomerBalance":
                customer_balance,

            "Invoices": [],

            "Payments": []
        }

    # ========================================================
    # ATTACH INVOICES TO CUSTOMERS
    # ========================================================

    for invoice in invoices:

        customer_ref = invoice.get(
            "CustomerRef",
            {}
        )

        customer_id = customer_ref.get(
            "value"
        )

        if not customer_id:
            continue

        customer_id = str(
            customer_id
        )

        customer_name = customer_ref.get(
            "name",
            "Unknown Customer"
        )

        # ----------------------------------------------------
        # INVOICE BALANCE
        # ----------------------------------------------------

        try:

            invoice_balance = float(
                invoice.get(
                    "Balance",
                    0
                ) or 0
            )

        except (
            TypeError,
            ValueError
        ):

            invoice_balance = 0.0

        # ----------------------------------------------------
        # INVOICE TOTAL
        # ----------------------------------------------------

        try:

            total_amount = float(
                invoice.get(
                    "TotalAmt",
                    0
                ) or 0
            )

        except (
            TypeError,
            ValueError
        ):

            total_amount = 0.0

        billing_invoice = {

            "InvoiceID":
                invoice.get("Id"),

            "CustomerID":
                customer_id,

            "CustomerName":
                customer_name,

            "Balance":
                invoice_balance,

            "TotalAmount":
                total_amount,

            "DueDate":
                invoice.get("DueDate"),

            "TxnDate":
                invoice.get("TxnDate")
        }

        # ----------------------------------------------------
        # CUSTOMER MAY NOT HAVE BEEN IN CUSTOMER QUERY
        # ----------------------------------------------------

        if customer_id not in customers:

            customers[
                customer_id
            ] = {

                "CustomerID":
                    customer_id,

                "CustomerName":
                    customer_name,

                "CustomerBalance":
                    0.0,

                "Invoices": [],

                "Payments": []
            }

        customers[
            customer_id
        ][
            "Invoices"
        ].append(
            billing_invoice
        )

    # ========================================================
    # ATTACH PAYMENTS TO CUSTOMERS
    # ========================================================

    for payment in payments:

        customer_ref = payment.get(
            "CustomerRef",
            {}
        )

        customer_id = customer_ref.get(
            "value"
        )

        if not customer_id:
            continue

        customer_id = str(
            customer_id
        )

        customer_name = customer_ref.get(
            "name",
            "Unknown Customer"
        )

        # ----------------------------------------------------
        # PAYMENT TOTAL
        # ----------------------------------------------------

        try:

            payment_amount = float(
                payment.get(
                    "TotalAmt",
                    0
                ) or 0
            )

        except (
            TypeError,
            ValueError
        ):

            payment_amount = 0.0

        # ----------------------------------------------------
        # UNAPPLIED PAYMENT
        # ----------------------------------------------------

        try:

            unapplied_amount = float(
                payment.get(
                    "UnappliedAmt",
                    0
                ) or 0
            )

        except (
            TypeError,
            ValueError
        ):

            unapplied_amount = 0.0

        payment_record = {

            "PaymentID":
                payment.get("Id"),

            "Amount":
                payment_amount,

            "UnappliedAmount":
                unapplied_amount,

            "TxnDate":
                payment.get("TxnDate")
        }

        # ----------------------------------------------------
        # CUSTOMER MAY NOT HAVE BEEN IN CUSTOMER QUERY
        # ----------------------------------------------------

        if customer_id not in customers:

            customers[
                customer_id
            ] = {

                "CustomerID":
                    customer_id,

                "CustomerName":
                    customer_name,

                "CustomerBalance":
                    0.0,

                "Invoices": [],

                "Payments": []
            }

        customers[
            customer_id
        ][
            "Payments"
        ].append(
            payment_record
        )

    # ========================================================
    # PROCESS CUSTOMERS
    # ========================================================

    print()
    print(
        "Customers to process:",
        len(customers)
    )

    print()

    for customer_id, customer_data in customers.items():

        try:

            process_customer(

                customer_id=
                    customer_id,

                customer_name=
                    customer_data[
                        "CustomerName"
                    ],

                customer_balance=
                    customer_data[
                        "CustomerBalance"
                    ],

                invoices=
                    customer_data[
                        "Invoices"
                    ],

                payments=
                    customer_data[
                        "Payments"
                    ]
            )

        except Exception as e:

            print()
            print(
                "ERROR processing customer:"
            )

            print(
                "Customer ID:",
                customer_id
            )

            print(
                "Customer:",
                customer_data[
                    "CustomerName"
                ]
            )

            print(
                "Error:",
                e
            )


# ============================================================
# CONTINUOUS BILLING LOOP
# ============================================================

if __name__ == "__main__":

    while True:

        try:

            run_billing_check()

        except KeyboardInterrupt:

            print(
                "\nBilling checker stopped."
            )

            break

        except Exception as e:

            print()
            print(
                "Unexpected error:"
            )

            print(e)

        print()
        print(
            "Next check will run in 5 minutes..."
        )

        try:

            time.sleep(300)

        except KeyboardInterrupt:

            print(
                "\nBilling checker stopped."
            )

            break
