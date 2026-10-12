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
# HELPER FUNCTIONS
# ============================================================

def safe_float(value):
    """
    Safely convert a value to float.
    """
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def parse_date(value):
    """
    Convert a QuickBooks date string into a date object.
    """
    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        return None


# ============================================================
# CALCULATE CUSTOMER STATUS
# ============================================================

def calculate_customer_status(
    customer_balance,
    invoices=None,
    payments=None
):
    """
    Determine customer's billing status.

    Rules:

    Negative balance
        -> PAID / CUSTOMER HAS CREDIT

    Zero balance
        -> PAID

    Future invoice
        -> GRACE_PERIOD

    1-3 days overdue
        -> GRACE_PERIOD

    More than 3 days overdue
        -> SUSPEND

    QuickBooks Customer Balance is used as the
    primary outstanding balance.
    """

    customer_balance = safe_float(
        customer_balance
    )

    invoices = invoices or []
    payments = payments or []

    # --------------------------------------------------------
    # CUSTOMER HAS CREDIT
    # --------------------------------------------------------

    if customer_balance < 0:

        return {
            "status": "PAID",
            "reason": "CUSTOMER HAS CREDIT",
            "balance": customer_balance,
            "days_overdue": 0
        }

    # --------------------------------------------------------
    # ZERO BALANCE
    # --------------------------------------------------------

    if customer_balance == 0:

        return {
            "status": "PAID",
            "reason": "NO OUTSTANDING BALANCE",
            "balance": 0.0,
            "days_overdue": 0
        }

    # --------------------------------------------------------
    # FIND OPEN INVOICES
    # --------------------------------------------------------

    outstanding_invoices = []

    for invoice in invoices:

        balance = safe_float(
            invoice.get("Balance")
        )

        if balance <= 0:
            continue

        due_date = parse_date(
            invoice.get("DueDate")
        )

        outstanding_invoices.append({
            "balance": balance,
            "due_date": due_date
        })

    # --------------------------------------------------------
    # OUTSTANDING BALANCE BUT NO OPEN INVOICE
    # --------------------------------------------------------

    if not outstanding_invoices:

        return {
            "status": "SUSPEND",
            "reason": "CUSTOMER HAS OUTSTANDING BALANCE",
            "balance": customer_balance,
            "days_overdue": 0
        }

    # --------------------------------------------------------
    # CALCULATE OVERDUE DAYS
    # --------------------------------------------------------

    today = date.today()

    max_days_overdue = 0

    for invoice in outstanding_invoices:

        due_date = invoice["due_date"]

        if not due_date:
            continue

        days_overdue = (
            today - due_date
        ).days

        if days_overdue > max_days_overdue:
            max_days_overdue = days_overdue

    # --------------------------------------------------------
    # INVOICE NOT YET DUE
    # --------------------------------------------------------

    if max_days_overdue <= 0:

        return {
            "status": "GRACE_PERIOD",
            "reason": "INVOICE NOT YET DUE",
            "balance": customer_balance,
            "days_overdue": 0
        }

    # --------------------------------------------------------
    # WITHIN GRACE PERIOD
    # --------------------------------------------------------

    if max_days_overdue <= GRACE_PERIOD_DAYS:

        return {
            "status": "GRACE_PERIOD",
            "reason": (
                f"WITHIN {GRACE_PERIOD_DAYS}-DAY "
                f"GRACE PERIOD"
            ),
            "balance": customer_balance,
            "days_overdue": max_days_overdue
        }

    # --------------------------------------------------------
    # OVERDUE BEYOND GRACE PERIOD
    # --------------------------------------------------------

    return {
        "status": "SUSPEND",
        "reason": "PAYMENT OVERDUE",
        "balance": customer_balance,
        "days_overdue": max_days_overdue
    }


# ============================================================
# PROCESS ONE CUSTOMER
# ============================================================

