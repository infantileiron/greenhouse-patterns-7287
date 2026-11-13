from dataclasses import dataclass, asdict
@dataclass
class Run:
    study_id: str
    status: str
    result: dict | None = None
    error: str | None = None
    claim_token: str | None = None
    claimed_at: str | None = None
    recovered_at: str | None = None
    attempts: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    def to_record(self):
        return asdict(self)
