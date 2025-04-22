from common.document import Document
from typing import Sequence

class DocumentDatabasePort:
    def list_documents(self) -> Sequence[Document]:
        raise NotImplementedError