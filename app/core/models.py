from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class ReceiptItem:
    name: str
    price: float
    # These default to empty lists/dicts if not explicitly provided
    selected_people: List[str] = field(default_factory=list)
    custom_split: Dict[str, float] = field(default_factory=dict)