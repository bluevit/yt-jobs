print("🔥 Python process booting (pre-import)...", flush=True)

import time
import aiohttp
import asyncio
import tempfile
import shutil
from typing import Optional, Tuple, Dict, List
from functools import partial
import re
import json

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---------- Config ----------
load_dotenv()
WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook-test/ytjobs"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
LIST_URL = "https://ytjobs.co/job/search/all_categories"
# ----------------------------

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
    opts.add_argument("--no-zygote")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-features=IsolateOrigins,site-per-process,VizDisplayCompositor")
    opts.add_argument("--lang=en-US,en")
    opts.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    opts.page_load_strategy = "none"
    if profile_dir:
        opts.add_argument(f"--user-data-dir={profile_dir}")
    return opts

def launch_driver() -> Tuple[webdriver.Chrome, str]:
    tmpdir = tempfile.mkdtemp(prefix="chrome-profile-")
    options = build_chrome_options(tmpdir)
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    return driver, tmpdir

def cleanup_driver(driver: webdriver.Chrome, tmpdir: Optional[str]):
    try:
        driver.quit()
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)

def safe_get(driver: webdriver.Chrome, url: str, timeout: int = 60, retries: int = 3, sleep_between: int = 3) -> bool:
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

def text_or_na(tag) -> str:
    return tag.get_text(strip=True) if tag else "N/A"

# ---------------------------
# Detail page
# ---------------------------

def extract_detail_from_job_page(url: str) -> Dict:
    d, prof = launch_driver()
    try:
        if not safe_get(d, url):
            return {k: "N/A" for k in [
                "channel_anchor", "channel_url", "youtube_links",
                "youtube_channel_link", "posted_date", "experience",
                "job_description", "content_format"
            ]}
        WebDriverWait(d, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        time.sleep(1)
        soup = BeautifulSoup(d.page_source, "html.parser")

        # Channel link detection (both formats)
        channel_anchor = soup.select_one('a[href^="/youtube-channel/"], a[href*="youtube.com/@"]')
        channel_anchor_str = str(channel_anchor) if channel_anchor else "N/A"

        if channel_anchor and channel_anchor.has_attr("href"):
            href = channel_anchor["href"]
            if href.startswith("/youtube-channel/"):
                channel_url = f"https://ytjobs.co{href}"
            else:
                channel_url = href
        else:
            channel_url = "N/A"

        # Direct YouTube link if already found
        youtube_channel_link = "N/A"
        if channel_url != "N/A":
            if "youtube.com" in channel_url:
                youtube_channel_link = channel_url
            elif safe_get(d, channel_url):
                WebDriverWait(d, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
                time.sleep(0.8)
                ch_soup = BeautifulSoup(d.page_source, "html.parser")
                yt_link_tag = ch_soup.select_one("section.channel-page-header a[href*='youtube.com']")
                if yt_link_tag and yt_link_tag.has_attr("href"):
                    youtube_channel_link = yt_link_tag["href"]

        # Video thumbnails → YouTube URLs
        youtube_links: List[str] = []
        for img in soup.select("div.yt-video-img-container img.yt-video-img-el, img[src*='/vi/']"):
            src = img.get("src", "")
            if "/vi/" in src:
                try:
                    video_id = src.split("/vi/")[1].split("/")[0]
                    youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")
                except Exception:
                    pass

        # Posted date
        posted_div = soup.find(string=re.compile(r"Posted on", re.I))
        posted_date = posted_div.strip() if posted_div else "N/A"

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
            "channel_anchor": channel_anchor_str,
            "channel_url": channel_url,
            "youtube_links": youtube_links,
            "youtube_channel_link": youtube_channel_link,
            "posted_date": posted_date,
            "experience": experience_text,
            "job_description": job_details,
            "content_format": form_text,
        }
    finally:
        cleanup_driver(d, prof)

async def get_detail_async(url: str) -> Dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(extract_detail_from_job_page, url))

# ---------------------------
# List page
# ---------------------------

_COMP_RE = re.compile(r'(\$|€|£|₹|\d)\s?[\d,]+|/hour|/hr|per\s?(hour|month|week|year)|month|hour|year|yr|salary', re.I)
def is_comp(t: str) -> bool:
    return bool(_COMP_RE.search(t))

def is_location(t: str) -> bool:
    low = t.lower()
    return ("remote" in low or "hybrid" in low or "onsite" in low or "on-site" in low or ("," in t and len(t) <= 60))

_JOBTYPE_TOKENS = ("full time", "full-time", "part time", "part-time", "contract", "intern", "freelance")
def looks_like_jobtype(t: str) -> bool:
    low = t.lower()
    return any(tok in low for tok in _JOBTYPE_TOKENS)

async def scrape_first_job() -> Dict | None:
    d, prof = launch_driver()
    try:
        if not safe_get(d, LIST_URL):
            return None

        WebDriverWait(d, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-job-card")))
        time.sleep(0.8)
        soup = BeautifulSoup(d.page_source, "html.parser")
    finally:
        cleanup_driver(d, prof)

    root_div = soup.find("div", id="root")
    if not root_div:
        print("⚠️ No root div found.")
        return None

    first_card = root_div.select_one("div.search-job-card")
    if not first_card:
        print("⚠️ No job cards found.")
        return None

    job_link_tag = first_card.select_one('a[href^="/job/"]')
    apply_link = f"https://ytjobs.co{job_link_tag['href']}" if job_link_tag and job_link_tag.has_attr("href") else "N/A"

    title_el = job_link_tag.select_one("h1,h2,h3,h4") if job_link_tag else None
    title_text = (
        text_or_na(title_el) if title_el else
        (text_or_na(job_link_tag) if job_link_tag else text_or_na(first_card.find(["h1","h2","h3","h4"])))
    )
    if not title_text or title_text == "N/A":
        maybe_title = first_card.find(["h3", "h5"])
        title_text = text_or_na(maybe_title)

    h5_texts = [h.get_text(strip=True) for h in first_card.select("h5")]
    job_type = "N/A"; location = "N/A"; compensation = "N/A"

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

    company_img = first_card.select_one("img[alt]")
    company = company_img["alt"].strip() if company_img and company_img.has_attr("alt") else "N/A"
    thumbnail = company_img["src"] if company_img and company_img.has_attr("src") else "N/A"

    subs = "N/A"
    subs_text = first_card.find(string=re.compile(r"subscriber", re.I))
    if subs_text:
        subs = subs_text.strip()
    else:
        subs_el = first_card.find(lambda t: getattr(t, "get_text", None) and "subscriber" in t.get_text(strip=True).lower())
        if subs_el:
            subs = subs_el.get_text(strip=True)

    extra_details: Dict = {}
    if apply_link != "N/A":
        extra_details = await get_detail_async(apply_link)

    job = {
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
    return job

# ---------------------------
# Runner loop
# ---------------------------

async def main_loop():
    while True:
        print("🔄 Scraping first job...")
        job = await scrape_first_job()
        if not job:
            print("❌ No job found.")
        else:
            print("🧪 First job title:", job.get("title"))
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(WEBHOOK_URL, json=job) as resp:
                        print(f"📤 Sent FIRST job: {job.get('title','(no title)')} | Status: {resp.status}")
                except Exception as e:
                    print(f"❌ Failed to send to webhook: {e}")
        await asyncio.sleep(300)

if __name__ == "__main__":
    print("🚀 Scraper starting...", flush=True)
    asyncio.run(main_loop())
