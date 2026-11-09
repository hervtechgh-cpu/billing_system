
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

    try:
        print("\nDHCP IP ADDRESS POOLS")
        print("=" * 40)

        pools = list(router.path("ip", "pool").select())

        for pool in pools:
            print({
                key: pool.get(key)
                for key in ("name", "ranges", "next-pool")
            })

        print("\nFIREWALL ADDRESS LISTS")
        print("=" * 40)

        lists = list(
            router.path("ip", "firewall", "address-list").select()
        )

        print("Address list entries:", len(lists))

        for item in lists:
            print({
                key: item.get(key)
                for key in (
                    "list", "address", "timeout", "disabled"
                )
            })

    finally:
        router.close()
        print("\nConnection closed safely.")


if __name__ == "__main__":
    main()
