from dataclasses import dataclass, asdict
@dataclass
class Run:
    study_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    def to_record(self):
        return asdict(self)
