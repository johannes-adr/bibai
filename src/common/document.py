from typing import List, Optional, Tuple
from dataclasses import dataclass, field

@dataclass
class Document:
    id: str
    tags: Optional[List[str]]
    _text: Optional[str] = field(default=None, repr=False)
   
    @property
    def text(self) -> Optional[str]:
        return self._text

    @text.setter
    def text(self, value: Optional[str]) -> None:
        self._text = value

@dataclass(kw_only=True)
class ImageDocument(Document):
    # binary and mime_type are loaded from the source
    def load_image(self) -> Tuple[bytes, str]:
        raise NotImplementedError