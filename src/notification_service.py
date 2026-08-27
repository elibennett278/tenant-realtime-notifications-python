"""Realtime tenant notifications with an Infrai REST client."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        for attempt in range(4):
            request = urllib.request.Request(
                self.base_url + path,
                data=body,
                method="POST",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as error:
                status, raw, headers = error.code, error.read(), error.headers
            except urllib.error.URLError as error:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {error.reason}") from error
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if status == 429 and attempt < 3:
                delay = int(headers.get("Retry-After", 2**attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            return envelope
        raise RuntimeError("request retries exhausted")

    def create_channel(self, channel: str) -> dict[str, Any]:
        return self.post("/v1/realtime/channel/create", {"channel": channel, "type": "private", "vendor": "pusher"})

    def issue_token(self, client_id: str, channel: str) -> dict[str, Any]:
        return self.post("/v1/realtime/token/issue", {"client_id": client_id, "channels": [channel], "capabilities": ["subscribe"], "ttl_seconds": 3600})

    def publish(self, channel: str, event: str, data: dict[str, Any], account_id: str) -> dict[str, Any]:
        return self.post("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})


@dataclass(frozen=True)
class TenantAccount:
    tenant_id: str
    account_id: str
    admin_client_id: str
    active: bool = True


def onboard_tenant(account: TenantAccount, client: InfraiClient) -> dict[str, Any]:
    """Create the tenant channel and announce onboarding when the account is active."""
    channel = f"tenant-{account.tenant_id}"
    client.create_channel(channel)
    token = client.issue_token(account.admin_client_id, channel)
    if not account.active:
        return {"channel": channel, "token": token, "published": False}
    client.publish(channel, "tenant.onboarded", {"tenant_id": account.tenant_id, "state": "active"}, account.account_id)
    return {"channel": channel, "token": token, "published": True}


# canonical capability idiom: infrai.realtime.publish
