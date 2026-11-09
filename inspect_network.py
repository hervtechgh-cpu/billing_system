
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
    tls = ssl.create_default_context(cafile=CA_CERTIFICATE)

    router = connect(
        host=HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD,
        timeout=10,
        ssl_wrapper=lambda sock: tls.wrap_socket(
            sock, server_hostname=HOST
        ),
    )

    checks = {
        "IP ADDRESSES": (
            "ip", "address"
        ),
        "BRIDGE PORTS": (
            "interface", "bridge", "port"
        ),
        "INTERFACE LIST MEMBERS": (
            "interface", "list", "member"
        ),
        "IP ROUTES": (
            "ip", "route"
        ),
    }

    try:
        for title, path in checks.items():
            print("\n" + title)
            print("=" * 40)

            records = list(router.path(*path).select())
            print("Records found:", len(records))

            for record in records:
                print({
                    key: record.get(key)
                    for key in (
                        "address", "interface", "network",
                        "bridge", "disabled", "list",
                        "gateway", "dst-address", "active"
                    )
                    if key in record
                })

    finally:
        router.close()
        print("\nConnection closed safely.")


if __name__ == "__main__":
    main()
