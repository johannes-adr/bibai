from common.document import Document
from typing import List

class Document2TextPort:
    def document2text(self, document: Document) -> str:
        raise NotImplementedError
    
    def is_capable_of(self, document: Document) -> bool:
        raise NotImplementedError



class Document2TextMultiplexer(Document2TextPort):
    doc2text: List[Document2TextPort]
    def __init__(self):
        self.doc2text = []

    def document2text(self, document: Document) -> str:
        for doc2text in self.doc2text:
            if doc2text.is_capable_of(document):
                return doc2text.document2text(document)
        raise NotImplementedError(f"No Document2TextPort capable of handling {document}")
    
    def is_capable_of(self, document: Document) -> bool:
        for doc2text in self.doc2text:
            if doc2text.is_capable_of(document):
                return True
        return False

    # Register a Document2TextPort
    def register_adapter(self, doc2text: Document2TextPort):
        self.doc2text.append(doc2text)