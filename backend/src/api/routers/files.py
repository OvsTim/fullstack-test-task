from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from src.api.deps import get_file_service
from src.schemas.files import FileItem, FileUpdate
from src.services.file_service import FileService
from src.workers.tasks import scan_file_for_threats

router = APIRouter()


def _content_disposition(filename: str) -> str:
    quoted = quote(filename)
    if quoted != filename:
        return f"attachment; filename*=utf-8''{quoted}"
    return f'attachment; filename="{filename}"'


@router.get("/files", response_model=list[FileItem])
async def list_files_view(files: FileService = Depends(get_file_service)):
    return await files.list()


@router.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
    files: FileService = Depends(get_file_service),
):
    content = await file.read()
    file_item = await files.upload(
        title=title,
        filename=file.filename,
        content_type=file.content_type,
        content=content,
    )
    scan_file_for_threats.delay(file_item.id)
    return file_item


@router.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(file_id: str, files: FileService = Depends(get_file_service)):
    return await files.get(file_id)


@router.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
    files: FileService = Depends(get_file_service),
):
    return await files.update(file_id=file_id, title=payload.title)


@router.get("/files/{file_id}/download")
async def download_file(file_id: str, files: FileService = Depends(get_file_service)):
    downloaded = await files.download(file_id)
    return StreamingResponse(
        downloaded.iter_chunks(),
        media_type=downloaded.mime_type,
        headers={"Content-Disposition": _content_disposition(downloaded.filename)},
    )


@router.delete("/files/{file_id}", status_code=204)
async def delete_file_view(file_id: str, files: FileService = Depends(get_file_service)):
    await files.delete(file_id)
