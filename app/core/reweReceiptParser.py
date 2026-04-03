import pdfplumber
import re

# Constants
from core.config import START_KEYWORD, STOP_KEYWORDS
ITEM_REGEX = re.compile(r'(.+?)\s+(\d+[,.]\d{2})[\sAB*]*$')

def extract_text_from_pdf(uploaded_file) -> str:
    """Extracts raw text from the PDF file object."""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text(layout=True) + "\n"
    return text

def parse_receipt(text: str) -> list:
    """Parses raw receipt text and returns a list of dictionaries (Items & Prices)."""
    items = []
    start_reading = False

    for line in text.split('\n'):
        clean_line = line.replace('"', '').strip()

        if clean_line == START_KEYWORD:
            start_reading = True
            continue

        if any(keyword in clean_line for keyword in STOP_KEYWORDS):
            start_reading = False
            break

        if start_reading:
            match = ITEM_REGEX.search(clean_line)
            if match:
                item_name = match.group(1).strip()
                item_name = re.sub(r'^[,;\s]+', '', item_name)
                price_str = match.group(2).replace(',', '.')

                if 'Stk x' in item_name:
                    continue

                if item_name:
                    items.append({"Item": item_name, "Price": float(price_str)})
    return items