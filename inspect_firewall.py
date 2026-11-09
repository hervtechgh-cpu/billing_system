
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

    tls_context = ssl.create_default_context(
        cafile=CA_CERTIFICATE
    )

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

    try:
        checks = {
            "FIREWALL FILTER RULES": (
                "ip", "firewall", "filter"
            ),
            "FIREWALL NAT RULES": (
                "ip", "firewall", "nat"
            ),
        }

        fields = (
            "chain",
            "action",
            "src-address",
            "dst-address",
            "src-address-list",
            "dst-address-list",
            "in-interface",
            "out-interface",
            "disabled",
            "comment",
        )

        for description, path in checks.items():

            print("\n" + description)
            print("=" * 45)

            records = list(router.path(*path).select())

            print("Rules found:", len(records))

            for record in records:
                print({
                    key: record.get(key)
                    for key in fields
                    if key in record
                })

        print("\nFirewall inspection completed.")

    finally:
        router.close()
        print("\nConnection closed safely.")


if __name__ == "__main__":
    main()
