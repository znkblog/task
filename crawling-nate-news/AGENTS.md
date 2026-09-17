# 네이트 뉴스 크롤러

## 프로젝트 현황

이 프로젝트는 네이트 뉴스 크롤링을 2단계로 나누어 처리하는 구조로
개발 중입니다.

1. 검색어와 검색 기간으로 네이트 뉴스 검색
2. 검색 결과에서 말줄임 처리된 제목, 뉴스 링크, 표시 날짜 수집
3. 수집 결과를 CSV 파일로 저장

첫 번째 단계인 검색 결과 목록 크롤러와 두 번째 단계인 각 뉴스 링크 접속
후 완전한 제목과 본문 수집 크롤러가 구현되어 있습니다.

## 개발 환경 및 의존성

- Python: `>=3.12`
- 패키지 관리 및 실행 도구: `uv`
- HTML 파서: `beautifulsoup4`
- HTTP 클라이언트: `requests`
- CSV 저장: Python 표준 라이브러리 `csv`

의존성 동기화:

```powershell
uv sync
```

## 첫 번째 단계 크롤러

실행 파일은 `crawl_news.py`입니다.

검색 조건은 파일 상단의 상수로 설정합니다.

```python
QUERY = "경제"
START_DATE = "20260801"
END_DATE = "20260831"
```

다른 검색어 또는 검색 기간을 사용하려면 실행 전에 해당 상수 값을 변경합니다.
날짜는 `YYYYMMDD` 형식을 사용해야 합니다.

실행 방법:

```powershell
uv run python crawl_news.py
```

크롤러는 다음 형식의 검색 URL을 생성합니다.

```text
https://news.nate.com/search?q={query}&f3=2&ps=3&ps1={start_date}&ps2={end_date}&o=T&page={page}
```

검색 페이지 1부터 100까지 순서대로 접속하며, 페이지의
`ul.search-list li` 요소가 없으면 더 이상 수집하지 않고 종료합니다.
페이지 요청 사이에는 1초의 대기 시간을 둡니다.

각 검색 결과에서 다음 정보를 수집합니다.

- `news_date`: `span.time` 요소의 텍스트
- `news_title`: `h2.tit` 요소의 텍스트
- `news_link`: `a` 요소의 `href` 속성

`news_title`은 줄바꿈, 탭, 연속 공백 등 모든 공백 문자를 하나의 일반
공백으로 바꾸고 앞뒤 공백을 제거합니다.

`news_date`는 줄바꿈, 탭, 연속 공백 등 모든 공백 문자를 `|` 하나로
바꿉니다. 예를 들어 다음과 같이 저장됩니다.

```text
티브이데일리|2026.08.01|00:12
```

`//`로 시작하는 프로토콜 상대 URL은 앞에 `https:`를 붙여
`https://...` 형식으로 변환합니다.

## 결과 파일

수집 결과는 다음 파일에 저장됩니다.

```text
crawl_news_output.csv
```

CSV 컬럼 순서는 다음과 같습니다.

```text
news_date,news_title,news_link
```

CSV는 UTF-8 BOM(`utf-8-sig`) 인코딩으로 저장하므로 Excel에서 직접 열 수
있습니다. 크롤러를 새로 실행하면 기존 결과 파일을 비우고 새 결과를
수집합니다.

생성된 결과 파일, 가상환경, Python 바이트코드 및 캐시 파일은
`.gitignore`에 등록되어 있습니다.

## 두 번째 단계 기사 크롤러

실행 파일은 `crawl_news_article.py`입니다.

첫 번째 단계에서 생성한 `crawl_news_output.csv`를 입력으로 사용합니다.
입력 파일이 없으면 오류를 발생시키고 종료합니다. CSV 전체를 메모리에
올리지 않도록 20개 단위의 배치로 읽고, 배치 안의 기사를 하나씩 처리합니다.
입력 파일이 없을 때는 traceback 대신 원인과 조치 방법을 한글 안내로
출력하고 종료 코드 `1`을 반환합니다.

실행 방법:

```powershell
uv run python crawl_news_article.py
```

각 `news_link`에 접속해 다음 요소를 수집합니다.

- `news_title`: 먼저 `div#articleView h1.articleSubecjt`의 텍스트를 찾고,
  없으면 `div#articleView h1.articleSubject`의 텍스트를 사용
- `news_body`: `div#articleView div#realArtcContents`의 텍스트

본문을 수집할 때 `img`와 `script` 요소는 제거합니다. 제목과 본문은
줄바꿈, 탭, 연속 공백 등 모든 공백 문자를 하나의 일반 공백으로 바꾸고
앞뒤 공백을 제거합니다.

결과는 `crawl_news_article_output.csv`에 기사 하나를 처리할 때마다
즉시 저장합니다. 결과 컬럼 순서는 다음과 같습니다.

```text
news_date,news_title,news_link,news_body
```

`news_date`와 `news_link`는 원본 CSV 값을 사용하고, `news_title`과
`news_body`는 기사 페이지에서 새로 수집한 값을 사용합니다. 기사 처리
상태는 콘솔에 표시되며, 요청 사이에는 1초의 대기 시간을 둡니다.
개별 기사 수집에 실패해도 오류를 출력하고 해당 행을 빈 제목·본문으로
저장한 후 다음 기사 처리를 계속합니다. 출력 파일은 UTF-8 BOM
(`utf-8-sig`)으로 저장되어 Excel에서 직접 열 수 있습니다.
