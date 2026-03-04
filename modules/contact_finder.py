"""
ALIAS_X · Contact Finder
Web scraping + fallback archive for university registrar contacts.
"""

import re
import urllib3
import requests
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

# Internal fallback archive
ARCHIVE = {
    "University of Madras":   {"phone": "044-2539 9422", "email": "registrar@unom.ac.in"},
    "Anna University":     {"phone": "044-2235 2161", "email": "registrar@annauniv.edu"},
    "IIT Madras":      {"phone": "044-2257 8000", "email": "registrar@iitm.ac.in"},
    "VIT University":      {"phone": "0416-220 2020", "email": "registrar@vit.ac.in"},
    "SRM Institute of Science and Technology":      {"phone": "044-2745 5510", "email": "registrar@srmist.edu.in"},
    "Birla Institute of Technology and Science":     {"phone": "01596-242192", "email": "registrar@bits-pilani.ac.in"},
    "University of Mumbai":   {"phone": "022-2652 6091", "email": "registrar@mu.ac.in"},
    "University of Delhi":    {"phone": "011-2766 7011", "email": "registrar@du.ac.in"},
    "University of Bangalore":{"phone": "080-2296 1000", "email": "registrar@iisc.ac.in"},
}


def find_university_contact(university_name: str) -> dict:
    print(f"[CONTACT] Scanning: {university_name}...")

    result = {"phone": None, "email": None, "source": "Searching..."}

    if not university_name or university_name in ("Unknown", "Manual Check", ""):
        return result

    target_urls = _get_search_urls(university_name)

    for url in target_urls:
        if result["phone"] and result["email"]:
            break
        _scrape_url(url, result)

    # Fallback to archive
    if not result["phone"]:
        print("[CONTACT] Checking internal archive...")
        for key, info in ARCHIVE.items():
            if key in university_name.lower():
                result.update(info)
                result["source"] = "Internal Archive"
                break

    print(f"[CONTACT] Result: {result}")
    return result


def _get_search_urls(university_name: str) -> list:
    """Try Google search; fall back to DuckDuckGo HTML scrape."""
    urls = []
    query = f"{university_name} registrar contact number official"

    # Try googlesearch-python
    try:
        from googlesearch import search
        for r in search(query, num_results=3, advanced=True):
            urls.append(r.url)
            print(f"    > Google URL: {r.url}")
        if urls:
            return urls
    except Exception as e:
        print(f"    > Google search failed: {e}")

    # Fallback: DuckDuckGo HTML
    try:
        ddg_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        r = requests.get(ddg_url, headers=HEADERS, timeout=10, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("a.result__url")[:3]:
            href = a.get("href", "")
            if href.startswith("http"):
                urls.append(href)
                print(f"    > DDG URL: {href}")
    except Exception as e:
        print(f"    > DDG search failed: {e}")

    return urls


def _scrape_url(url: str, result: dict):
    try:
        print(f"    > Crawling: {url}")
        r = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if r.status_code != 200:
            return

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.extract()
        text = soup.get_text(separator=" ")

        # Phone extraction
        if not result["phone"]:
            keywords = ["Phone", "Ph:", "Tel:", "Contact:", "Registrar:", "Office:"]
            for line in text.split("\n"):
                if any(k in line for k in keywords):
                    matches = re.findall(r"(?:\+91|0\d{2,5})[-.\s]*\d{5,10}", line)
                    for m in matches:
                        if len(re.sub(r"[^\d]", "", m)) >= 10:
                            result["phone"] = m.strip()
                            result["source"] = f"Scraped from {url}"
                            print(f"      [+] Phone: {m}")
                            break
                if result["phone"]:
                    break

            if not result["phone"]:
                for m in re.findall(r"(?:\+91|0\d{2,4})[-.\s]+\d{3,5}[-.\s]+\d{3,5}", text):
                    result["phone"] = m.strip()
                    result["source"] = f"Scraped from {url}"
                    break

        # Email extraction
        if not result["email"]:
            for e in re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
                if any(d in e for d in ["registrar", "exam", "controller", "ac.in", "edu"]):
                    result["email"] = e
                    print(f"      [+] Email: {e}")
                    break

    except Exception as e:
        print(f"    > Skipped {url}: {e}")