def process_customer(
    customer,
    invoices=None,
    payments=None
):
    """
    Process one QuickBooks customer.

    Determines billing status and required MikroTik action.
    """

    invoices = invoices or []
    payments = payments or []

    # --------------------------------------------------------
    # CUSTOMER INFORMATION
    # --------------------------------------------------------

    customer_id = str(
        customer.get("Id", "")
    )

    customer_name = (
        customer.get("DisplayName")
        or customer.get("FullyQualifiedName")
        or "Unknown Customer"
    )

    customer_balance = safe_float(
        customer.get("Balance")
    )

    # --------------------------------------------------------
    # CALCULATE BILLING STATUS
    # --------------------------------------------------------

    billing_result = calculate_customer_status(
        customer_balance=customer_balance,
        invoices=invoices,
        payments=payments
    )

    status = billing_result["status"]
    reason = billing_result["reason"]
    days_overdue = billing_result["days_overdue"]

    # --------------------------------------------------------
    # GET MIKROTIK MAPPING
    # IMPORTANT:
    # Use QuickBooks CUSTOMER ID, not customer name.
    # --------------------------------------------------------

    mapping = get_customer_mapping(
        customer_id
    )

    if mapping is None:
        mapping = {}

    # --------------------------------------------------------
    # READ CORRECT JSON FIELD NAMES
    # --------------------------------------------------------

    username = mapping.get(
        "mikrotik_username"
    )

    ip_address = mapping.get(
        "mikrotik_ip"
    )

    enabled = mapping.get(
        "enabled",
        False
    )

    # --------------------------------------------------------
    # DEFAULT ACTION
    # --------------------------------------------------------

    action = "NO ACTION"
    result = reason

    # ========================================================
    # CUSTOMER HAS CREDIT
    # ========================================================

    if customer_balance < 0:

        action = "NO ACTION"
        result = "CUSTOMER HAS CREDIT"

        log_action(
            customer_id,
            customer_name,
            customer_balance,
            "PAID",
            username or "",
            ip_address or "",
            action,
            result
        )

        return {
            "Id": customer_id,
            "DisplayName": customer_name,
            "Balance": customer_balance,
            "Status": "PAID",
            "Reason": reason,
            "Action": action,
            "Username": username,
            "IP": ip_address,
            "Enabled": enabled,
            "DaysOverdue": 0
        }

    # ========================================================
    # PAID
    # ========================================================

    if status == "PAID":

        if username and enabled:

            action = "RESTORE"

            try:

                restore_customer(
                    customer_id,
                    customer_name
                )

                result = "CUSTOMER RESTORED"

            except Exception as e:

                action = "RESTORE ERROR"
                result = str(e)

        else:

            action = "NO ACTION"

            if not username:
                result = "NO MIKROTIK MAPPING"
            elif not enabled:
                result = "MIKROTIK MAPPING DISABLED"
            else:
                result = "NO MIKROTIK ACTION REQUIRED"

        log_action(
            customer_id,
            customer_name,
            customer_balance,
            status,
            username or "",
            ip_address or "",
            action,
            result
        )

    # ========================================================
    # GRACE PERIOD
    # ========================================================

    elif status == "GRACE_PERIOD":

        action = "NO ACTION"

        result = reason

        log_action(
            customer_id,
            customer_name,
            customer_balance,
            status,
            username or "",
            ip_address or "",
            action,
            result
        )

    # ========================================================
    # SUSPEND
    # ========================================================

    elif status == "SUSPEND":

        if username and enabled:

            action = "SUSPEND"

            try:

                suspend_customer(
                    customer_id,
                    customer_name
                )

                result = "CUSTOMER SUSPENDED"

            except Exception as e:

                action = "SUSPEND ERROR"
                result = str(e)

        else:

            action = "NO ACTION"

            if not username:
                result = "NO MIKROTIK MAPPING"
            elif not enabled:
                result = "MIKROTIK MAPPING DISABLED"
            else:
                result = "NO MIKROTIK ACTION REQUIRED"

        log_action(
            customer_id,
            customer_name,
            customer_balance,
            status,
            username or "",
            ip_address or "",
            action,
            result
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
        "DaysOverdue": days_overdue
    }


# ============================================================
# PROCESS ALL CUSTOMERS
# ============================================================

def process_all_customers(
    customers,
    invoices=None,
    payments=None
):
    """
    Process all QuickBooks customers.

    Invoices are grouped by QuickBooks Customer ID.
    """

    invoices = invoices or []
    payments = payments or []

    # --------------------------------------------------------
    # GROUP INVOICES BY CUSTOMER ID
    # --------------------------------------------------------

    invoice_map = {}

    for invoice in invoices:

        customer_ref = invoice.get(
            "CustomerRef",
            {}
        )

        customer_id = str(
            customer_ref.get(
                "value",
                ""
            )
        )

        if not customer_id:
            continue

        if customer_id not in invoice_map:

            invoice_map[customer_id] = []

        invoice_map[customer_id].append(
            invoice
        )

    # --------------------------------------------------------
    # PROCESS CUSTOMERS
    # --------------------------------------------------------

    results = []

    for customer in customers:

        customer_id = str(
            customer.get(
                "Id",
                ""
            )
        )

        customer_invoices = invoice_map.get(
            customer_id,
            []
        )

        result = process_customer(
            customer=customer,
            invoices=customer_invoices,
            payments=payments
        )

        results.append(
            result
        )

    return results


# ============================================================
# SUMMARY
# ============================================================

def summarize_results(results):
    """
    Produce summary information for the dashboard.
    """

    summary = {
        "total_customers": len(results),
        "paid": 0,
        "grace_period": 0,
        "suspend": 0,
        "credit": 0,
        "total_balance": 0.0
    }

    for result in results:

        balance = safe_float(
            result.get("Balance")
        )

        # Only positive balances count as money owed.
        summary["total_balance"] += max(
            balance,
            0
        )

        status = result.get(
            "Status"
        )

        if status == "PAID":

            summary["paid"] += 1

            if balance < 0:
                summary["credit"] += 1

        elif status == "GRACE_PERIOD":

            summary["grace_period"] += 1

        elif status == "SUSPEND":

            summary["suspend"] += 1

    return summary