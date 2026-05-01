import enum


class AnalysisSourceType(str, enum.Enum):
    photo = "photo"
    pdf = "pdf"


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    done = "done"
    failed = "failed"
