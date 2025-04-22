from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from tqdm import tqdm
from docdatabase.docdatabase_port import DocumentDatabasePort
from doc2text.doc2text_port import Document2TextPort

logger = logging.getLogger(__name__)

class Bibai:
    doc_database_port: DocumentDatabasePort
    document2text_port: Document2TextPort
    
    def __init__(self,doc_database_port: DocumentDatabasePort, document2text_port: Document2TextPort):
        self.doc_database_port = doc_database_port
        self.document2text_port = document2text_port

    def update(self):
        documents = self.doc_database_port.list_documents()

        # executor to parallelize document2text calls
        with ThreadPoolExecutor(32) as executor:
            # submit all tasks, keep track of which future belongs to which doc
            futures = {
                executor.submit(self.document2text_port.document2text, doc): doc
                for doc in documents
            }

            # as each future completes, tqdm will advance
            for future in tqdm(as_completed(futures),
                               total=len(futures),
                               desc="Converting docs",
                               unit="doc"):
                doc = futures[future]
                try:
                    doc.text = future.result()
                except Exception as e:
                    doc.text = f"<error: {e}>"
                
                logger.debug(f"{doc.id} -> '{doc.text}'\n")

