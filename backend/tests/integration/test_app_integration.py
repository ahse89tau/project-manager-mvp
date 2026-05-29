import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_root_serves_static_html_and_page_can_call_api_contract() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        page = await client.get("/")
        hello = await client.get("/api/hello")

    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert "Hello from the PM MVP Scaffold" in page.text
    assert "/api/hello" in page.text

    assert hello.status_code == 200
    assert hello.json() == {"message": "Hello from FastAPI"}
