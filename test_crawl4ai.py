import asyncio, os, re
from crawl4ai import AsyncWebCrawler, BrowserConfig

URLS = [
    "https://example.com",
    "https://github.com/browser-use/browser-use",
    "https://news.ycombinator.com",
]
OUT = r"E:\knowledge_database\open-metaphysics\webtools-test-output"
os.makedirs(OUT, exist_ok=True)

def safe(s):
    return (s or "").encode("ascii", "replace").decode("ascii")

async def main():
    browser_config = BrowserConfig(chrome_channel="chrome", headless=True, verbose=False)
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for i, url in enumerate(URLS):
            print(f"\n===== {url} =====", flush=True)
            try:
                result = await crawler.arun(url=url)
                md = getattr(result, "markdown", "") or ""
                ok = getattr(result, "success", True)
                meta = getattr(result, "metadata", {}) or {}
                t = meta.get("title") if isinstance(meta, dict) else None
                print(f"success={ok}", flush=True)
                print(f"markdown_len={len(md)}", flush=True)
                print(f"title={safe(t)}", flush=True)
                fname = re.sub(r'[^a-z0-9]+','_', url.lower()).strip('_')[:60]
                fpath = os.path.join(OUT, f"{i+1}_{fname}.md")
                with open(fpath, "w", encoding="utf-8") as fh:
                    fh.write(md)
                print(f"saved={fpath}", flush=True)
                print(f"preview={safe(md[:300])}", flush=True)
            except Exception as e:
                print(f"error={type(e).__name__}: {safe(str(e))}", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
