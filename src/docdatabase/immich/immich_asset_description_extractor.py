import re
from typing import Optional, List


def extract_ocr_section(description: str) -> Optional[str]:
    """
    Extracts and returns the text between %OCR_BEG% and %OCR_END% markers.

    Args:
        description (str): The string containing the OCR section markers.

    Returns:
        Optional[str]: The extracted OCR text, stripped of whitespace, or None if markers not found.
    """
    match = re.search(r'%OCR_BEG%(.*?)%OCR_END%', description, re.S)
    return match.group(1).strip() if match else None


def extract_tag_section(description: str) -> Optional[List[str]]:
    """
    Extracts and returns a list of tags between %TAG_BEG% and %TAG_END% markers.

    Args:
        description (str): The string containing the tag section markers.

    Returns:
        Optional[List[str]]: A list of tag strings, stripped of whitespace, or None if markers not found.
    """
    match = re.search(r'%TAG_BEG%(.*?)%TAG_END%', description, re.S)
    if not match:
        return None
    raw = match.group(1).strip()
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(',')]


def update_ocr_section(description: str, new_ocr: Optional[str]) -> str:
    if new_ocr is None:
        new_ocr = ""

    if len(new_ocr) > 0:
        new_ocr = "\n" + new_ocr + "\n"
    """
    Replaces or inserts the OCR section in the description.

    Args:
        description (str): Original text potentially containing OCR markers.
        new_ocr (str): New OCR content to insert.

    Returns:
        str: The updated description with the new OCR content.
    """
    marker = f"%OCR_BEG%{new_ocr}%OCR_END%"
    if re.search(r'%OCR_BEG%.*?%OCR_END%', description, re.S):
        return re.sub(r'%OCR_BEG%.*?%OCR_END%', marker, description, flags=re.S)
    # No existing section: append at end
    return description.rstrip() + "\n\n" + marker


def update_tag_section(description: str, tags: List[str]) -> str:
    """
    Replaces or inserts the TAG section in the description.

    Args:
        description (str): Original text potentially containing TAG markers.
        tags (List[str]): New tags to insert.

    Returns:
        str: The updated description with the new TAG content.
    """
    tags_str = ', '.join(tags)
    marker = f"%TAG_BEG%{tags_str}%TAG_END%"
    if re.search(r'%TAG_BEG%.*?%TAG_END%', description, re.S):
        return re.sub(r'%TAG_BEG%.*?%TAG_END%', marker, description, flags=re.S)
    # No existing section: append at end
    return description.rstrip() + "\n" + marker


# Unit tests
if __name__ == "__main__":
    import unittest


    class TestSections(unittest.TestCase):
        def setUp(self):
            self.base_desc = (
                "Header text\n"
                "%OCR_BEG%"
                "old ocr\n"
                "%OCR_END%\n"
                "Body\n"
                "%TAG_BEG%\n"
                "A, B"
                "%TAG_END%\nHii"
            )

        def test_update_ocr_existing(self):
            updated = update_ocr_section(self.base_desc, "new ocr content")
            self.assertIn("%OCR_BEG%new ocr content%OCR_END%", updated)
            self.assertNotIn("old ocr", updated)

        def test_update_ocr_existing_empty_text(self):
            updated = update_ocr_section(self.base_desc, "")
            self.assertIn("%OCR_BEG%%OCR_END%", updated)
            self.assertNotIn("old ocr", updated)

        def test_update_ocr_insert(self):
            desc = "No OCR here"
            updated = update_ocr_section(desc, "inserted")
            self.assertTrue(updated.endswith("%OCR_BEG%inserted%OCR_END%"))

        # def test_update_tag_existing(self):
        #     updated = update_tag_section(self.base_desc, ["X", "Y", "Z"])
        #     self.assertIn("%TAG_BEG%\nX, Y, Z\n%TAG_END%", updated)
        #     self.assertNotIn("A, B", updated)

        # def test_update_tag_insert(self):
        #     desc = "No tags here"
        #     updated = update_tag_section(desc, ["T1"])
        #     self.assertTrue(updated.endswith("%TAG_BEG%\nT1\n%TAG_END%"))

    unittest.main()
