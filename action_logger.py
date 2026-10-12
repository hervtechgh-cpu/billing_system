import csv
import os
from datetime import datetime


# --------------------------------
# LOG FILE
# --------------------------------

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

LOG_FILE = os.path.join(
    BASE_DIR,
    "billing_action_log.csv"
)


# --------------------------------
# LOG ACTION
# --------------------------------

def log_action(
    customer_id,
    customer_name,
    outstanding,
    status,
    mikrotik_username,
    mikrotik_ip,
    action,
    result
):

    file_exists = os.path.exists(
        LOG_FILE
    )

    with open(
        LOG_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        # Create column headings
        # only when the file is new
        if not file_exists:

            writer.writerow([
                "DateTime",
                "CustomerID",
                "CustomerName",
                "Outstanding",
                "Status",
                "MikroTikUsername",
                "MikroTikIP",
                "Action",
                "Result"
            ])

        writer.writerow([
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            customer_id,
            customer_name,
            f"{outstanding:.2f}",
            status,
            mikrotik_username,
            mikrotik_ip,
            action,
            result
        ])

        print(
            f"[LOG] Action recorded for "
            f"{customer_name}"
        )