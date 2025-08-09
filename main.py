print("🔥 Python process booting (pre-import)...", flush=True)

import os
import time
import aiohttp
import asyncio
import tempfile
import shutil
from functools import partial
from typing import Optional, Tuple, List, Dict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
WEBHOOK_URL = "https://automationsinc.app.n8n.cloud/webhook/ytjobs"

CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
LIST_URL = "https://ytjobs.co/job/search/all_categories"

# ---------------------------
# Chrome setup helpers
# ---------------------------

def build_chrome_options(profile_dir: Optional[str] = None) -> Options:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-sync")
    opts.add_argument("--metrics-recording-only")
    opts.add_argument("--disable-default-apps")
    opts.add_argument("--mute-audio")
    # Lighten load a bit more
    opts.add_argument("--no-zygote")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-features=IsolateOrigins,site-per-process,VizDisplayCompositor")
    if profile_dir:
        opts.add_argument(f"--user-data-dir={profile_dir}")  # unique per instance
    return opts

def launch_driver(profile_dir: Optional[str] = None) -> Tuple[webdriver.Chrome, Optional[str]]:
    """Create a Chrome driver with a unique profile; returns (driver, profile_dir_to_cleanup)."""
    created_dir = None
    if profile_dir is None:
        created_dir = tempfile.mkdtemp(prefix="chrome-profile-")
        profile_dir = created_dir
    options = build_chrome_options(profile_dir)
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    # shorter page load timeout to avoid long hangs
    driver.set_page_load_timeout(25)
    return driver, created_dir  # created_dir will be removed by caller

def safe_get(driver: webdriver.Chrome, url: str, timeout: int = 25, retries: int = 2, sleep_between: int = 2) -> bool:
    """driver.get with timeout & retries to avoid hanging the whole loop."""
    driver.set_page_load_timeout(timeout)
    for attempt in range(retries + 1):
        try:
            driver.get(url)
            return True
        except (TimeoutException, WebDriverException) as e:
            if attempt == retries:
                print(f"⏱️ GET failed for {url}: {e}")
                return False
            time.sleep(sleep_between)

# ---------------------------
# Detail page (blocking)
# ---------------------------

def extract_youtube_links_from_page(url: str) -> Dict:
    driver, tmpdir = launch_driver()
    try:
        if not safe_get(driver, url):
            return {
                "youtube_links": [],
                "youtube_channel_link": "N/A",
                "posted_date": "N/A",
                "experience": "N/A",
                "job_description": "N/A",
                "content_format": "N/A",
            }

        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Channel page link on job page (structure-based selector)
        channel_anchor = soup.select_one('a[href^="/youtube-channel/"]')
        channel_url = ("https://ytjobs.co" + channel_anchor["href"]) if channel_anchor and channel_anchor.has_attr("href") else "N/A"

        # Go to channel page and find YouTube channel link
        youtube_channel_link = "N/A"
        if channel_url != "N/A" and safe_get(driver, channel_url):
            time.sleep(1.5)
            channel_soup = BeautifulSoup(driver.page_source, "html.parser")
            yt_link_tag = channel_soup.select_one("section.channel-page-header a[href*='youtube.com']")
            if yt_link_tag and yt_link_tag.has_attr("href"):
                youtube_channel_link = yt_link_tag["href"]

        # Video thumbnails -> YouTube URLs
        youtube_links: List[str] = []
        for img in soup.select("div.yt-video-img-container img.yt-video-img-el, img[src*='/vi/']"):
            src = img.get("src", "")
            try:
                if "/vi/" in src:
                    video_id = src.split("/vi/")[1].split("/")[0]
                    youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")
            except Exception:
                pass

        # Posted date (fallback: look for text like "Posted on")
        posted_div = soup.find("div", class_="Couww") or soup.find(string=re.compile(r"Posted on", re.I))
        posted_date = posted_div.get_text(strip=True) if hasattr(posted_div, "get_text") else (posted_div.strip() if posted_div else "N/A")

        # Experience
        experience_text = "N/A"
        experience_p = soup.find("p", string=lambda t: "Minimum years of experience" in t if t else False)
        if experience_p:
            prev_h = experience_p.find_previous(["h6", "h5", "strong"])
            if prev_h:
                experience_text = prev_h.get_text(strip=True)

        # Content Format
        form_text = "N/A"
        form_p = soup.find("p", string=lambda t: "Content Format" in t if t else False)
        if form_p:
            prev_h = form_p.find_previous(["h6", "h5", "strong"])
            if prev_h:
                form_text = prev_h.get_text(strip=True)

        # Job description
        details_div = soup.find("div", class_="jQzvkT") or soup.find("div", attrs={"data-testid": "job-description"})
        job_details = re.sub(r"\s+", " ", details_div.get_text(separator="\n", strip=True)) if details_div else "N/A"

        return {
            "youtube_links": youtube_links,
            "youtube_channel_link": youtube_channel_link,
            "posted_date": posted_date,
            "experience": experience_text,
            "job_description": job_details,
            "content_format": form_text,
        }
    finally:
        try:
            driver.quit()
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)

async def get_extra_details_async(url: str) -> Dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(extract_youtube_links_from_page, url))

