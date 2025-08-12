# # print("🔥 Python process booting (pre-import)...", flush=True)

# # import time
# # import aiohttp
# # import asyncio
# # import tempfile
# # import shutil
# # from typing import Optional, Tuple, Dict, List
# # from functools import partial
# # import re

# # from selenium import webdriver
# # from selenium.webdriver.chrome.service import Service
# # from selenium.webdriver.chrome.options import Options
# # from selenium.common.exceptions import TimeoutException, WebDriverException
# # from selenium.webdriver.common.by import By
# # from selenium.webdriver.support.ui import WebDriverWait
# # from selenium.webdriver.support import expected_conditions as EC

# # from bs4 import BeautifulSoup
# # from dotenv import load_dotenv

# # # ---------- Config ----------
# # load_dotenv()
# # WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook-test/ytjobs"
# # CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
# # LIST_URL = "https://ytjobs.co/job/search/all_categories"
# # # ----------------------------

# # def build_chrome_options(profile_dir: Optional[str] = None) -> Options:
# #     opts = Options()
# #     opts.add_argument("--headless=new")
# #     opts.add_argument("--disable-gpu")
# #     opts.add_argument("--no-sandbox")
# #     opts.add_argument("--disable-dev-shm-usage")
# #     opts.add_argument("--disable-background-networking")
# #     opts.add_argument("--disable-extensions")
# #     opts.add_argument("--disable-sync")
# #     opts.add_argument("--metrics-recording-only")
# #     opts.add_argument("--disable-default-apps")
# #     opts.add_argument("--mute-audio")
# #     opts.add_argument("--no-zygote")
# #     opts.add_argument("--blink-settings=imagesEnabled=false")
# #     opts.add_argument("--disable-features=IsolateOrigins,site-per-process,VizDisplayCompositor")
# #     opts.add_argument("--lang=en-US,en")
# #     opts.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
# #                       "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
# #     # Return immediately; we will wait for specific elements
# #     opts.page_load_strategy = "none"
# #     if profile_dir:
# #         opts.add_argument(f"--user-data-dir={profile_dir}")
# #     return opts

# # def launch_driver() -> Tuple[webdriver.Chrome, str]:
# #     tmpdir = tempfile.mkdtemp(prefix="chrome-profile-")
# #     options = build_chrome_options(tmpdir)
# #     service = Service(CHROMEDRIVER_PATH)
# #     driver = webdriver.Chrome(service=service, options=options)
# #     driver.set_page_load_timeout(60)
# #     return driver, tmpdir

# # def cleanup_driver(driver: webdriver.Chrome, tmpdir: Optional[str]):
# #     try:
# #         driver.quit()
# #     finally:
# #         if tmpdir:
# #             shutil.rmtree(tmpdir, ignore_errors=True)

# # def safe_get(driver: webdriver.Chrome, url: str, timeout: int = 60, retries: int = 3, sleep_between: int = 3) -> bool:
# #     driver.set_page_load_timeout(timeout)
# #     for attempt in range(retries + 1):
# #         try:
# #             driver.get(url)
# #             return True
# #         except (TimeoutException, WebDriverException) as e:
# #             if attempt == retries:
# #                 print(f"⏱️ GET failed for {url}: {e}")
# #                 return False
# #             time.sleep(sleep_between)

# # def text_or_na(tag) -> str:
# #     return tag.get_text(strip=True) if tag else "N/A"

# # # ---------------------------
# # # Detail page (blocking)
# # # ---------------------------

# # def extract_detail_from_job_page(url: str) -> Dict:
# #     d, prof = launch_driver()
# #     try:
# #         if not safe_get(d, url):
# #             return {
# #                 "youtube_links": [],
# #                 "youtube_channel_link": "N/A",
# #                 "posted_date": "N/A",
# #                 "experience": "N/A",
# #                 "job_description": "N/A",
# #                 "content_format": "N/A",
# #             }
# #         WebDriverWait(d, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
# #         time.sleep(1)
# #         soup = BeautifulSoup(d.page_source, "html.parser")

# #         # Channel link on job page
# #         channel_anchor = soup.select_one('a[href^="/youtube-channel/"]')
# #         channel_url = f"https://ytjobs.co{channel_anchor['href']}" if channel_anchor and channel_anchor.has_attr("href") else "N/A"

