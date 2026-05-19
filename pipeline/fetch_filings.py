import requests
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "JPM", "V"]
SEC_BASE_URL = "https://data.sec.gov/submissions"
SEC_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"
RATE_LIMIT_DELAY = 0.11  # 11 requests per second to be safe
DATA_DIR = Path(__file__).parent.parent / "data" / "raw"


def lookup_cik(ticker: str) -> str:
    """Lookup CIK from ticker symbol."""
    try:
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={ticker}&type=10-K&dateb=&owner=include&count=1&search_text="
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Parse CIK from the response (simple extraction)
        if "CIK" in response.text:
            start = response.text.find("CIK=") + 4
            end = response.text.find("&", start)
            cik = response.text[start:end].strip()
            return cik
    except Exception as e:
        logger.error(f"Error looking up CIK for {ticker}: {e}")

    return None


def get_company_filings(cik: str, ticker: str) -> list:
    """Fetch filing metadata from SEC for a company."""
    try:
        # Format CIK with leading zeros
        cik_padded = str(cik).zfill(10)
        url = f"{SEC_BASE_URL}/CIK{cik_padded}.json"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        filings = []
        three_years_ago = datetime.now() - timedelta(days=3*365)

        # Extract filings from the response
        if "filings" in data and "recent" in data["filings"]:
            recent = data["filings"]["recent"]
            for i, form_type in enumerate(recent.get("form", [])):
                if form_type not in ["10-K", "10-Q"]:
                    continue

                filing_date_str = recent["filingDate"][i]
                filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")

                if filing_date < three_years_ago:
                    continue

                accession = recent["accessionNumber"][i].replace("-", "")
                company_name = data.get("entityName", ticker)

                filings.append({
                    "ticker": ticker,
                    "company_name": company_name,
                    "filing_type": form_type,
                    "filing_date": filing_date_str,
                    "accession": accession,
                    "cik": cik_padded,
                })

        return filings

    except Exception as e:
        logger.error(f"Error fetching filings for {ticker}: {e}")
        return []


def download_filing(filing: dict) -> bool:
    """Download a single filing HTML."""
    try:
        ticker = filing["ticker"]
        filing_type = filing["filing_type"]
        filing_date = filing["filing_date"]
        cik = filing["cik"]
        accession = filing["accession"]

        # Construct the filing URL
        url = f"{SEC_ARCHIVES_URL}/{cik}/{accession}/{accession[0:10]}-{accession[10:12]}-{accession[12:]}.htm"

        # Try alternate paths
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            # Try without the formatted accession
            url = f"{SEC_ARCHIVES_URL}/{cik}/{accession}/0{accession}.txt"
            response = requests.get(url, timeout=10)

        response.raise_for_status()

        # Save the filing
        ticker_dir = DATA_DIR / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{filing_type}_{filing_date.replace('-', '')}.html"
        filepath = ticker_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(response.text)

        logger.info(f"Downloaded {ticker} {filing_type} ({filing_date}) to {filepath}")
        return True

    except Exception as e:
        logger.error(f"Error downloading filing {filing['ticker']} {filing['filing_type']} {filing['filing_date']}: {e}")
        return False


def main():
    """Main pipeline: fetch all filings."""
    total_downloaded = 0

    for ticker in TICKERS:
        logger.info(f"Processing {ticker}...")

        # Lookup CIK
        cik = lookup_cik(ticker)
        if not cik:
            logger.warning(f"Could not find CIK for {ticker}")
            continue

        time.sleep(RATE_LIMIT_DELAY)

        # Get filings metadata
        filings = get_company_filings(cik, ticker)
        logger.info(f"Found {len(filings)} filings for {ticker}")

        # Download each filing
        for filing in filings:
            if download_filing(filing):
                total_downloaded += 1
            time.sleep(RATE_LIMIT_DELAY)

    logger.info(f"\n✅ Pipeline complete. Downloaded {total_downloaded} filings total.")


if __name__ == "__main__":
    main()
