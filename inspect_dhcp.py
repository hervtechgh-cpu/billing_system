
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
        print("\nDHCP SERVER DETAILS")
        print("=" * 40)

        servers = list(
            router.path("ip", "dhcp-server").select()
        )

        for server in servers:
            print({
                key: server.get(key)
                for key in (
                    "name",
                    "interface",
                    "address-pool",
                    "lease-time",
                    "disabled"
                )
            })

        print("\nDHCP NETWORK DETAILS")
        print("=" * 40)

        networks = list(
            router.path("ip", "dhcp-server", "network").select()
        )

        for network in networks:
            print({
                key: network.get(key)
                for key in (
                    "address",
                    "gateway",
                    "dns-server"
                )
            })

        print("\nInspection completed.")

    finally:
        router.close()
        print("Connection closed safely.")


if __name__ == "__main__":
    main()
