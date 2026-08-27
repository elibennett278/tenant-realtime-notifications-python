import os

from src.notification_service import InfraiClient, TenantAccount, onboard_tenant


def main() -> None:
    client = InfraiClient()
    result = onboard_tenant(TenantAccount("acme", "acct-42", "admin-7"), client)
    print(result)


if __name__ == "__main__":
    if not os.environ.get("INFRAI_API_KEY"):
        raise SystemExit("Set INFRAI_API_KEY before running the demo")
    main()