# #         # YouTube channel link (if available)
# #         youtube_channel_link = "N/A"
# #         if channel_url != "N/A" and safe_get(d, channel_url):
# #             WebDriverWait(d, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
# #             time.sleep(0.8)
# #             ch_soup = BeautifulSoup(d.page_source, "html.parser")
# #             yt_link_tag = ch_soup.select_one("section.channel-page-header a[href*='youtube.com']")
# #             if yt_link_tag and yt_link_tag.has_attr("href"):
# #                 youtube_channel_link = yt_link_tag["href"]

# #         # Video thumbnails → YouTube URLs
# #         youtube_links: List[str] = []
# #         for img in soup.select("div.yt-video-img-container img.yt-video-img-el, img[src*='/vi/']"):
# #             src = img.get("src", "")
# #             if "/vi/" in src:
# #                 try:
# #                     video_id = src.split("/vi/")[1].split("/")[0]
# #                     youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")
# #                 except Exception:
# #                     pass

# #         # Posted date
# #         posted_div = soup.find("div", class_="Couww") or soup.find(string=re.compile(r"Posted on", re.I))
# #         posted_date = posted_div.get_text(strip=True) if hasattr(posted_div, "get_text") else (posted_div.strip() if posted_div else "N/A")

# #         # Experience
# #         experience_text = "N/A"
# #         experience_p = soup.find("p", string=lambda t: "Minimum years of experience" in t if t else False)
# #         if experience_p:
# #             prev_h = experience_p.find_previous(["h6", "h5", "strong"])
# #             if prev_h:
# #                 experience_text = prev_h.get_text(strip=True)

# #         # Content Format
# #         form_text = "N/A"
# #         form_p = soup.find("p", string=lambda t: "Content Format" in t if t else False)
# #         if form_p:
# #             prev_h = form_p.find_previous(["h6", "h5", "strong"])
# #             if prev_h:
# #                 form_text = prev_h.get_text(strip=True)

# #         # Job description
# #         details_div = soup.find("div", class_="jQzvkT") or soup.find("div", attrs={"data-testid": "job-description"})
# #         job_details = re.sub(r"\s+", " ", details_div.get_text(separator="\n", strip=True)) if details_div else "N/A"

# #         return {
# #             "channel_url": channel_url,
# #             "youtube_links": youtube_links,
# #             "youtube_channel_link": youtube_channel_link,
# #             "posted_date": posted_date,
# #             "experience": experience_text,
# #             "job_description": job_details,
# #             "content_format": form_text,
# #         }
# #     finally:
# #         cleanup_driver(d, prof)


# # async def get_detail_async(url: str) -> Dict:
# #     loop = asyncio.get_event_loop()
# #     return await loop.run_in_executor(None, partial(extract_detail_from_job_page, url))

# # # ---------------------------
# # # List page (only first card)
# # # ---------------------------

# # _COMP_RE = re.compile(r'(\$|€|£|₹|\d)\s?[\d,]+|/hour|/hr|per\s?(hour|month|week|year)|month|hour|year|yr|salary', re.I)
# # def is_comp(t: str) -> bool:
# #     return bool(_COMP_RE.search(t))

# # def is_location(t: str) -> bool:
# #     low = t.lower()
# #     return ("remote" in low or "hybrid" in low or "onsite" in low or "on-site" in low or ("," in t and len(t) <= 60))

# # _JOBTYPE_TOKENS = ("full time", "full-time", "part time", "part-time", "contract", "intern", "freelance")
# # def looks_like_jobtype(t: str) -> bool:
# #     low = t.lower()
# #     return any(tok in low for tok in _JOBTYPE_TOKENS)

# # async def scrape_first_job() -> Dict | None:
# #     d, prof = launch_driver()
# #     try:
# #         if not safe_get(d, LIST_URL):
# #             return None

# #         # Wait for a single card to appear
# #         WebDriverWait(d, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-job-card")))
# #         time.sleep(0.8)
# #         soup = BeautifulSoup(d.page_source, "html.parser")
# #     finally:
# #         cleanup_driver(d, prof)

# #     root_div = soup.find("div", id="root")
# #     if not root_div:
# #         print("⚠️ No root div found.")
# #         return None

# #     first_card = root_div.select_one("div.search-job-card")
# #     if not first_card:
# #         print("⚠️ No job cards found.")
# #         return None

