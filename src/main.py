import os

from dotenv import load_dotenv
load_dotenv()

from common.common import setup_logging
setup_logging()

from bibai_controller import Bibai
from docdatabase.immich.immich_docdatabase_adapter import ImmichAPIDatabasePort, ImmichApiSession
from doc2text.doc2text_port import Document2TextMultiplexer
from doc2text.imagedocument_doc2text_adapter import ImageDocument2TextAdapter



def main():
    API_HOST = os.getenv("IMMICH_API_HOST")
    API_KEY = os.getenv("IMMICH_API_KEY")
    OCR_LANG = os.getenv("OCR_LANG", "en")

    database_port = ImmichAPIDatabasePort(ImmichApiSession(API_HOST, API_KEY))
    
    document2text_port = Document2TextMultiplexer()
    document2text_port.register_adapter(ImageDocument2TextAdapter(OCR_LANG))

    controller = Bibai(database_port, document2text_port)
    controller.update()


main()