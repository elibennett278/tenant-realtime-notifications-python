from src.notification_service import TenantAccount, onboard_tenant


class FakeClient:
    def __init__(self):
        self.calls = []

    def create_channel(self, channel):
        self.calls.append(("channel", channel))
        return {"ok": True}

    def issue_token(self, client_id, channel):
        self.calls.append(("token", client_id, channel))
        return {"ok": True, "data": {"token": "test"}}

    def publish(self, channel, event, data, account_id):
        self.calls.append(("publish", channel, event, data, account_id))
        return {"ok": True}


def test_suspended_account_gets_token_without_broadcast():
    fake = FakeClient()
    result = onboard_tenant(TenantAccount("north", "acct-9", "client-1", active=False), fake)
    assert result["published"] is False
    assert [call[0] for call in fake.calls] == ["channel", "token"]
