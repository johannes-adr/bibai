from typing import Any, Dict, List, Tuple, TypedDict, Sequence
from docdatabase.docdatabase_port import DocumentDatabasePort
from common.document import ImageDocument, Document

from dataclasses import dataclass

from concurrent.futures import ThreadPoolExecutor, as_completed
from docdatabase.immich_asset_description_extractor import extract_ocr_section, extract_tag_section, update_ocr_section

import requests
import logging

logger = logging.getLogger(__name__)

class TimeBucket(TypedDict):
    timeBucket: str
    count: int

class ImmichApiSession:
    def __init__(self, api_host: str | None, api_key: str | None):
        if not api_host or not api_key:
            raise ValueError("IMMICH_API_HOST and IMMICH_API_KEY must be set in environment")
        self.api_host = api_host.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key})
        logger.debug("Initialized ImmichAPI client with host %s", self.api_host)


@dataclass(kw_only=True)
class ImmichImageDocument(ImageDocument):
    immich_api_session: ImmichApiSession 
    original_description: str

    def load_image(self) -> Tuple[bytes, str]:
        size = "preview" # preview or thumbnail
        url = f"{self.immich_api_session.api_host}/assets/{self.id}/thumbnail?size={size}"
        res = self.immich_api_session.session.get(url)
        res.raise_for_status()

        mime_type = res.headers.get("Content-Type", "")
        if not mime_type.startswith("image/"):
            raise ValueError(f"Unexpected MIME type: {mime_type}")

        return res.content, mime_type
    
    @Document.text.setter
    def text(self, value: str | None) -> None:
        self._text = value

        new_description = update_ocr_section(self.original_description, value if value else "")
        if new_description == self.original_description:
            return
        
        self.original_description = new_description
       
        url = f"{self.immich_api_session.api_host}/assets/{self.id}"
        res = self.immich_api_session.session.put(url, json={"description": self.original_description})
        res.raise_for_status()



class ImmichAPIDatabasePort(DocumentDatabasePort):
    def __init__(self, immich_api_session: ImmichApiSession) -> None:
        self.immich_api_session = immich_api_session
        pass
     
    def get_time_buckets(self) -> List[TimeBucket]:
        url = f"{self.immich_api_session.api_host}/timeline/buckets"
        params = {"size": "MONTH"}
        logger.debug("Requesting time buckets from %s with params %s", url, params)
        resp = self.immich_api_session.session.get(url, params=params)
        resp.raise_for_status()
        buckets = resp.json()
        logger.debug("Retrieved %d time buckets", len(buckets))
        return buckets
    
    
    def get_documents_by_time_bucket(self, time_bucket: str) -> List[ImmichImageDocument]:
        url = f"{self.immich_api_session.api_host}/timeline/bucket"
        params = {"timeBucket": time_bucket, "size": "MONTH"}
        logger.debug("Fetching assets for bucket %s from %s", time_bucket, url)
        resp = self.immich_api_session.session.get(url, params=params)
        resp.raise_for_status()
        assets: List[Dict[str, Any]] = resp.json()

        image_docs: List[ImmichImageDocument] = []

        for asset in assets:
            mime = asset['originalMimeType']
            if not mime.startswith("image/"):
                logger.debug("Skipping asset %s with unsupported mime type %s", asset['id'], mime)
                continue

            desc = asset.get('exifInfo', {}).get('description', '')
            image_doc = ImmichImageDocument(
                id=asset['id'],
                tags=extract_tag_section(desc),
                original_description=desc,
                immich_api_session=self.immich_api_session,
                _text=extract_ocr_section(desc)
            )

            image_docs.append(image_doc)
        logger.debug("Fetched %d assets for bucket %s", len(assets), time_bucket)
        return image_docs
    

    def list_documents(self, max_workers: int = 5) -> Sequence[ImmichImageDocument]:
        """
        Fetch all documents in parallel by time bucket.

        :param max_workers: Number of threads to use for parallel fetching
        """
        documents: List[ImmichImageDocument] = []
        buckets = self.get_time_buckets()
        total_buckets = len(buckets)
        logger.info("Starting to fetch documents for %d buckets with %d workers", total_buckets, max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_bucket = {
                executor.submit(self.get_documents_by_time_bucket, bucket["timeBucket"]): bucket
                for bucket in buckets
            }
            for idx, future in enumerate(as_completed(future_to_bucket), start=1):
                bucket = future_to_bucket[future]
                try:
                    assets = future.result()
                    documents.extend(assets)
                    logger.debug("(%d/%d) Completed bucket %s with %d assets", idx, total_buckets, bucket['timeBucket'], len(assets))
                except Exception as exc:
                    logger.error("Error fetching bucket %s: %s", bucket['timeBucket'], exc)
        logger.info("Finished fetching documents. Total assets retrieved: %d", len(documents))
        return documents
    

# docs = ImmichAPIDatabasePort().list_documents()
# for doc in docs[:10]:
#     print(doc)