# #     # ------- Extract from the first card -------
# #     job_link_tag = first_card.select_one('a[href^="/job/"]')
# #     apply_link = f"https://ytjobs.co{job_link_tag['href']}" if job_link_tag and job_link_tag.has_attr("href") else "N/A"

# #     title_el = job_link_tag.select_one("h1,h2,h3,h4") if job_link_tag else None
# #     title_text = (
# #         text_or_na(title_el) if title_el else
# #         (text_or_na(job_link_tag) if job_link_tag else text_or_na(first_card.find(["h1","h2","h3","h4"])))
# #     )
# #     if not title_text or title_text == "N/A":
# #         maybe_title = first_card.find(["h3", "h5"])
# #         title_text = text_or_na(maybe_title)

# #     h5_texts = [h.get_text(strip=True) for h in first_card.select("h5")]
# #     job_type = "N/A"; location = "N/A"; compensation = "N/A"

# #     for txt in h5_texts:
# #         if looks_like_jobtype(txt):
# #             job_type = txt
# #             break
# #     for txt in h5_texts:
# #         if txt == job_type:
# #             continue
# #         if location == "N/A" and is_location(txt):
# #             location = txt
# #             continue
# #         if compensation == "N/A" and is_comp(txt):
# #             compensation = txt

# #     company_img = first_card.select_one("img[alt]")
# #     company = company_img["alt"].strip() if company_img and company_img.has_attr("alt") else "N/A"
# #     thumbnail = company_img["src"] if company_img and company_img.has_attr("src") else "N/A"

# #     subs = "N/A"
# #     subs_text = first_card.find(string=re.compile(r"subscriber", re.I))
# #     if subs_text:
# #         subs = subs_text.strip()
# #     else:
# #         subs_el = first_card.find(lambda t: getattr(t, "get_text", None) and "subscriber" in t.get_text(strip=True).lower())
# #         if subs_el:
# #             subs = subs_el.get_text(strip=True)

# #     # Single detail fetch
# #     extra_details: Dict = {}
# #     if apply_link != "N/A":
# #         extra_details = await get_detail_async(apply_link)

# #     job = {
# #         "title": title_text,
# #         "job_type": job_type,
# #         "location": location,
# #         "compensation": compensation,
# #         "company": company,
# #         "subscribers": subs,
# #         "thumbnail": thumbnail,
# #         "apply_link": apply_link,
# #         **extra_details,
# #     }
# #     return job

# # # ---------------------------
# # # Runner loop (send ONLY first job)
# # # ---------------------------

# # async def main_loop():
# #     while True:
# #         print("🔄 Scraping first job...")
# #         job = await scrape_first_job()
# #         if not job:
# #             print("❌ No job found.")
# #         else:
# #             print("🧪 First job title:", job.get("title"))
# #             async with aiohttp.ClientSession() as session:
# #                 try:
# #                     async with session.post(WEBHOOK_URL, json=job) as resp:
# #                         print(f"📤 Sent FIRST job: {job.get('title','(no title)')} | Status: {resp.status}")
# #                 except Exception as e:
# #                     print(f"❌ Failed to send to webhook: {e}")
# #         await asyncio.sleep(300)  # 5 minutes

# # if __name__ == "__main__":
# #     print("🚀 Scraper starting...", flush=True)
# #     asyncio.run(main_loop())
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# import re, time, tempfile, shutil, asyncio, aiohttp, os
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from bs4 import BeautifulSoup
# from functools import partial
# from typing import Optional, Tuple, Dict, List

# CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
# LIST_URL = "https://ytjobs.co/job/search/all_categories"
# WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook-test/ytjobs"

# DEBUG_DIR = "debug_pages"
# os.makedirs(DEBUG_DIR, exist_ok=True)

# def dump_html(name: str, driver):
#     path = os.path.join(DEBUG_DIR, f"{name}.html")
#     with open(path, "w", encoding="utf-8") as f:
#         f.write(driver.page_source)
#     print(f"💾 Saved debug HTML to {path}")

# # ---------------- Chrome Setup ----------------
# def build_chrome_options(profile_dir: Optional[str] = None) -> Options:
#     opts = Options()
#     opts.add_argument("--headless=new")
#     opts.add_argument("--disable-gpu")
#     opts.add_argument("--no-sandbox")
#     opts.add_argument("--disable-dev-shm-usage")
#     opts.add_argument("--blink-settings=imagesEnabled=false")
#     opts.page_load_strategy = "normal"
#     if profile_dir:
#         opts.add_argument(f"--user-data-dir={profile_dir}")
#     return opts

