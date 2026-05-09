import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ShoplazzaImage:
    src: str


@dataclass
class ShoplazzaOption:
    name: str
    values: List[str]


@dataclass
class ShoplazzaVariant:
    price: float
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    compare_at_price: Optional[float] = None
    image: Optional[ShoplazzaImage] = None
    position: int = 1


@dataclass
class ShoplazzaProduct:
    title: str
    handle: str
    description: str = ""
    id: Optional[str] = None
    options: List[ShoplazzaOption] = field(default_factory=list)
    images: List[ShoplazzaImage] = field(default_factory=list)
    variants: List[ShoplazzaVariant] = field(default_factory=list)
    has_only_default_variant: bool = False
    requires_shipping: bool = True


@dataclass
class ShoplazzaProductPayload:
    product: ShoplazzaProduct

    def to_dict(self):
        def clean_dict(d):
            if isinstance(d, dict):
                return {k: clean_dict(v) for k, v in d.items() if v is not None}
            elif isinstance(d, list):
                return [clean_dict(v) for v in d]
            else:
                return d

        raw = json.loads(
            json.dumps(
                self, default=lambda o: o.__dict__ if hasattr(o, "__dict__") else o
            )
        )
        return clean_dict(raw)