# ---------------------------
# List page (async)
# ---------------------------

def text_or_na(tag) -> str:
    return tag.get_text(strip=True) if tag else "N/A"

_COMP_RE = re.compile(r'(\$|€|£|₹|\d)\s?[\d,]+|/hour|/hr|per\s?(hour|month|week|year)|month|hour|year|yr|salary', re.I)
def is_comp(t: str) -> bool:
    return bool(_COMP_RE.search(t))

def is_location(t: str) -> bool:
    low = t.lower()
    return (
        "remote" in low or "hybrid" in low or "onsite" in low or "on-site" in low or
        ("," in t and len(t) <= 60)
    )

_JOBTYPE_TOKENS = ("full time", "full-time", "part time", "part-time", "contract", "intern", "freelance")
def looks_like_jobtype(t: str) -> bool:
    low = t.lower()
    return any(tok in low for tok in _JOBTYPE_TOKENS)

async def scrape_yt_jobs() -> List[Dict]:
    # unique profile for list page, single driver
    driver, tmpdir = launch_driver()
    try:
        if not safe_get(driver, LIST_URL):
            return []

        # wait until cards render
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.search-job-card"))
            )
        except Exception as e:
            print(f"⚠️ List page wait failed: {e}")

        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        try:
            driver.quit()
        finally:
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)

    root_div = soup.find("div", id="root")
    if not root_div:
        return []

    job_cards = root_div.select("div.search-job-card")
    sem = asyncio.Semaphore(2)  # limit detail fetch concurrency

    async def extract_job_data(card) -> Optional[Dict]:
        try:
            # Stable job link (anchor for both title + apply link)
            job_link_tag = card.select_one('a[href^="/job/"]')
            apply_link = f"https://ytjobs.co{job_link_tag['href']}" if job_link_tag and job_link_tag.has_attr("href") else "N/A"

            # Title priority: <a><h1..h4> → link text → any h1..h4 in card → h3/h5 fallback
            title_el = job_link_tag.select_one("h1,h2,h3,h4") if job_link_tag else None
            title_text = (
                text_or_na(title_el) if title_el else
                (text_or_na(job_link_tag) if job_link_tag else text_or_na(card.find(["h1","h2","h3","h4"])))
            )
            if not title_text or title_text == "N/A":
                maybe_title = card.find(["h3", "h5"])
                title_text = text_or_na(maybe_title)

            # Collect all h5 texts and classify
            h5_texts = [h.get_text(strip=True) for h in card.select("h5")]

            job_type = "N/A"
            location = "N/A"
            compensation = "N/A"

            for txt in h5_texts:
                if looks_like_jobtype(txt):
                    job_type = txt
                    break

            for txt in h5_texts:
                if txt == job_type:
                    continue
                if location == "N/A" and is_location(txt):
                    location = txt
                    continue
                if compensation == "N/A" and is_comp(txt):
                    compensation = txt

            # Company & thumbnail from any <img alt="Company">
            company_img = card.select_one("img[alt]")
            company = company_img["alt"].strip() if company_img and company_img.has_attr("alt") else "N/A"
            thumbnail = company_img["src"] if company_img and company_img.has_attr("src") else "N/A"

            # Subscribers / channel stats: find any text containing "subscriber"
            subs = "N/A"
            subs_text = card.find(string=re.compile(r"subscriber", re.I))
            if subs_text:
                subs = subs_text.strip()
            else:
                subs_el = card.find(lambda t: getattr(t, "get_text", None) and "subscriber" in t.get_text(strip=True).lower())
                if subs_el:
                    subs = subs_el.get_text(strip=True)

            extra_details: Dict = {}
            if apply_link != "N/A":
                async with sem:
                    extra_details = await get_extra_details_async(apply_link)

            return {
                "title": title_text,
                "job_type": job_type,
                "location": location,
                "compensation": compensation,
                "company": company,
                "subscribers": subs,
                "thumbnail": thumbnail,
                "apply_link": apply_link,
                **extra_details,
            }
        except Exception as e:
            print(f"❌ Error parsing job card: {e}")
            print("   ↳ card snippet:", card.get_text(" ", strip=True)[:200])
            return None

    jobs = await asyncio.gather(*(extract_job_data(card) for card in job_cards))
    return [j for j in jobs if j is not None]

# ---------------------------
# Runner loop
# ---------------------------

async def main_loop():
    while True:
        print("🔄 Scraping jobs...")
        jobs = await scrape_yt_jobs()
        if not jobs:
            print("❌ No jobs found.")
        else:
            print("🧪 First titles:", [j.get("title") for j in jobs[:1]])
            # sent = 0
            async with aiohttp.ClientSession() as session:
                for job in jobs[:1]:  # send first only; change to 'jobs' to send all
                    try:
                        async with session.post(WEBHOOK_URL, json=job) as resp:
                            print(f"📤 Sent job: {job.get('title','(no title)')} | Status: {resp.status}")
                            # sent += 1
                    except Exception as e:
                        print(f"❌ Failed to send to webhook: {e}")
            print(f"✅ Done. Sent 1 job.")
        await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    print("🚀 Scraper starting...", flush=True)
    asyncio.run(main_loop())
