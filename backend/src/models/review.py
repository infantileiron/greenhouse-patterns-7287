from dataclasses import dataclass, asdict
@dataclass
class Review:
    run_id: str
    rule_ids: list[str]
    note: str
    status: str
    def to_record(self):
        return asdict(self)
