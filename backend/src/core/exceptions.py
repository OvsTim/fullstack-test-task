class DomainError(Exception):
    status_code: int = 400
    detail: str = "Error"


class FileNotFound(DomainError):
    status_code = 404
    detail = "File not found"


class EmptyFile(DomainError):
    status_code = 400
    detail = "File is empty"


class StoredFileMissing(DomainError):
    status_code = 404
    detail = "Stored file not found"