# def launch_driver() -> Tuple[webdriver.Chrome, str]:
#     tmpdir = tempfile.mkdtemp(prefix="chrome-profile-")
#     service = Service(CHROMEDRIVER_PATH)
#     driver = webdriver.Chrome(service=service, options=build_chrome_options(tmpdir))
#     driver.set_page_load_timeout(60)
#     return driver, tmpdir

# def cleanup_driver(driver: webdriver.Chrome, tmpdir: Optional[str]):
#     try:
#         driver.quit()
#     finally:
#         if tmpdir:
#             shutil.rmtree(tmpdir, ignore_errors=True)

# def safe_get(driver: webdriver.Chrome, url: str, timeout: int = 60) -> bool:
#     try:
#         driver.set_page_load_timeout(timeout)
#         driver.get(url)
#         return True
#     except Exception as e:
#         print(f"⏱️ GET failed for {url}: {e}")
#         return False

# # ---------------- Detail Page Scraper ----------------
# def extract_detail_from_job_page(url: str) -> Dict:
#     d, prof = launch_driver()
#     try:
#         if not safe_get(d, url):
#             return {}
        
#         WebDriverWait(d, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
#         time.sleep(2)
#         soup = BeautifulSoup(d.page_source, "html.parser")

#         channel_anchor = soup.select_one('a[href^="/youtube-channel/"]')
#         channel_url = f"https://ytjobs.co{channel_anchor['href']}" if channel_anchor else "N/A"

#         youtube_channel_link = "N/A"
#         if channel_url != "N/A" and safe_get(d, channel_url):
#             WebDriverWait(d, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
#             ch_soup = BeautifulSoup(d.page_source, "html.parser")
#             yt_link_tag = ch_soup.select_one("a[href*='youtube.com']")
#             if yt_link_tag and yt_link_tag.has_attr("href"):
#                 youtube_channel_link = yt_link_tag["href"]

#         youtube_links = []
#         for img in soup.select("img[src*='/vi/']"):
#             src = img.get("src", "")
#             if "/vi/" in src:
#                 video_id = src.split("/vi/")[1].split("/")[0]
#                 youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")

#         posted_div = soup.find(text=re.compile("Posted on", re.I))
#         posted_date = posted_div.strip() if posted_div else "N/A"

#         exp_match = soup.find(text=re.compile("Minimum years of experience", re.I))
#         experience = exp_match.find_previous(["h6","h5","strong"]).get_text(strip=True) if exp_match else "N/A"

#         form_match = soup.find(text=re.compile("Content Format", re.I))
#         content_format = form_match.find_previous(["h6","h5","strong"]).get_text(strip=True) if form_match else "N/A"

#         details_div = soup.find("div", attrs={"data-testid": "job-description"}) \
#                        or soup.find("div", class_=re.compile("job-description", re.I)) \
#                        or soup.find("div", class_=re.compile("jQzvkT", re.I))
#         job_description = details_div.get_text(separator="\n", strip=True) if details_div else "N/A"

#         # Dump debug HTML if anything is missing
#         if any(v == "N/A" for v in [channel_url, youtube_channel_link, job_description]):
#             dump_html("job_detail_page", d)

#         return {
#             "channel_url": channel_url,
#             "youtube_channel_link": youtube_channel_link,
#             "youtube_links": youtube_links,
#             "posted_date": posted_date,
#             "experience": experience,
#             "content_format": content_format,
#             "job_description": job_description
#         }
#     finally:
#         cleanup_driver(d, prof)

# async def get_detail_async(url: str) -> Dict:
#     loop = asyncio.get_event_loop()
#     return await loop.run_in_executor(None, partial(extract_detail_from_job_page, url))

# # ---------------- Listing Page Scraper ----------------
# async def scrape_first_job() -> Dict | None:
#     d, prof = launch_driver()
#     try:
#         if not safe_get(d, LIST_URL):
#             return None

#         WebDriverWait(d, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-job-card")))
#         time.sleep(1)
#         soup = BeautifulSoup(d.page_source, "html.parser")

