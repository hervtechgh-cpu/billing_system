
import os
import ssl

from dotenv import load_dotenv
from librouteros import connect

load_dotenv()

HOST = os.getenv("MIKROTIK_HOST")
PORT = int(os.getenv("MIKROTIK_PORT", "8729"))
USERNAME = os.getenv("MIKROTIK_USERNAME")
PASSWORD = os.getenv("MIKROTIK_PASSWORD")

CA_CERTIFICATE = "cert_export_billing-ca-signed.crt"


def main():

    tls_context = ssl.create_default_context(cafile=CA_CERTIFICATE)

    router = connect(
        host=HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
        timeout=10,
        ssl_wrapper=lambda sock: tls_context.wrap_socket(
            sock, server_hostname=HOST
        ),
    )

    checks = {
        "PPPoE Server Configuration": (
            "interface", "pppoe-server", "server"
        ),
        "Active PPP Connections": ("ppp", "active"),
        "Hotspot Server Configuration": (
            "ip", "hotspot", "server"
        ),
        "Active Hotspot Sessions": (
            "ip", "hotspot", "active"
        ),
    }

    try:
        print("\nMIKROTIK ACTIVE SERVICE INSPECTION")
        print("=" * 45)

        for description, path in checks.items():
            try:
                records = list(router.path(*path).select())

                print(f"\n{description}")
                print("Records found:", len(records))

                # Show only non-sensitive configuration information
                if "Configuration" in description:
                    for record in records:
                        print({
                            key: record.get(key)
                            for key in ("name", "interface", "service-name",
                                        "disabled")
                            if key in record
                        })

            except Exception as error:
                print(f"\n{description}: Unable to inspect")
                print(type(error).__name__, str(error))

        print("\nInspection completed.")

    finally:
        router.close()
        print("Connection closed safely.")


if __name__ == "__main__":
    main()
