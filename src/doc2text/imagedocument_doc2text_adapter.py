import logging
from doc2text.doc2text_port import Document2TextPort
from common.document import Document, ImageDocument
from typing import Dict, Any, Optional, Tuple, List
import json
import cv2
import numpy as np
import paddle
from paddleocr import PaddleOCR # type: ignore

logger = logging.getLogger(__name__)

def parse_immich_ocr_cache():

    result: Dict[str, Any] = {}
    with open("./ocrresult.txt", 'r') as file:
        for line in file:
            [id, cache] = line.split(" ", 1)
            cache = json.loads(cache)
            text = ""
            for item in cache:
                text += item["text"] + " "
            result[id] = text
    
    return result
cache = parse_immich_ocr_cache()

# Module‐level cache of the OCR instance
_ocr: Optional[PaddleOCR] = None

def _get_ocr(lang: str) -> PaddleOCR:
    """
    Lazily instantiate and return the PaddleOCR engine.
    """
    global _ocr
    if _ocr is None:
        gpu_available = paddle.device.is_compiled_with_cuda()
        logging.getLogger("ppocr").setLevel(logging.INFO)
        logging.getLogger("paddleocr").setLevel(logging.INFO)
        _ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            use_gpu=gpu_available
        )
    return _ocr

class ImageDocument2TextAdapter(Document2TextPort):
    def __init__(self, lang: str):
        """
        Initialize the ImageDocument2TextAdapter with the specified language.
        """
        super().__init__()
        self.lang = lang

    def document2text(self, document: Document) -> str:
        """
        Convert the given image to text using OCR.

        If the document is not an ImageDocument, raise a ValueError.
        """
        if not isinstance(document, ImageDocument):
            raise ValueError("Document is not an ImageDocument")
        
        if document.id in cache:
            logger.debug(f"Cache hit for document {document.id}")
            return cache[document.id].lower()
        

        [binary, _] = document.load_image()

        image_array = np.frombuffer(binary, np.uint8)
        image: Optional[np.ndarray[Any, Any]] = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if image is None:  # type: ignore[comparison-overlap]
            raise ValueError("Failed to decode image from binary data")

        ocr_engine = _get_ocr(self.lang)

        # Run OCR on the image
        result: Optional[List[List[Tuple[Any, Tuple[str, float]]]]] = ocr_engine.ocr(image, cls=True)  # type: ignore

        if result is None: # type: ignore 
            raise ValueError("OCR failed to process the image")
    
        # Extract text from the OCR result
        joined_text: List[str] = []
        for box, (text, confidence) in result[0]: # type: ignore # 
            joined_text.append(text)

            
        text = " ".join(joined_text).lower()
        return text
    
    def is_capable_of(self, document: Document) -> bool:
        return isinstance(document, ImageDocument)