import logging
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
SECTIONS_TO_EXTRACT = ["Item 1.", "Item 1A.", "Item 7.", "Item 8.", "Item 9A."]
SECTION_NAMES = {
    "Item 1.": "Business",
    "Item 1A.": "Risk Factors",
    "Item 7.": "MD&A",
    "Item 8.": "Financial Statements",
    "Item 9A.": "Controls",
}


def extract_fiscal_period(filing_type: str, filing_date: str) -> str:
    """Convert filing date to fiscal period."""
    date_obj = datetime.strptime(filing_date, "%Y-%m-%d")
    year = date_obj.year

    if filing_type == "10-K":
        return f"FY{year}"
    elif filing_type == "10-Q":
        quarter = (date_obj.month - 1) // 3 + 1
        return f"Q{quarter} {year}"
    return f"{date_obj.strftime('%Y-%m-%d')}"


def parse_filing(filepath: Path, ticker: str, company_name: str, filing_type: str, filing_date: str, edgar_url: str) -> list:
    """Parse a single filing HTML file and extract sections."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()

        # Clean up text: remove extra whitespace, boilerplate
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(Copyright|Page|Exhibit|Forward-looking|Item \d+\.)', '', text, flags=re.IGNORECASE)

        fiscal_period = extract_fiscal_period(filing_type, filing_date)
        sections = []

        # Extract sections based on headers
        for section_header in SECTIONS_TO_EXTRACT:
            section_name = SECTION_NAMES.get(section_header, section_header)

            # Find the section in text
            start_idx = text.find(section_header)
            if start_idx == -1:
                continue

            # Find the next section start
            end_idx = len(text)
            for other_header in SECTIONS_TO_EXTRACT:
                if other_header != section_header:
                    next_idx = text.find(other_header, start_idx + len(section_header))
                    if next_idx != -1 and next_idx < end_idx:
                        end_idx = next_idx

            section_text = text[start_idx:end_idx].strip()

            if len(section_text) > 100:  # Only keep substantial sections
                sections.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "filing_type": filing_type,
                    "filing_date": filing_date,
                    "fiscal_period": fiscal_period,
                    "section_name": section_name,
                    "section_text": section_text,
                    "edgar_url": edgar_url,
                })

        return sections

    except Exception as e:
        logger.error(f"Error parsing {filepath}: {e}")
        return []


def main():
    """Main pipeline: parse all downloaded filings."""
    all_sections = []
    parsed_count = 0

    for ticker_dir in DATA_DIR.iterdir():
        if not ticker_dir.is_dir():
            continue

        ticker = ticker_dir.name
        logger.info(f"Parsing filings for {ticker}...")

        for filing_file in ticker_dir.glob("*.html"):
            # Parse filename: 10-K_20240630.html
            parts = filing_file.stem.split("_")
            if len(parts) != 2:
                continue

            filing_type = parts[0]
            filing_date_str = parts[1]
            filing_date = f"{filing_date_str[0:4]}-{filing_date_str[4:6]}-{filing_date_str[6:8]}"

            edgar_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={ticker}&accession_number=&xbrl_type=v"

            sections = parse_filing(
                filing_file,
                ticker,
                ticker,  # Use ticker as company name placeholder
                filing_type,
                filing_date,
                edgar_url,
            )

            all_sections.extend(sections)
            parsed_count += 1

    logger.info(f"✅ Parsed {parsed_count} filings into {len(all_sections)} sections")

    return all_sections


if __name__ == "__main__":
    sections = main()
