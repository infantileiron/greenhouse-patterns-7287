from dataclasses import dataclass, asdict
@dataclass
class Report:
    review_id: str
    name: str
    path: str
    def to_record(self):
        return asdict(self)
