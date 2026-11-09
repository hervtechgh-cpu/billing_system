
import os
import ssl

from dotenv import load_dotenv
from librouteros import connect

# Load MikroTik credentials and settings from .env
load_dotenv()

HOST = os.getenv("MIKROTIK_HOST")
PORT = int(os.getenv("MIKROTIK_PORT", "8729"))
USERNAME = os.getenv("MIKROTIK_USERNAME")
PASSWORD = os.getenv("MIKROTIK_PASSWORD")

# CA certificate exported from the MikroTik router
CA_CERTIFICATE = "cert_export_billing-ca-signed.crt"


def main():
    # Check that connection settings are available
    if not all([HOST, USERNAME, PASSWORD]):
        print("ERROR: MikroTik settings are missing from .env")
        return

    # Confirm that the CA certificate exists
    if not os.path.isfile(CA_CERTIFICATE):
        print("ERROR: CA certificate file was not found.")
        print("Expected file:", os.path.abspath(CA_CERTIFICATE))
        return

    try:
        # Load the exported CA certificate as a trusted certificate
        tls_context = ssl.create_default_context(
            cafile=CA_CERTIFICATE
        )

        print("Connecting securely to MikroTik...")
        print("Host:", HOST)
        print("Port:", PORT)
        print("Certificate verification: ENABLED")

        # Establish the secure MikroTik API connection
        router = connect(
            host=HOST,
            port=PORT,
            username=USERNAME,
            password=PASSWORD,
            timeout=10,
            ssl_wrapper=lambda sock: tls_context.wrap_socket(
                sock,
                server_hostname=HOST
            ),
        )

        print("\nSUCCESS: Secure connection established.")

        try:
            # Read router identity
            print("\nRouter identity:")
            identity = list(
                router.path("system", "identity").select()
            )
            print(identity)

            # Read router system resources
            print("\nSystem resources:")
            resources = list(
                router.path("system", "resource").select()
            )
            print(resources)

        finally:
            # Close the connection safely
            router.close()
            print("\nConnection closed safely.")

    except ssl.SSLCertVerificationError as error:
        print("\nSSL CERTIFICATE VERIFICATION FAILED.")
        print("Details:", str(error))
        print("Check that the exported CA certificate is correct.")

    except Exception as error:
        print("\nConnection test failed.")
        print("Error type:", type(error).__name__)
        print("Details:", str(error))


if __name__ == "__main__":
    main()
