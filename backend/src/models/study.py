from dataclasses import dataclass, asdict
@dataclass
class Study:
    name: str
    dataset_id: str
    min_support: float
    min_confidence: float
    permutations: int
    seed: int
    def to_record(self):
        return asdict(self)
