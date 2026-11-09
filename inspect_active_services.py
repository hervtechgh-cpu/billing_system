
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
        "PPP Accounts": ("ppp", "secret"),
        "Hotspot Server Configuration": ("ip", "hotspot"),
        "Hotspot Accounts": ("ip", "hotspot", "user"),
        "Active Hotspot Sessions": ("ip", "hotspot", "active"),
        "DHCP Servers": ("ip", "dhcp-server"),
        "Simple Queues": ("queue", "simple"),
        "Queue Trees": ("queue", "tree"),
    }

    try:
        print("\nMIKROTIK CONFIGURATION REPORT")
        print("=" * 45)

        for description, path in checks.items():
            print(f"\n{description}")

            try:
                records = list(router.path(*path).select())
                print("Records found:", len(records))

                if "Server Configuration" in description:
                    for record in records:
                        print({
                            key: record.get(key)
                            for key in (
                                "name", "interface",
                                "service-name", "disabled",
                                "profile"
                            )
                            if key in record
                        })

            except Exception as error:
                print("Inspection error:", type(error).__name__)
                print(str(error))

    finally:
        router.close()
        print("\nConnection closed safely.")


if __name__ == "__main__":
    main()