#         first_card = soup.select_one("div.search-job-card")
#         if not first_card:
#             return None

#         job_link_tag = first_card.select_one('a[href^="/job/"]')
#         apply_link = f"https://ytjobs.co{job_link_tag['href']}" if job_link_tag else "N/A"

#         title_text = first_card.select_one("h1,h2,h3,h4")
#         title = title_text.get_text(strip=True) if title_text else "N/A"

#         job_type = "N/A"
#         for tag in first_card.select("h5, span, div"):
#             txt = tag.get_text(strip=True).lower()
#             if any(k in txt for k in ["full time", "part time", "intern", "contract", "freelance"]):
#                 job_type = tag.get_text(strip=True)
#                 break

#         location = "N/A"
#         for tag in first_card.select("h5, span, div"):
#             txt = tag.get_text(strip=True)
#             if "remote" in txt.lower() or "onsite" in txt.lower():
#                 location = txt
#                 break

#         subscribers = "N/A"
#         sub_match = first_card.find(text=re.compile("subscriber", re.I))
#         if sub_match:
#             subscribers = sub_match.strip()

#         company_img = first_card.select_one("img[alt]")
#         company = company_img["alt"] if company_img else "N/A"
#         thumbnail = company_img["src"] if company_img else "N/A"

#         # Dump debug HTML if anything is missing
#         if any(v == "N/A" for v in [job_type, subscribers]):
#             dump_html("list_page", d)

#     finally:
#         cleanup_driver(d, prof)

#     extra_details = {}
#     if apply_link != "N/A":
#         extra_details = await get_detail_async(apply_link)

#     return {
#         "title": title,
#         "job_type": job_type,
#         "location": location,
#         "company": company,
#         "subscribers": subscribers,
#         "thumbnail": thumbnail,
#         "apply_link": apply_link,
#         **extra_details
#     }

# # ---------------- Main Loop ----------------
# async def main_loop():
#     while True:
#         job = await scrape_first_job()
#         print(job)
#         async with aiohttp.ClientSession() as session:
#             await session.post(WEBHOOK_URL, json=job)
#         await asyncio.sleep(300)

# if __name__ == "__main__":
#     print("🔥 Python process booting (post-import)...")
#     asyncio.run(main_loop())
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re, time, tempfile, shutil, asyncio, aiohttp, os, json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from functools import partial
from typing import Optional, Tuple, Dict, List

# ---------------- CONFIG ----------------
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
LIST_URL = "https://ytjobs.co/job/search/all_categories"
WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook-test/ytjobs"

DEBUG_DIR = "debug_pages"
os.makedirs(DEBUG_DIR, exist_ok=True)

JOB_TYPE_MAP = {
    "1": "Full Time",
    "2": "Part Time",
    "3": "Contract",
    "4": "Freelance",
    "5": "Internship"
}

# ---------------- DEBUG DUMP ----------------
def dump_html(name: str, driver):
    path = os.path.join(DEBUG_DIR, f"{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"💾 Saved debug HTML to {path}")

# ---------------- CHROME SETUP ----------------
def build_chrome_options(profile_dir: Optional[str] = None) -> Options:
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.page_load_strategy = "normal"
    if profile_dir:
        opts.add_argument(f"--user-data-dir={profile_dir}")
    return opts

def launch_driver() -> Tuple[webdriver.Chrome, str]:
    tmpdir = tempfile.mkdtemp(prefix="chrome-profile-")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=build_chrome_options(tmpdir))
    driver.set_page_load_timeout(60)
    return driver, tmpdir

def cleanup_driver(driver: webdriver.Chrome, tmpdir: Optional[str]):
    try:
        driver.quit()
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)

def safe_get(driver: webdriver.Chrome, url: str, timeout: int = 60) -> bool:
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(url)
        return True
    except Exception as e:
        print(f"⏱️ GET failed for {url}: {e}")
        return False

# ---------------- JOB DETAIL SCRAPER ----------------
import html

