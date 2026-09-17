import csv
import re
import time
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


QUERY = "경제"
START_DATE = "20260801"
END_DATE = "20260831"
OUTPUT_FILE = "crawl_news_output.csv"
MAX_PAGE = 100
REQUEST_INTERVAL_SECONDS = 1


def clean_text(text: str) -> str:
    """Replace line breaks with spaces and remove surrounding whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def clean_news_date(text: str) -> str:
    """Separate the media name and date with a single pipe character."""
    return re.sub(r"\s+", "|", text.strip())


def normalize_news_link(link: str) -> str:
    if link.startswith("//"):
        return f"https:{link}"
    return link


def build_search_url(page: int) -> str:
    params = {
        "q": QUERY,
        "f3": "2",
        "ps": "3",
        "ps1": START_DATE,
        "ps2": END_DATE,
        "o": "T",
        "page": page,
    }
    return f"https://news.nate.com/search?{urlencode(params)}"


def fetch_news_page(session: requests.Session, page: int) -> list[dict[str, str]]:
    response = session.get(build_search_url(page), timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    news_items = soup.select("ul.search-list li")
    page_news = []

    for el in news_items:
        link_element = el.select_one("a[href]")
        title_element = el.select_one("h2.tit")
        date_element = el.select_one("span.time")

        if not link_element or not title_element or not date_element:
            print(f"페이지 {page}: 필수 요소가 없어 해당 항목을 건너뜁니다.")
            continue

        page_news.append(
            {
                "news_link": normalize_news_link(link_element["href"]),
                "news_title": clean_text(title_element.get_text()),
                "news_date": clean_news_date(date_element.get_text()),
            }
        )

    return page_news


def append_to_csv(news_items: list[dict[str, str]], write_header: bool) -> None:
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=["news_date", "news_title", "news_link"],
        )
        if write_header:
            writer.writeheader()
        writer.writerows(news_items)


def main() -> None:
    # Start a fresh result file for each execution.
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig"):
        pass

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            )
        }
    )

    header_written = False
    for page in range(1, MAX_PAGE + 1):
        page_news = fetch_news_page(session, page)

        if not page_news:
            print(f"페이지 {page}: 수집할 뉴스가 없어 종료합니다.")
            break

        append_to_csv(page_news, write_header=not header_written)
        header_written = True
        print(f"페이지 {page}/{MAX_PAGE} 수집 완료: {len(page_news)}건")

        if page < MAX_PAGE:
            time.sleep(REQUEST_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
