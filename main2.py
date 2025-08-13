print("🔥 Python process booting (pre-import)...", flush=True)

import time
import aiohttp
import asyncio
import tempfile
import shutil
import json
from typing import Optional, Tuple, Dict, List
from functools import partial
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---------- Config ----------
load_dotenv()
WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook-test/ytjobs"
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
    service = Service(ChromeDriverManager().install())
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
# Detail page (blocking)
# ---------------------------

# def extract_detail_from_job_page(url: str) -> Dict:
#     d, prof = launch_driver()
#     try:
#         if not safe_get(d, url):
#             return {
#                 "youtube_links": [],
#                 "youtube_channel_link": "N/A",
#                 "posted_date": "N/A",
#                 "experience": "N/A",
#                 "job_description": "N/A",
#                 "content_format": "N/A",
#                 "skills": [],
#                 "categories": []
#             }
        
#         # Wait for main content to load
#         WebDriverWait(d, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.sc-YnwpJ.cZctmD")))
#         time.sleep(2)
#         soup = BeautifulSoup(d.page_source, "html.parser")
        
#         # Extract job details from script tag
#         job_data = {}
#         script_tag = soup.find('script', string=re.compile(r'var ___yt_cf_pcache'))
#         if script_tag:
#             match = re.search(r'var ___yt_cf_pcache\s*=\s*(\[.*?\]);', script_tag.string, re.DOTALL)
#             if match:
#                 try:
#                     data = json.loads(match.group(1))
#                     if data and isinstance(data, list) and data[0].get('cval'):
#                         job_data = data[0]['cval']
#                 except json.JSONDecodeError:
#                     print("⚠️ Failed to parse job data JSON")

#         # Extract YouTube links from sample videos
#         youtube_links = []
#         if job_data.get('youtubeVideos'):
#             for video in job_data['youtubeVideos']:
#                 youtube_links.append(f"https://youtube.com/watch?v={video['id']}")
        
#         # Extract channel link
#         youtube_channel_link = "N/A"
#         if job_data.get('company', {}).get('ytLink'):
#             youtube_channel_link = job_data['company']['ytLink']
            
#         # Extract posted date
#         posted_date = job_data.get('createdAt', 'N/A')
        
#         # Extract job description
#         job_description = job_data.get('htmlContent', 'N/A')
        
#         # Extract skills
#         skills = [skill['name'] for skill in job_data.get('skills', [])]
        
#         # Extract categories
#         categories = [category['name'] for category in job_data.get('categories', [])]
        
#         # Extract content format (video type)
#         content_format = job_data.get('videoType', 'N/A')
#         if content_format == "short":
#             content_format = "Short-form"
        
#         return {
#             "youtube_links": youtube_links,
#             "youtube_channel_link": youtube_channel_link,
#             "posted_date": posted_date,
#             "experience": "N/A",  # Not available in the data
#             "job_description": job_description,
#             "content_format": content_format,
#             "skills": skills,
#             "categories": categories
#         }
#     except Exception as e:
#         print(f"⚠️ Error extracting job details: {e}")
#         return {
#             "youtube_links": [],
#             "youtube_channel_link": "N/A",
#             "posted_date": "N/A",
#             "experience": "N/A",
#             "job_description": "N/A",
#             "content_format": "N/A",
#             "skills": [],
#             "categories": []
#         }
#     finally:
#         cleanup_driver(d, prof)

def extract_detail_from_job_page(url: str) -> Dict:
    d, prof = launch_driver()
    try:
        if not safe_get(d, url):
            return {k: "N/A" for k in [
                "channel_url", "youtube_channel_link", "youtube_links",
                "posted_date", "experience", "content_format", "job_description"
            ]}

        WebDriverWait(d, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )
        time.sleep(1)
        soup = BeautifulSoup(d.page_source, "html.parser")
        print(soup.prettify())

        # 1️⃣ Channel link on job page
        channel_anchor = soup.select_one('a[href^="/youtube-channel/"]')
        channel_url = f"https://ytjobs.co{channel_anchor['href']}" \
            if channel_anchor and channel_anchor.has_attr("href") else "N/A"

        # 2️⃣ YouTube channel link
        youtube_channel_link = "N/A"
        if channel_url != "N/A" and safe_get(d, channel_url):
            WebDriverWait(d, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            time.sleep(0.8)
            ch_soup = BeautifulSoup(d.page_source, "html.parser")
            yt_link_tag = (
                ch_soup.select_one("section.channel-page-header a[href*='youtube.com']")
                or ch_soup.find("a", href=lambda x: x and "youtube.com" in x)
            )
            if yt_link_tag and yt_link_tag.has_attr("href"):
                youtube_channel_link = yt_link_tag["href"]

        # 3️⃣ YouTube video links
        youtube_links: List[str] = []
        for img in soup.select("div.yt-video-img-container img, img[src*='/vi/']"):
            src = img.get("src", "")
            if "/vi/" in src:
                video_id = src.split("/vi/")[1].split("/")[0]
                youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")
        youtube_links = list(set(youtube_links))  # Remove duplicates

        # 4️⃣ Posted date
        posted_div = (
            soup.find("div", class_="Couww") or
            soup.find(string=re.compile(r"Posted on", re.I))
        )
        posted_date = (
            posted_div.get_text(strip=True) if hasattr(posted_div, "get_text")
            else (posted_div.strip() if posted_div else "N/A")
        )

        # 5️⃣ Experience
        experience_text = "N/A"
        exp_elem = soup.find(string=re.compile(r"Minimum years of experience", re.I))
        if exp_elem:
            # Try previous heading, else take the parent text
            prev_h = (
                getattr(exp_elem, "find_previous", lambda *_: None)(["h6", "h5", "strong"])
                or exp_elem.parent
            )
            if prev_h:
                experience_text = prev_h.get_text(strip=True)

        # 6️⃣ Content Format
        form_text = "N/A"
        form_elem = soup.find(string=re.compile(r"Content Format", re.I))
        if form_elem:
            prev_h = (
                getattr(form_elem, "find_previous", lambda *_: None)(["h6", "h5", "strong"])
                or form_elem.parent
            )
            if prev_h:
                form_text = prev_h.get_text(strip=True)

        # 7️⃣ Job description
        details_div = (
            soup.find("div", class_="jQzvkT") or
            soup.find("div", attrs={"data-testid": "job-description"}) or
            soup.find("section", class_=re.compile(r"description", re.I))
        )
        job_details = (
            re.sub(r"\s+", " ", details_div.get_text(separator="\n", strip=True))
            if details_div else "N/A"
        )

        return {
            "channel_url": channel_url,
            "youtube_channel_link": youtube_channel_link,
            "youtube_links": youtube_links,
            "posted_date": posted_date,
            "experience": experience_text,
            "content_format": form_text,
            "job_description": job_details,
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
    except Exception as e:
        print(f"⚠️ Error loading job list: {e}")
        return None
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
        await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    print("🚀 Scraper starting...", flush=True)
    asyncio.run(main_loop())