def extract_detail_from_job_page(url: str) -> Dict:
    d, prof = launch_driver()
    try:
        if not safe_get(d, url):
            return {k: "N/A" for k in [
                "channel_url", "youtube_channel_link", "youtube_links",
                "posted_date", "experience", "content_format", "job_description"
            ]}

        # Wait for the script with ___yt_cf_pcache to be present and contain data
        WebDriverWait(d, 20).until(
            lambda drv: drv.find_element(By.XPATH, "//script[contains(., '___yt_cf_pcache')]").get_attribute("innerHTML")
        )

        time.sleep(0.5)  # short buffer in case script finishes rendering

        soup = BeautifulSoup(d.page_source, "html.parser")

        # --- Extract job_data from inline script ---
        job_data = {}
        script_tag = soup.find("script", string=lambda t: t and "___yt_cf_pcache" in t)
        if script_tag:
            script_content = script_tag.string or script_tag.text
            script_content = html.unescape(script_content)  # decode &quot; etc.

            match = re.search(r"var\s+___yt_cf_pcache\s*=\s*(\[.*\]);", script_content, re.S)
            if match:
                try:
                    data = json.loads(match.group(1))
                    if isinstance(data, list) and data and "cval" in data[0]:
                        job_data = data[0]["cval"]
                        print("🔍 job_data keys:", list(job_data.keys()))
                        print("📌 job_type raw value:", job_data.get("jobType"))
                except Exception as e:
                    print(f"⚠ JSON parse failed: {e}")
            else:
                print("⚠ JSON not found in script content")
        else:
            print("⚠ Script tag not found")

        # --- Channel link ---
        channel_anchor = soup.select_one('a[href^="/youtube-channel/"]')
        channel_url = f"https://ytjobs.co{channel_anchor['href']}" \
            if channel_anchor and channel_anchor.has_attr("href") else "N/A"

        # --- YouTube channel link ---
        youtube_channel_link = job_data.get("company", {}).get("ytLink", "N/A")

        # --- YouTube video links ---
        youtube_links = []
        if job_data.get("youtubeVideos"):
            for video in job_data["youtubeVideos"]:
                if "id" in video:
                    youtube_links.append(f"https://youtube.com/watch?v={video['id']}")

        # --- Posted date ---
        posted_date = job_data.get("createdAt", "N/A")

        # --- Experience ---
        experience_text = str(job_data.get("minimumExperience", "N/A"))

        # --- Content Format ---
        content_format = job_data.get("videoType", "N/A")
        if content_format == "short":
            content_format = "Short-form"
        elif content_format == "long":
            content_format = "Long-form"

        # --- Job Description ---
        job_description = (
            BeautifulSoup(job_data.get("htmlContent", ""), "html.parser").get_text("\n", strip=True)
            if job_data.get("htmlContent") else "N/A"
        )

        return {
            "channel_url": channel_url,
            "youtube_channel_link": youtube_channel_link,
            "youtube_links": youtube_links,
            "posted_date": posted_date,
            "experience": experience_text,
            "content_format": content_format,
            "job_description": job_description,
        }

    finally:
        cleanup_driver(d, prof)


        # ---------------- Channel + YT Link ----------------
        channel_url = "N/A"
        youtube_channel_link = "N/A"
        if job_data.get("company", {}).get("channelId"):
            channel_url = f"https://ytjobs.co/youtube-channel/{job_data['company']['channelId']}"
        elif soup.select_one('a[href^="/youtube-channel/"]'):
            channel_anchor = soup.select_one('a[href^="/youtube-channel/"]')
            channel_url = f"https://ytjobs.co{channel_anchor['href']}"

        if job_data.get("company", {}).get("ytLink"):
            youtube_channel_link = job_data["company"]["ytLink"]

        # ---------------- YouTube Videos ----------------
        youtube_links: List[str] = []
        if job_data.get("youtubeVideos"):
            for vid in job_data["youtubeVideos"]:
                if vid.get("youtubeId"):
                    youtube_links.append(f"https://www.youtube.com/watch?v={vid['youtubeId']}")
        else:
            for img in soup.select("img[src*='/vi/']"):
                src = img.get("src", "")
                if "/vi/" in src:
                    video_id = src.split("/vi/")[1].split("/")[0]
                    youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")

        # ---------------- Job Type ----------------
        job_type = JOB_TYPE_MAP.get(str(job_data.get("jobType")), "N/A")

        # ---------------- Subscribers ----------------
        subscribers = "N/A"
        if job_data.get("company", {}).get("abvSubscribers"):
            subscribers = str(job_data["company"]["abvSubscribers"])
        elif sub_match := soup.find(text=re.compile("subscriber", re.I)):
            subscribers = sub_match.strip()

        # ---------------- Posted Date ----------------
        posted_date = f"Posted on: {job_data.get('createdAt')}" if job_data.get("createdAt") else "N/A"

        # ---------------- Experience ----------------
        experience = f"{job_data.get('minimumExperience')}+ Years" if job_data.get("minimumExperience") else "N/A"

        # ---------------- Content Format ----------------
        content_format = ", ".join(job_data.get("styles", [])) if job_data.get("styles") else "N/A"

        # ---------------- Job Description ----------------
        job_description = "N/A"
        if job_data.get("htmlContent"):
            job_description = BeautifulSoup(job_data["htmlContent"], "html.parser").get_text("\n", strip=True)
        elif details_div := soup.find("div", attrs={"data-testid": "job-description"}):
            job_description = details_div.get_text(separator="\n", strip=True)

        # ---------------- Compensation ----------------
        compensation = "N/A"
        if job_data.get("minSalary") and job_data.get("maxSalary"):
            compensation = f"${job_data['minSalary']}-${job_data['maxSalary']}"

        return {
            # "job_data": job_data.get(),
            "title": job_data.get("jobTitle", "N/A"),
            "job_type": job_type,
            "location": job_data.get("locationType", "N/A"),
            "compensation": compensation,
            "company": job_data.get("company", {}).get("name", "N/A"),
            "subscribers": subscribers,
            "thumbnail": job_data.get("company", {}).get("avatar", "N/A"),
            "apply_link": url,
            "channel_url": channel_url,
            "youtube_channel_link": youtube_channel_link,
            "youtube_links": youtube_links,
            "posted_date": posted_date,
            "experience": experience,
            "content_format": content_format,
            "job_description": job_description
        }
    finally:
        cleanup_driver(d, prof)

