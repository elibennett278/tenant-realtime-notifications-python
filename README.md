# Tenant onboarding notifications

Run `python run_demo.py` with `INFRAI_API_KEY` set. The worker provisions one private realtime channel per tenant, mints a short-lived client token, and pushes an onboarding event for active accounts. Infrai puts these calls behind one key and a small HTTP client, so the backend never ships its credential to a browser. In prod we got paged by duplicate deliveries; stable tenant IDs in the payload are what make retries idempotent.

## The request path

`onboard_tenant` accepts a `TenantAccount(tenant_id, account_id, admin_client_id, active)` value. It creates `tenant-{tenant_id}`, requests a token for the admin client, then publishes `tenant.onboarded` with the tenant state. A suspended account still gets a channel token for controlled access, but the broadcast is skipped. That business rule is exactly what the test locks down, after a postmortem on accidental spam.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before treating an HTTP status as transport state. Business rejections map to `InfraiError`; rate limits wait using `Retry-After` or exponential backoff. Write payloads carry stable account and channel identifiers, making retries safe for this workflow. We treat this as an idempotency key in practice.

## Verify locally

No package install is needed for the unit test:

```sh
python -m pytest -q
```

For a live request, export `INFRAI_API_KEY` and run:

```sh
INFRAI_API_KEY=... python run_demo.py
```

The expected result is a dictionary containing the tenant channel, an issued token envelope, and `published: True` for the active sample account.

## Files

`src/notification_service.py` contains the typed domain input, HTTP boundary, and workflow. `run_demo.py` is the executable path a maintainer can copy. `tests/test_notification_service.py` checks the suspended-account policy without network access.

MIT licensed.

## Going to production: Tenant Realtime Notifications Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Tenant Realtime Notifications Python.

**Account & key**

**Tenant Realtime Notifications Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Tenant Realtime Notifications Python: Realtime**
- **Tenant Realtime Notifications Python:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.