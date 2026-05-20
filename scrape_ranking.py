import csv
import json
import time
from pathlib import Path

import httpx


def fetch_page(client: httpx.Client, page: int) -> list[dict]:
    url = (
        "https://www.shanghairanking.cn/api/pub/v1/bcur"
        f"?bcur_type=11&year=2026&page={page}&size=30"
    )
    resp = client.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {}).get("rankings", [])


def main():
    output = Path("shanghairanking_universities_2026.csv")
    all_rows: list[dict] = []

    transport = httpx.HTTPTransport(retries=3)
    with httpx.Client(
        timeout=httpx.Timeout(30.0, connect=15.0, read=30.0),
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.shanghairanking.cn/rankings/bcur/202611",
        },
        follow_redirects=True,
        transport=transport,
    ) as client:
        for page in range(1, 21):
            print(f"Fetching page {page}/20 ...")
            for attempt in range(3):
                try:
                    rankings = fetch_page(client, page)
                    break
                except Exception as e:
                    print(f"  Error on page {page} attempt {attempt + 1}: {e}")
                    rankings = []
                    time.sleep(2)
            if not rankings:
                print(f"  No data on page {page}, stopping.")
                break
            for item in rankings:
                all_rows.append(
                    {
                        "排名": item.get("ranking", ""),
                        "学校中文名": item.get("univNameCn", ""),
                        "学校英文名": item.get("univNameEn", ""),
                        "省份": item.get("province", ""),
                        "类型": item.get("univCategory", ""),
                        "总分": item.get("score", ""),
                        "标签": "/".join(item.get("univTags", [])),
                    }
                )
            time.sleep(1)

    if not all_rows:
        print("No data fetched.")
        return

    with output.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "排名",
                "学校中文名",
                "学校英文名",
                "省份",
                "类型",
                "总分",
                "标签",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Done! {len(all_rows)} universities saved to {output.resolve()}")


if __name__ == "__main__":
    main()
