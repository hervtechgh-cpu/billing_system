
from datetime import datetime, date

from mikrotik_control import (
    suspend_customer,
    restore_customer,
    get_customer_mapping
)

from action_logger import log_action


# ============================================================
# BILLING SETTINGS
# ============================================================

GRACE_PERIOD_DAYS = 3


# ============================================================
# SAFE FLOAT CONVERSION
# ============================================================

def safe_float(value):
    """
    Safely convert a value to float.
    """

    try:
        if value is None or value == "":
            return 0.0

        return float(value)

    except (TypeError, ValueError):
        return 0.0


# ============================================================
# DATE PARSER
# ============================================================

def parse_date(value):
    """
    Convert a QuickBooks date value into a Python date object.
    """

    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(
            str(value)[:10],
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return None


# ============================================================
# PAYMENT ANALYSIS
# ============================================================

def analyze_payments(payments=None):
    """
    Analyze payment records.

    Supports normalized records:

        Amount
        UnappliedAmount

    and raw QuickBooks records:

        TotalAmt
        UnappliedAmt
    """

    payments = payments or []

    total_paid = 0.0
    total_unapplied = 0.0

    for payment in payments:

        amount = payment.get("Amount")

        if amount is None:
            amount = payment.get(
                "TotalAmt",
                0
            )

        unapplied = payment.get(
            "UnappliedAmount"
        )

        if unapplied is None:
            unapplied = payment.get(
                "UnappliedAmt",
                0
            )

        total_paid += safe_float(amount)

        total_unapplied += safe_float(
            unapplied
        )

    return {
        "total_paid": total_paid,
        "total_unapplied": total_unapplied
    }


# ============================================================
# CUSTOMER PAYMENT SUMMARY
# ============================================================

def get_customer_payment_summary(payments=None):
    """
    Calculate payment information for one customer.
    """

    payment_summary = analyze_payments(
        payments
    )

    return {
        "total_paid": payment_summary[
            "total_paid"
        ],

        "total_unapplied": payment_summary[
            "total_unapplied"
        ]
    }


# ============================================================
# CALCULATE CUSTOMER STATUS
# ============================================================

def calculate_customer_status(
    customer_balance,
    invoices,
    payments=None
):
    """
    Determine customer billing status.

    Rules:

    Negative balance
        -> PAID / CUSTOMER CREDIT

    Zero balance
        -> PAID

    Positive balance with no overdue invoice
        -> GRACE_PERIOD

    Positive balance and <= 3 days overdue
        -> GRACE_PERIOD

    Positive balance and > 3 days overdue
        -> SUSPEND

    Only invoices with an outstanding balance
    are considered when determining overdue status.
    """

    customer_balance = safe_float(
        customer_balance
    )

    invoices = invoices or []
    payments = payments or []

    # ========================================================
    # PAYMENT SUMMARY
    # ========================================================

    payment_summary = (
        get_customer_payment_summary(
            payments
        )
    )

    total_paid = payment_summary[
        "total_paid"
    ]

    total_unapplied = payment_summary[
        "total_unapplied"
    ]

    # ========================================================
    # CUSTOMER CREDIT
    # ========================================================

    if customer_balance < 0:

        return {
            "status": "PAID",
            "reason": "CUSTOMER CREDIT",
            "days_overdue": 0,
            "total_paid": total_paid,
            "unapplied_payment":
                total_unapplied
        }

    # ========================================================
    # ZERO BALANCE
    # ========================================================

    if customer_balance == 0:

        return {
            "status": "PAID",
            "reason": "ZERO BALANCE",
            "days_overdue": 0,
            "total_paid": total_paid,
            "unapplied_payment":
                total_unapplied
        }

    # ========================================================
    # FIND OUTSTANDING OVERDUE INVOICES
    # ========================================================

    today = date.today()

    maximum_days_overdue = 0

    for invoice in invoices:

        invoice_balance = safe_float(
            invoice.get("Balance")
        )

        # Ignore invoices that are already paid.
        if invoice_balance <= 0:
            continue

        due_date = parse_date(
            invoice.get("DueDate")
        )

        # Cannot calculate overdue status
        # without a valid due date.
        if not due_date:
            continue

        days_overdue = (
            today - due_date
        ).days

        if days_overdue > maximum_days_overdue:

            maximum_days_overdue = (
                days_overdue
            )

    # ========================================================
    # NOT YET DUE
    # ========================================================

    if maximum_days_overdue <= 0:

        return {
            "status": "GRACE_PERIOD",
            "reason": "INVOICE NOT YET DUE",
            "days_overdue": 0,
            "total_paid": total_paid,
            "unapplied_payment":
                total_unapplied
        }

    # ========================================================
    # GRACE PERIOD
    # ========================================================

    if maximum_days_overdue <= GRACE_PERIOD_DAYS:

        return {
            "status": "GRACE_PERIOD",
            "reason": (
                f"{maximum_days_overdue} "
                "DAY(S) OVERDUE"
            ),
            "days_overdue":
                maximum_days_overdue,
            "total_paid": total_paid,
            "unapplied_payment":
                total_unapplied
        }

    # ========================================================
    # SUSPEND
    # ========================================================

    return {
        "status": "SUSPEND",
        "reason": (
            f"{maximum_days_overdue} "
            "DAY(S) OVERDUE"
        ),
        "days_overdue":
            maximum_days_overdue,
        "total_paid": total_paid,
        "unapplied_payment":
            total_unapplied
    }


# ============================================================
# PROCESS ONE CUSTOMER
# ============================================================

def process_customer(
    customer_id,
    customer_name,
    customer_balance,
    invoices=None,
    payments=None
):
    """
    Process one QuickBooks customer.

    MikroTik actions remain DRY RUN according
    to mikrotik_control.py.
    """

    invoices = invoices or []
    payments = payments or []

    customer_id = str(
        customer_id
    )

    customer_balance = safe_float(
        customer_balance
    )

    # ========================================================
    # BILLING STATUS
    # ========================================================

    billing_status = calculate_customer_status(
        customer_balance=customer_balance,
        invoices=invoices,
        payments=payments
    )

    status = billing_status[
        "status"
    ]

    reason = billing_status[
        "reason"
    ]

    days_overdue = billing_status[
        "days_overdue"
    ]

    total_paid = billing_status[
        "total_paid"
    ]

    unapplied_payment = (
        billing_status[
            "unapplied_payment"
        ]
    )

    # ========================================================
    # DEFAULT VALUES
    # ========================================================

    action = "NO ACTION"

    username = ""

    ip_address = ""

    enabled = False

    # ========================================================
    # GET MIKROTIK MAPPING
    # ========================================================

    mapping = get_customer_mapping(
        customer_id
    )

    if mapping:

        username = mapping.get(
            "mikrotik_username",
            ""
        )

        ip_address = mapping.get(
            "mikrotik_ip",
            ""
        )

        enabled = mapping.get(
            "enabled",
            False
        )

    # ========================================================
    # PAID CUSTOMER
    # ========================================================

    if status == "PAID":

        if mapping and enabled:

            if username and ip_address:

                result = restore_customer(
                    customer_id,
                    customer_name
                )

                if result in (
                    "SIMULATED_RESTORE",
                    "RESTORED"
                ):

                    action = "RESTORE"

    # ========================================================
    # SUSPEND CUSTOMER
    # ========================================================

    elif status == "SUSPEND":

        if mapping and enabled:

            if username and ip_address:

                result = suspend_customer(
                    customer_id,
                    customer_name
                )

                if result in (
                    "SIMULATED_SUSPEND",
                    "SUSPENDED"
                ):

                    action = "SUSPEND"

    # ========================================================
    # GRACE PERIOD
    # ========================================================

    elif status == "GRACE_PERIOD":

        action = "NO ACTION"

    # ========================================================
    # LOG ACTION
    # ========================================================

    log_action(
        customer_id,
        customer_name,
        customer_balance,
        status,
        username,
        ip_address,
        action,
        reason
    )

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {
        "Id": customer_id,

        "DisplayName": customer_name,

        "Balance": customer_balance,

        "Status": status,

        "Reason": reason,

        "Action": action,

        "Username": username,

        "IP": ip_address,

        "Enabled": enabled,

        "DaysOverdue": days_overdue,

        "TotalPaid": total_paid,

        "UnappliedPayment":
            unapplied_payment
    }


# ============================================================
# PROCESS ALL CUSTOMERS
# ============================================================

def process_all_customers(
    customers,
    invoices,
    payments=None
):
    """
    Process all QuickBooks customers.

    Groups invoices and payments by
    QuickBooks Customer ID.
    """

    payments = payments or []

    # ========================================================
    # GROUP INVOICES
    # ========================================================

    invoices_by_customer = {}

    for invoice in invoices or []:

        customer_id = str(
            invoice.get(
                "CustomerRef",
                {}
            ).get(
                "value"
            )
        )

        if customer_id not in invoices_by_customer:

            invoices_by_customer[
                customer_id
            ] = []

        billing_invoice = {
            "InvoiceID":
                invoice.get("Id"),

            "CustomerID":
                customer_id,

            "CustomerName":
                invoice.get(
                    "CustomerRef",
                    {}
                ).get(
                    "name",
                    "Unknown Customer"
                ),

            "Balance":
                safe_float(
                    invoice.get(
                        "Balance"
                    )
                ),

            "TotalAmount":
                safe_float(
                    invoice.get(
                        "TotalAmt"
                    )
                ),

            "DueDate":
                invoice.get(
                    "DueDate"
                ),

            "TxnDate":
                invoice.get(
                    "TxnDate"
                )
        }

        invoices_by_customer[
            customer_id
        ].append(
            billing_invoice
        )

    # ========================================================
    # GROUP PAYMENTS
    # ========================================================

    payments_by_customer = {}

    for payment in payments:

        customer_id = str(
            payment.get(
                "CustomerRef",
                {}
            ).get(
                "value"
            )
        )

        if customer_id not in payments_by_customer:

            payments_by_customer[
                customer_id
            ] = []

        payment_record = {
            "PaymentID":
                payment.get("Id"),

            "Amount":
                safe_float(
                    payment.get(
                        "TotalAmt",
                        payment.get(
                            "Amount",
                            0
                        )
                    )
                ),

            "UnappliedAmount":
                safe_float(
                    payment.get(
                        "UnappliedAmt",
                        payment.get(
                            "UnappliedAmount",
                            0
                        )
                    )
                ),

            "TxnDate":
                payment.get(
                    "TxnDate"
                )
        }

        payments_by_customer[
            customer_id
        ].append(
            payment_record
        )

    # ========================================================
    # PROCESS CUSTOMERS
    # ========================================================

    results = []

    for customer in customers or []:

        customer_id = str(
            customer.get("Id")
        )

        customer_name = customer.get(
            "DisplayName",
            "Unknown Customer"
        )

        # ====================================================
        # IMPORTANT QUICKBOOKS BALANCE LOGIC
        # ====================================================
        #
        # BalanceWithJobs includes the balance of the
        # customer plus any associated Jobs.
        #
        # This is important for customers such as:
        #
        # Shara Barnett
        # Balance:         0.00
        # BalanceWithJobs: 274.50
        #
        # If BalanceWithJobs is available, use it.
        # Otherwise fall back to Balance.
        # ====================================================

        customer_balance = safe_float(
            customer.get(
                "BalanceWithJobs",
                customer.get(
                    "Balance"
                )
            )
        )

        customer_invoices = (
            invoices_by_customer.get(
                customer_id,
                []
            )
        )

        customer_payments = (
            payments_by_customer.get(
                customer_id,
                []
            )
        )

        result = process_customer(
            customer_id=customer_id,

            customer_name=customer_name,

            customer_balance=customer_balance,

            invoices=customer_invoices,

            payments=customer_payments
        )

        results.append(
            result
        )

    return results


# ============================================================
# SUMMARIZE RESULTS
# ============================================================

def summarize_results(results):
    """
    Produce billing summary.
    """

    results = results or []

    summary = {
        "total_customers":
            len(results),

        "paid":
            0,

        "grace_period":
            0,

        "suspend":
            0,

        "credit":
            0,

        "gross_outstanding":
            0.0,

        "customer_credits":
            0.0,

        "net_outstanding":
            0.0,

        "unapplied_payments":
            0.0
    }

    for result in results:

        status = result.get(
            "Status"
        )

        balance = safe_float(
            result.get(
                "Balance"
            )
        )

        unapplied = safe_float(
            result.get(
                "UnappliedPayment"
            )
        )

        # ====================================================
        # STATUS COUNTS
        # ====================================================

        if status == "PAID":

            summary[
                "paid"
            ] += 1

        elif status == "GRACE_PERIOD":

            summary[
                "grace_period"
            ] += 1

        elif status == "SUSPEND":

            summary[
                "suspend"
            ] += 1

        # ====================================================
        # FINANCIAL TOTALS
        # ====================================================

        if balance > 0:

            summary[
                "gross_outstanding"
            ] += balance

        elif balance < 0:

            summary[
                "customer_credits"
            ] += abs(
                balance
            )

            summary[
                "credit"
            ] += 1

        # ====================================================
        # UNAPPLIED PAYMENTS
        # ====================================================

        summary[
            "unapplied_payments"
        ] += unapplied

    # ========================================================
    # NET OUTSTANDING
    # ========================================================

    summary[
        "net_outstanding"
    ] = (
        summary[
            "gross_outstanding"
        ]
        -
        summary[
            "customer_credits"
        ]
    )

    # ========================================================
    # RETURN SUMMARY
    # ========================================================

    return summary
