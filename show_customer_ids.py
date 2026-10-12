from billing_checker import get_invoices


invoices = get_invoices()

customers = {}

for invoice in invoices:

    customer_ref = invoice.get(
        "CustomerRef",
        {}
    )

    customer_id = customer_ref.get(
        "value"
    )

    customer_name = customer_ref.get(
        "name",
        "Unknown Customer"
    )

    if customer_id:

        customers[customer_id] = customer_name


print("\n================================")
print("QUICKBOOKS CUSTOMER IDs")
print("================================")

for customer_id, customer_name in customers.items():

    print(
        f"ID: {customer_id} | "
        f"Customer: {customer_name}"
    )

print(
    "\nTotal customers:",
    len(customers)
)