async def get_detail_async(url: str) -> Dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(extract_detail_from_job_page, url))

# ---------------- Listing Page Scraper ----------------
async def scrape_first_job() -> Dict | None:
    d, prof = launch_driver()
    try:
        if not safe_get(d, LIST_URL):
            return None

        WebDriverWait(d, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-job-card")))
        time.sleep(1)
        soup = BeautifulSoup(d.page_source, "html.parser")

        first_card = soup.select_one("div.search-job-card")
        if not first_card:
            return None

        job_link_tag = first_card.select_one('a[href^="/job/"]')
        apply_link = f"https://ytjobs.co{job_link_tag['href']}" if job_link_tag else "N/A"

        title_text = first_card.select_one("h1,h2,h3,h4")
        title = title_text.get_text(strip=True) if title_text else "N/A"

        job_type = "N/A"
        for tag in first_card.select("h5, span, div"):
            txt = tag.get_text(strip=True).lower()
            if any(k in txt for k in ["full time", "part time", "intern", "contract", "freelance"]):
                job_type = tag.get_text(strip=True)
                break

        location = "N/A"
        for tag in first_card.select("h5, span, div"):
            txt = tag.get_text(strip=True)
            if "remote" in txt.lower() or "onsite" in txt.lower():
                location = txt
                break

        subscribers = "N/A"
        sub_match = first_card.find(text=re.compile("subscriber", re.I))
        if sub_match:
            subscribers = sub_match.strip()

        company_img = first_card.select_one("img[alt]")
        company = company_img["alt"] if company_img else "N/A"
        thumbnail = company_img["src"] if company_img else "N/A"

        # Dump debug HTML if anything is missing
        if any(v == "N/A" for v in [job_type, subscribers]):
            dump_html("list_page", d)

    finally:
        cleanup_driver(d, prof)

    extra_details = {}
    if apply_link != "N/A":
        extra_details = await get_detail_async(apply_link)

    return {
        "title": title,
        "job_type": job_type,
        "location": location,
        "company": company,
        "subscribers": subscribers,
        "thumbnail": thumbnail,
        "apply_link": apply_link,
        **extra_details
    }


# ---------------- MAIN LOOP ----------------
async def main_loop():
    while True:
        job = await scrape_first_job()
        print(job)
        async with aiohttp.ClientSession() as session:
            await session.post(WEBHOOK_URL, json=job)
        await asyncio.sleep(300)

if __name__ == "__main__":
    print("🔥 Python process booting (post-import)...")
    asyncio.run(main_loop())
