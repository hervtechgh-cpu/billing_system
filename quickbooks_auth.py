import os
import time
import requests

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

CLIENT_ID = os.getenv("QB_CLIENT_ID")
CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("QB_REFRESH_TOKEN")


print("CLIENT_ID loaded:", bool(CLIENT_ID))
print("CLIENT_SECRET loaded:", bool(CLIENT_SECRET))
print("REFRESH_TOKEN loaded:", bool(REFRESH_TOKEN))


# ============================================================
# QUICKBOOKS TOKEN URL
# ============================================================

TOKEN_URL = (
    "https://oauth.platform.intuit.com/"
    "oauth2/v1/tokens/bearer"
)


# ============================================================
# ACCESS TOKEN CACHE
# ============================================================

_access_token = None
_access_token_expires_at = 0

# Keep the latest refresh token in memory.
# QuickBooks may rotate the refresh token.
_current_refresh_token = REFRESH_TOKEN


# ============================================================
# GET ACCESS TOKEN
# ============================================================

def get_access_token():

    global _access_token
    global _access_token_expires_at
    global _current_refresh_token

    # --------------------------------------------------------
    # REUSE EXISTING ACCESS TOKEN IF STILL VALID
    # --------------------------------------------------------

    current_time = time.time()

    if (
        _access_token
        and current_time < (_access_token_expires_at - 60)
    ):

        print("Using cached QuickBooks access token.")

        return _access_token

    # --------------------------------------------------------
    # CHECK REFRESH TOKEN
    # --------------------------------------------------------

    if not _current_refresh_token:

        print("No QuickBooks refresh token available.")

        return None

    # --------------------------------------------------------
    # REQUEST NEW ACCESS TOKEN
    # --------------------------------------------------------

    try:

        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": _current_refresh_token
            },
            auth=(
                CLIENT_ID,
                CLIENT_SECRET
            ),
            headers={
                "Accept": "application/json"
            },
            timeout=30
        )

    except requests.RequestException as e:

        print(
            "QuickBooks authentication connection error:"
        )

        print(e)

        return None

    # --------------------------------------------------------
    # CHECK RESPONSE
    # --------------------------------------------------------

    if response.status_code != 200:

        print(
            "QuickBooks authentication failed."
        )

        print(
            "Status:",
            response.status_code
        )

        print(
            response.text
        )

        return None

    # --------------------------------------------------------
    # PARSE RESPONSE
    # --------------------------------------------------------

    try:

        token_data = response.json()

    except ValueError:

        print(
            "QuickBooks returned invalid authentication JSON."
        )

        return None

    # --------------------------------------------------------
    # ACCESS TOKEN
    # --------------------------------------------------------

    new_access_token = token_data.get(
        "access_token"
    )

    if not new_access_token:

        print(
            "No access token returned."
        )

        return None

    # --------------------------------------------------------
    # TOKEN EXPIRATION
    # --------------------------------------------------------

    expires_in = token_data.get(
        "expires_in",
        3600
    )

    try:

        expires_in = int(
            expires_in
        )

    except (
        TypeError,
        ValueError
    ):

        expires_in = 3600

    # --------------------------------------------------------
    # CACHE ACCESS TOKEN
    # --------------------------------------------------------

    _access_token = new_access_token

    _access_token_expires_at = (
        time.time() + expires_in
    )

    # --------------------------------------------------------
    # REFRESH TOKEN ROTATION
    # --------------------------------------------------------

    new_refresh_token = token_data.get(
        "refresh_token"
    )

    if new_refresh_token:

        _current_refresh_token = (
            new_refresh_token
        )

        print(
            "A new refresh token was returned."
        )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    print(
        "Authentication successful!"
    )

    print(
        "Access token received successfully."
    )

    print(
        "Token length:",
        len(_access_token)
    )

    print(
        "Access token cached."
    )

    return _access_token


# ============================================================
# TEST AUTHENTICATION
# ============================================================

if __name__ == "__main__":

    token = get_access_token()

    if token:

        print(
            "QuickBooks authentication test successful."
        )