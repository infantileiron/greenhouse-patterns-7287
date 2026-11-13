from dataclasses import dataclass, asdict
@dataclass
class Dataset:
    name: str
    filename: str
    rows: list[dict]
    def to_record(self):
        return asdict(self)
