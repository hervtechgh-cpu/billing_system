import json
import os


# ============================================================
# SAFETY SWITCH
# ============================================================

# True  = simulate MikroTik actions
# False = perform real MikroTik actions later
DRY_RUN = True


# ============================================================
# FILE LOCATIONS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

MAPPING_FILE = os.path.join(
    BASE_DIR,
    "customer_mikrotik_map.json"
)

STATE_FILE = os.path.join(
    BASE_DIR,
    "mikrotik_state.json"
)


# ============================================================
# LOAD CUSTOMER MAPPING
# ============================================================

def load_customer_mapping():

    if not os.path.exists(MAPPING_FILE):

        print(
            "ERROR: customer_mikrotik_map.json "
            "not found."
        )

        return {}

    try:

        with open(
            MAPPING_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except json.JSONDecodeError as e:

        print(
            "ERROR: Invalid JSON mapping file."
        )

        print(e)

        return {}


# ============================================================
# LOAD MIKROTIK STATE
# ============================================================

def load_mikrotik_state():

    if not os.path.exists(STATE_FILE):
        return {}

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except json.JSONDecodeError:

        print(
            "WARNING: Invalid mikrotik_state.json. "
            "Starting with empty state."
        )

        return {}


# ============================================================
# SAVE MIKROTIK STATE
# ============================================================

def save_mikrotik_state(state):

    with open(
        STATE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            state,
            file,
            indent=4
        )


# ============================================================
# FIND CUSTOMER BY QUICKBOOKS ID
# ============================================================

def get_customer_mapping(customer_id):

    customers = load_customer_mapping()

    customer = customers.get(
        str(customer_id)
    )

    if not customer:

        print(
            f"[MAPPING] No MikroTik mapping "
            f"found for QuickBooks Customer ID: "
            f"{customer_id}"
        )

        return None

    return customer


# ============================================================
# GET CURRENT MIKROTIK STATE
# ============================================================

def get_customer_state(customer_id):

    state = load_mikrotik_state()

    return state.get(
        str(customer_id),
        "UNKNOWN"
    )


# ============================================================
# SET CURRENT MIKROTIK STATE
# ============================================================

def set_customer_state(
    customer_id,
    status
):

    state = load_mikrotik_state()

    state[str(customer_id)] = status

    save_mikrotik_state(state)


# ============================================================
# SUSPEND CUSTOMER
# ============================================================

def suspend_customer(
    customer_id,
    customer_name
):

    customer = get_customer_mapping(
        customer_id
    )

    if not customer:

        print(
            "[MAPPING] Cannot suspend "
            f"{customer_name}."
        )

        return "NO_MAPPING"

    username = customer.get(
        "mikrotik_username"
    )

    ip_address = customer.get(
        "mikrotik_ip"
    )

    enabled = customer.get(
        "enabled",
        False
    )

    if not enabled:

        print(
            f"[MAPPING] MikroTik control "
            f"disabled for: {customer_name}"
        )

        return "DISABLED"

    # ========================================================
    # CHECK CURRENT STATE
    # ========================================================

    current_state = get_customer_state(
        customer_id
    )

    if current_state == "SUSPENDED":

        print(
            f"[MIKROTIK] {customer_name} "
            "is already SUSPENDED."
        )

        return "ALREADY_SUSPENDED"

    # ========================================================
    # DISPLAY CUSTOMER
    # ========================================================

    print(
        "\n[MikroTik Customer]"
    )

    print(
        f"Customer: {customer_name}"
    )

    print(
        f"QuickBooks ID: {customer_id}"
    )

    print(
        f"Username: {username}"
    )

    print(
        f"IP Address: {ip_address}"
    )

    # ========================================================
    # DRY RUN
    # ========================================================

    if DRY_RUN:

        print(
            "[DRY RUN] Would SUSPEND "
            "this MikroTik account."
        )

        # Simulate successful suspension
        set_customer_state(
            customer_id,
            "SUSPENDED"
        )

        return "SIMULATED_SUSPEND"

    # ========================================================
    # REAL MIKROTIK ACTION
    # ========================================================

    print(
        "[MIKROTIK] Suspending service..."
    )

    # Real MikroTik code will be added later.

    set_customer_state(
        customer_id,
        "SUSPENDED"
    )

    return "SUSPENDED"


# ============================================================
# RESTORE CUSTOMER
# ============================================================

def restore_customer(
    customer_id,
    customer_name
):

    customer = get_customer_mapping(
        customer_id
    )

    if not customer:

        print(
            "[MAPPING] Cannot restore "
            f"{customer_name}."
        )

        return "NO_MAPPING"

    username = customer.get(
        "mikrotik_username"
    )

    ip_address = customer.get(
        "mikrotik_ip"
    )

    enabled = customer.get(
        "enabled",
        False
    )

    if not enabled:

        print(
            f"[MAPPING] MikroTik control "
            f"disabled for: {customer_name}"
        )

        return "DISABLED"

    # ========================================================
    # CHECK CURRENT STATE
    # ========================================================

    current_state = get_customer_state(
        customer_id
    )

    if current_state == "ACTIVE":

        print(
            f"[MIKROTIK] {customer_name} "
            "is already ACTIVE."
        )

        return "ALREADY_ACTIVE"

    # ========================================================
    # DISPLAY CUSTOMER
    # ========================================================

    print(
        "\n[MikroTik Customer]"
    )

    print(
        f"Customer: {customer_name}"
    )

    print(
        f"QuickBooks ID: {customer_id}"
    )

    print(
        f"Username: {username}"
    )

    print(
        f"IP Address: {ip_address}"
    )

    # ========================================================
    # DRY RUN
    # ========================================================

    if DRY_RUN:

        print(
            "[DRY RUN] Would RESTORE "
            "this MikroTik account."
        )

        # Simulate successful restore
        set_customer_state(
            customer_id,
            "ACTIVE"
        )

        return "SIMULATED_RESTORE"

    # ========================================================
    # REAL MIKROTIK ACTION
    # ========================================================

    print(
        "[MIKROTIK] Restoring service..."
    )

    # Real MikroTik code will be added later.

    set_customer_state(
        customer_id,
        "ACTIVE"
    )

    return "RESTORED"