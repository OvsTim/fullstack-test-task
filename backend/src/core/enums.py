from enum import Enum


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class ScanStatus(str, Enum):
    CLEAN = "clean"
    SUSPICIOUS = "suspicious"
    FAILED = "failed"


class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
