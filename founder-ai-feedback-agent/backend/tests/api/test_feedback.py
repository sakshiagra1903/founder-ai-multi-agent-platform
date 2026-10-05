"""API tests for feedback upload endpoints."""
import io
import csv
import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> str:
    await client.post("/api/v1/auth/register", json={
        "email": "uploader@example.com",
        "password": "SecurePass1",
        "full_name": "Upload User",
        "company_name": "Upload Co",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "uploader@example.com",
        "password": "SecurePass1",
    })
    return resp.json()["access_token"]


def _make_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode()


@pytest.mark.asyncio
async def test_upload_csv(client: AsyncClient):
    token = await _register_and_login(client)
    csv_bytes = _make_csv([
        {"feedback_id": "1", "customer_id": "c1", "feedback_text": "Great product!", "rating": "5"},
        {"feedback_id": "2", "customer_id": "c2", "feedback_text": "Terrible experience.", "rating": "1"},
    ])
    resp = await client.post(
        "/api/v1/feedback/upload?auto_analyze=false",
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert data["imported"] == 2


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient):
    csv_bytes = _make_csv([{"feedback_text": "test"}])
    resp = await client.post(
        "/api/v1/feedback/upload",
        files={"file": ("test.csv", csv_bytes, "text/csv")},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_feedback(client: AsyncClient):
    token = await _register_and_login(client)
    resp = await client.get(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
