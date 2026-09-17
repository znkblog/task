import csv
import sys
import time
from itertools import islice
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from crawl_news import clean_text


INPUT_FILE = "crawl_news_output.csv"
OUTPUT_FILE = "crawl_news_article_output.csv"
BATCH_SIZE = 20
REQUEST_INTERVAL_SECONDS = 1


def fetch_article(
    session: requests.Session, news_link: str
) -> tuple[str, str]:
    response = session.get(news_link, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    article_view = soup.select_one("div#articleView")
    if article_view is None:
        raise ValueError("기사 영역(div#articleView)을 찾을 수 없습니다.")

    title_element = article_view.select_one("h1.articleSubecjt")
    if title_element is None:
        title_element = article_view.select_one("h1.articleSubject")
    body_element = article_view.select_one("div#realArtcContents")
    if title_element is None:
        raise ValueError("기사 제목(h1.articleSubject)을 찾을 수 없습니다.")
    if body_element is None:
        raise ValueError("기사 본문(div#realArtcContents)을 찾을 수 없습니다.")

    for element in body_element.select("img, script"):
        element.decompose()

    return (
        clean_text(title_element.get_text()),
        clean_text(body_element.get_text()),
    )


def append_article(
    writer: csv.DictWriter, source_row: dict[str, str], news_title: str, news_body: str
) -> None:
    writer.writerow(
        {
            "news_date": source_row.get("news_date", ""),
            "news_title": news_title,
            "news_link": source_row.get("news_link", ""),
            "news_body": news_body,
        }
    )


def main() -> int:
    input_path = Path(INPUT_FILE)
    if not input_path.is_file():
        print(
            f"[오류] 입력 파일을 찾을 수 없습니다: {INPUT_FILE}\n"
            "crawl_news.py를 먼저 실행해 원본 CSV를 생성해 주세요.",
            file=sys.stderr,
        )
        return 1

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

    with (
        input_path.open("r", newline="", encoding="utf-8-sig") as input_file,
        open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as output_file,
    ):
        reader = csv.DictReader(input_file)
        writer = csv.DictWriter(
            output_file,
            fieldnames=["news_date", "news_title", "news_link", "news_body"],
        )
        writer.writeheader()

        processed_count = 0
        while batch := list(islice(reader, BATCH_SIZE)):
            for source_row in batch:
                news_link = source_row.get("news_link", "").strip()
                if not news_link:
                    print("뉴스 링크가 없어 해당 항목을 건너뜁니다.")
                    continue

                try:
                    news_title, news_body = fetch_article(session, news_link)
                except (requests.RequestException, ValueError) as error:
                    print(f"수집 실패: {news_link} ({error})")
                    news_title = ""
                    news_body = ""

                append_article(writer, source_row, news_title, news_body)
                output_file.flush()
                processed_count += 1
                print(f"기사 {processed_count}건 처리 완료: {news_link}")
                time.sleep(REQUEST_INTERVAL_SECONDS)

    print(f"전체 기사 수집 완료: {processed_count}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
