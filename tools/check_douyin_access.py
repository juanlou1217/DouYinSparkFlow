import argparse
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def load_cookies(cookie_file: str | None, cookie_json: str | None) -> list[dict]:
    if cookie_json:
        return json.loads(cookie_json)

    if cookie_file:
        return json.loads(Path(cookie_file).read_text(encoding="utf-8"))

    raise SystemExit("Provide --cookie-file or --cookie-json")


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check whether current Douyin cookies can access web, likes, and favorites pages."
    )
    parser.add_argument("--cookie-file", help="Path to exported cookies JSON file")
    parser.add_argument("--cookie-json", help="Raw cookies JSON string")
    parser.add_argument(
        "--out-dir",
        default="artifacts/douyin-check",
        help="Output directory for screenshots, html, and captured URLs",
    )
    args = parser.parse_args()

    cookies = load_cookies(args.cookie_file, args.cookie_json)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls_to_check = [
        ("home", "https://www.douyin.com/"),
        ("user_self", "https://www.douyin.com/user/self"),
        ("liked", "https://www.douyin.com/user/self?showTab=post_like"),
        ("favorite", "https://www.douyin.com/user/self?showTab=favorite_collection"),
    ]

    captured_urls: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()

        def handle_response(response) -> None:
            url = response.url
            if "douyin.com" in url:
                captured_urls.append(url)

        page.on("response", handle_response)

        results: list[dict] = []

        for name, url in urls_to_check:
            try:
                response = page.goto(url, wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(5000)
                title = page.title()
                html = page.content()
                screenshot_path = out_dir / f"{name}.png"
                html_path = out_dir / f"{name}.html"
                page.screenshot(path=str(screenshot_path), full_page=True)
                save_text(html_path, html)
                results.append(
                    {
                        "name": name,
                        "url": url,
                        "status": response.status if response else None,
                        "title": title,
                        "screenshot": str(screenshot_path),
                        "html": str(html_path),
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "name": name,
                        "url": url,
                        "error": str(exc),
                    }
                )

        save_text(out_dir / "results.json", json.dumps(results, ensure_ascii=False, indent=2))
        save_text(
            out_dir / "captured_urls.txt",
            "\n".join(sorted(dict.fromkeys(captured_urls))),
        )

        context.close()
        browser.close()

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Captured URLs written to {out_dir / 'captured_urls.txt'}")


if __name__ == "__main__":
    main()
