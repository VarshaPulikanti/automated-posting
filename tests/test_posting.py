import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.platforms.base import Platform, PlatformError, PostOutcome
from app.services import posting_service

client = TestClient(app)
GOOD = "Check out our platform and grow your visibility. https://example.com"


class OkPlatform(Platform):
    name = "Ok"
    def is_configured(self): return True
    async def post(self, message, client): return PostOutcome("https://ok.example/1")


class FailPlatform(Platform):
    name = "Fail"
    def is_configured(self): return True
    async def post(self, message, client): raise PlatformError("Authentication failed")


class CrashPlatform(Platform):
    name = "Crash"
    def is_configured(self): return True
    async def post(self, message, client): raise RuntimeError("boom")


class UnconfiguredPlatform(Platform):
    name = "NoCreds"
    def is_configured(self): return False
    async def post(self, message, client): raise AssertionError("must not be called")


class TimeoutPlatform(Platform):
    name = "Slow"
    def is_configured(self): return True
    async def post(self, message, client): raise httpx.ReadTimeout("slow")


# ---------- validation ----------
@pytest.mark.parametrize("message", [
    "",                                                     # empty
    "   ",                                                  # whitespace
    "No link here at all",                                  # zero links
    "Two links https://a.com and https://b.org",            # two links
    "Bad link https://not_a_domain",                        # invalid URL
    "x" * 201 + " https://example.com",                     # too long
])
def test_invalid_messages_rejected(message):
    r = client.post("/posting", json={"message": message})
    assert r.status_code == 422


def test_missing_message_rejected():
    assert client.post("/posting", json={}).status_code == 422


def test_exactly_200_chars_allowed(monkeypatch):
    monkeypatch.setattr(posting_service, "get_platforms", lambda: [OkPlatform()])
    url = " https://example.com"
    r = client.post("/posting", json={"message": "a" * (200 - len(url)) + url})
    assert r.status_code == 200


def test_trailing_punctuation_not_part_of_url(monkeypatch):
    monkeypatch.setattr(posting_service, "get_platforms", lambda: [OkPlatform()])
    assert client.post("/posting", json={"message": "Visit https://example.com."}).status_code == 200


# ---------- posting behaviour ----------
def test_one_failure_does_not_stop_others(monkeypatch):
    monkeypatch.setattr(posting_service, "get_platforms", lambda: [
        FailPlatform(), OkPlatform(), CrashPlatform(), UnconfiguredPlatform(), TimeoutPlatform()])
    body = client.post("/posting", json={"message": GOOD}).json()
    by_name = {r["platform"]: r for r in body["results"]}

    assert body["success"] is True
    assert by_name["Ok"]["status"] == "success"
    assert by_name["Ok"]["posted_url"] == "https://ok.example/1"
    assert by_name["Ok"]["public_access"] is True
    assert by_name["Ok"]["date"] and by_name["Ok"]["time"]
    assert by_name["Fail"]["error"] == "Authentication failed"
    assert by_name["Crash"]["status"] == "failed"
    assert "Credentials" in by_name["NoCreds"]["error"]
    assert by_name["Slow"]["error"] == "Request timed out"
    assert by_name["Fail"]["posted_url"] is None and by_name["Fail"]["public_access"] is False


def test_all_fail_reports_success_false(monkeypatch):
    monkeypatch.setattr(posting_service, "get_platforms", lambda: [FailPlatform()])
    body = client.post("/posting", json={"message": GOOD}).json()
    assert body["success"] is False
