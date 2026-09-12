import pytest

from src.service import create_alert
from src.tasks import _scan_file_for_threats

TEN_MB_PLUS_ONE = 10 * 1024 * 1024 + 1


async def upload_file(
    client,
    *,
    filename: str,
    content: bytes,
    content_type: str = "application/octet-stream",
    title: str = "test file",
):
    return await client.post(
        "/files",
        data={"title": title},
        files={"file": (filename, content, content_type)},
    )


async def upload_and_scan(client, **kwargs):
    response = await upload_file(client, **kwargs)
    assert response.status_code == 201, response.text
    file_id = response.json()["id"]
    await _scan_file_for_threats(file_id)
    scanned = await client.get(f"/files/{file_id}")
    assert scanned.status_code == 200, scanned.text
    return scanned.json()


async def test_empty_file_is_rejected(client):
    response = await upload_file(client, filename="empty.txt", content=b"")

    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty"


@pytest.mark.parametrize("filename", ["a.exe", "a.bat", "a.cmd", "a.sh", "a.js"])
async def test_dangerous_extension_is_suspicious(client, filename: str):
    payload = await upload_and_scan(
        client,
        filename=filename,
        content=b"not empty",
        content_type="application/octet-stream",
    )
    extension = filename[filename.rfind(".") :]

    assert payload["scan_status"] == "suspicious"
    assert payload["requires_attention"] is True
    assert f"suspicious extension {extension}" in payload["scan_details"]


async def test_file_larger_than_10mb_is_suspicious(client):
    payload = await upload_and_scan(
        client,
        filename="big.bin",
        content=b"x" * TEN_MB_PLUS_ONE,
        content_type="application/octet-stream",
    )

    assert payload["scan_status"] == "suspicious"
    assert payload["requires_attention"] is True
    assert "file is larger than 10 MB" in payload["scan_details"]


async def test_pdf_with_wrong_mime_is_suspicious(client):
    payload = await upload_and_scan(
        client,
        filename="x.pdf",
        content=b"%PDF-1.4 fake",
        content_type="text/plain",
    )

    assert payload["scan_status"] == "suspicious"
    assert payload["requires_attention"] is True
    assert "pdf extension does not match mime type" in payload["scan_details"]


@pytest.mark.parametrize("content_type", ["application/pdf", "application/octet-stream"])
async def test_pdf_with_allowed_mime_is_clean(client, content_type: str):
    payload = await upload_and_scan(
        client,
        filename="x.pdf",
        content=b"%PDF-1.4 fake",
        content_type=content_type,
    )

    assert payload["scan_status"] == "clean"
    assert payload["requires_attention"] is False
    assert payload["scan_details"] == "no threats found"


async def test_small_txt_is_clean(client):
    payload = await upload_and_scan(
        client,
        filename="notes.txt",
        content=b"hello",
        content_type="text/plain",
    )

    assert payload["scan_status"] == "clean"
    assert payload["requires_attention"] is False
    assert payload["scan_details"] == "no threats found"


async def test_rename_updates_title(client):
    created = await upload_file(client, filename="notes.txt", content=b"hello", title="old title")
    assert created.status_code == 201, created.text
    file_id = created.json()["id"]

    updated = await client.patch(f"/files/{file_id}", json={"title": "new title"})

    assert updated.status_code == 200
    body = updated.json()
    assert body["title"] == "new title"
    assert body["id"] == file_id


@pytest.mark.xfail(strict=True, reason="FK without cascade")
async def test_delete_file_with_alerts(client):
    created = await upload_file(client, filename="notes.txt", content=b"hello")
    assert created.status_code == 201, created.text
    file_id = created.json()["id"]
    await create_alert(file_id, "warning", "needs attention")

    response = await client.delete(f"/files/{file_id}")

    assert response.status_code == 204
    missing = await client.get(f"/files/{file_id}")
    assert missing.status_code == 404
