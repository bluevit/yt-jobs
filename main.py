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
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.common.by import By
# import re, time, tempfile, shutil, asyncio, aiohttp, os, json, html
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.support.ui import WebDriverWait
# from bs4 import BeautifulSoup
# from functools import partial
# from typing import Optional, Tuple, Dict, List

# # ---------------- CONFIG ----------------
# CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
# LIST_URL = "https://ytjobs.co/job/search/all_categories"
# WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook-test/ytjobs"

# DEBUG_DIR = "debug_pages"
# os.makedirs(DEBUG_DIR, exist_ok=True)

# JOB_TYPE_MAP = {
#     "1": "Full Time",
#     "2": "Part Time",
#     "3": "Contract",
#     "4": "Freelance",
#     "5": "Internship"
# }

# # ---------------- UTIL / DEBUG ----------------
# def dump_html(name: str, driver):
#     path = os.path.join(DEBUG_DIR, f"{name}.html")
#     with open(path, "w", encoding="utf-8") as f:
#         f.write(driver.page_source)
#     print(f"💾 Saved debug HTML to {path}")

# def _try_parse_json_blobs_from_scripts(soup: BeautifulSoup) -> List[object]:
#     parsed: List[object] = []
#     for s in soup.find_all("script"):
#         raw = (s.string or s.text or "").strip()
#         if not raw:
#             continue
#         raw = html.unescape(raw)

#         if (raw.startswith("{") and raw.endswith("}")) or (raw.startswith("[") and raw.endswith("]")):
#             try:
#                 parsed.append(json.loads(raw))
#                 continue
#             except Exception:
#                 pass

#         m = re.search(r"=\s*(\{.*\}|\[.*\])\s*;?", raw, flags=re.S)
#         if m:
#             blob = m.group(1)
#             for candidate in (blob, html.unescape(blob)):
#                 try:
#                     parsed.append(json.loads(candidate))
#                     break
#                 except Exception:
#                     continue
#     return parsed

# def _pick_job_payload(json_candidates: List[object]) -> Optional[dict]:
#     def looks_like_job_dict(d: dict) -> bool:
#         k = set(d.keys())
#         return bool({"jobTitle", "company", "htmlContent"} & k) or "youtubeVideos" in d

#     for obj in json_candidates:
#         if isinstance(obj, dict):
#             if looks_like_job_dict(obj):
#                 return obj
#             for k in ("props", "pageProps", "__APOLLO_STATE__", "data"):
#                 if k in obj:
#                     stack = [obj[k]]
#                     seen = set()
#                     while stack:
#                         cur = stack.pop()
#                         if id(cur) in seen:
#                             continue
#                         seen.add(id(cur))
#                         if isinstance(cur, dict):
#                             if looks_like_job_dict(cur):
#                                 return cur
#                             stack.extend(cur.values())
#                         elif isinstance(cur, list):
#                             stack.extend(cur)

#     for obj in json_candidates:
#         if isinstance(obj, list) and obj:
#             first = obj[0]
#             if isinstance(first, dict) and "cval" in first and isinstance(first["cval"], dict):
#                 return first["cval"]
#             for it in obj:
#                 if isinstance(it, dict) and looks_like_job_dict(it):
#                     return it
#     return None

# def _clean_text(s: Optional[str]) -> str:
#     if not s:
#         return "N/A"
#     return s.strip()

# def _clean_url(u: Optional[str]) -> str:
#     if not u:
#         return "N/A"
#     return u.strip().rstrip(" ;,)")

# # ---------------- CHROME SETUP ----------------
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

# # ---------------- JOB DETAIL SCRAPER ----------------
# def extract_detail_from_job_page(url: str) -> Dict:
#     d, prof = launch_driver()
#     try:
#         if not safe_get(d, url):
#             return {
#                 "channel_url": "N/A",
#                 "youtube_channel_link": "N/A",
#                 "youtube_links": [],
#                 "posted_date": "N/A",
#                 "experience": "N/A",
#                 "content_format": "N/A",
#                 "job_description": "N/A",
#             }

#         WebDriverWait(d, 25).until(
#             EC.any_of(
#                 EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-description']")),
#                 EC.presence_of_element_located((By.CSS_SELECTOR, "body script")),
#                 EC.presence_of_element_located((By.XPATH, "//*[contains(., 'Posted')]"))
#             )
#         )
#         time.sleep(0.5)

#         soup = BeautifulSoup(d.page_source, "html.parser")
#         json_candidates = _try_parse_json_blobs_from_scripts(soup)
#         job_data = _pick_job_payload(json_candidates)

#         channel_anchor = soup.select_one('a[href^="/youtube-channel/"]')
#         channel_url = (
#             _clean_url(f"https://ytjobs.co{channel_anchor['href']}")
#             if channel_anchor and channel_anchor.has_attr("href") else "N/A"
#         )

#         youtube_channel_link = "N/A"
#         if isinstance(job_data, dict):
#             youtube_channel_link = _clean_url(job_data.get("company", {}).get("ytLink")) if job_data.get("company") else "N/A"

#         youtube_links: List[str] = []
#         if isinstance(job_data, dict) and job_data.get("youtubeVideos"):
#             for video in job_data["youtubeVideos"]:
#                 vid = video.get("id") or video.get("youtubeId")
#                 if vid:
#                     youtube_links.append(_clean_url(f"https://youtube.com/watch?v={vid}"))
#         if not youtube_links:
#             for img in soup.select("img[src*='/vi/']"):
#                 src = img.get("src", "")
#                 if "/vi/" in src:
#                     try:
#                         video_id = src.split("/vi/")[1].split("/")[0]
#                         youtube_links.append(_clean_url(f"https://www.youtube.com/watch?v={video_id}"))
#                     except Exception:
#                         pass

#         posted_date = "N/A"
#         experience_text = "N/A"
#         content_format = "N/A"
#         job_description = "N/A"

#         if isinstance(job_data, dict):
#             posted_date = _clean_text(job_data.get("createdAt"))
#             experience_text = _clean_text(str(job_data.get("minimumExperience"))) if job_data.get("minimumExperience") is not None else "N/A"

#             vtype = job_data.get("videoType")
#             if vtype == "short":
#                 content_format = "Short-form"
#             elif vtype == "long":
#                 content_format = "Long-form"
#             elif isinstance(vtype, str):
#                 content_format = _clean_text(vtype)

#             if job_data.get("htmlContent"):
#                 job_description = BeautifulSoup(job_data["htmlContent"], "html.parser").get_text("\n", strip=True)

#         if job_description == "N/A":
#             details_div = soup.find("div", attrs={"data-testid": "job-description"}) \
#                         or soup.find("div", class_=re.compile("job-description", re.I))
#             if details_div:
#                 job_description = details_div.get_text("\n", strip=True)

#         return {
#             "channel_url": channel_url,
#             "youtube_channel_link": youtube_channel_link,
#             "youtube_links": youtube_links,
#             "posted_date": posted_date,
#             "experience": experience_text,
#             "content_format": content_format,
#             "job_description": job_description,
#         }

#     finally:
#         cleanup_driver(d, prof)

# async def get_detail_async(url: str) -> Dict:
#     loop = asyncio.get_event_loop()
#     return await loop.run_in_executor(None, partial(extract_detail_from_job_page, url))

# # ---------------- LISTING PAGE SCRAPER ----------------
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
#             print("⚠ No job cards found on list page")
#             dump_html("list_page", d)
#             return None

#         job_link_tag = first_card.select_one('a[href^="/job/"]')
#         apply_link = _clean_url(f"https://ytjobs.co{job_link_tag['href']}") if job_link_tag and job_link_tag.has_attr("href") else "N/A"

#         title_el = first_card.select_one("h1,h2,h3,h4") or first_card.find(["h1","h2","h3","h4"])
#         title = _clean_text(title_el.get_text(strip=True) if title_el else None)

#         job_type = "N/A"
#         for tag in first_card.select("h5, span, div"):
#             txt = tag.get_text(strip=True).lower()
#             if any(k in txt for k in ["full time", "full-time", "part time", "part-time", "intern", "contract", "freelance"]):
#                 job_type = _clean_text(tag.get_text(strip=True))
#                 break

#         location = "N/A"
#         for tag in first_card.select("h5, span, div"):
#             txt = tag.get_text(strip=True)
#             low = txt.lower()
#             if "remote" in low or "onsite" in low or "on-site" in low or "hybrid" in low:
#                 location = _clean_text(txt)
#                 break

#         subscribers = "N/A"
#         sub_match = first_card.find(string=re.compile("subscriber", re.I))
#         if sub_match:
#             subscribers = _clean_text(sub_match)

#         company_img = first_card.select_one("img[alt]")
#         company = _clean_text(company_img["alt"]) if (company_img and company_img.has_attr("alt")) else "N/A"
#         thumbnail = _clean_url(company_img["src"]) if (company_img and company_img.has_attr("src")) else "N/A"

#         if any(v == "N/A" for v in [job_type, subscribers, title]):
#             dump_html("list_page", d)

#     finally:
#         cleanup_driver(d, prof)

#     extra_details: Dict = {}
#     if apply_link != "N/A":
#         extra_details = await get_detail_async(apply_link)

#     job = {
#         "title": title,
#         "job_type": job_type,
#         "location": location,
#         "company": company,
#         "subscribers": subscribers,
#         "thumbnail": thumbnail,
#         "apply_link": apply_link,
#         **extra_details
#     }
#     return job

# # ---------------- MAIN LOOP ----------------
# async def main_loop():
#     while True:
#         job = await scrape_first_job()
#         print("📦 Job payload:", job)
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(WEBHOOK_URL, json=job, timeout=30) as resp:
#                     print(f"📤 Sent to webhook. Status: {resp.status}")
#                     if resp.status >= 400:
#                         body = await resp.text()
#                         print(f"⚠ Webhook error body: {body[:500]}...")
#         except Exception as e:
#             print(f"❌ Failed to send to webhook: {e}")
#         await asyncio.sleep(300)

# if __name__ == "__main__":
#     print("🔥 Python process booting (post-import)...")
#     asyncio.run(main_loop())


from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re, time, tempfile, shutil, asyncio, aiohttp, os, json, html
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
WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook-test/ytjobs"  # arm test webhook in n8n editor

DEBUG_DIR = "debug_pages"
os.makedirs(DEBUG_DIR, exist_ok=True)

JOB_TYPE_MAP = {
    "1": "Full Time",
    "2": "Part Time",
    "3": "Contract",
    "4": "Freelance",
    "5": "Internship"
}

# ---------------- UTILITIES ----------------
def dump_html(name: str, driver):
    path = os.path.join(DEBUG_DIR, f"{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"💾 Saved debug HTML to {path}")

def _clean_text(s: Optional[str]) -> str:
    if not s:
        return "N/A"
    return re.sub(r"\s+", " ", str(s)).strip()

def _clean_url(u: Optional[str]) -> str:
    if not u:
        return "N/A"
    u = str(u).strip()
    return re.sub(r"""[\s'";,)\]]+$""", "", u)

def _normalize_job_type(raw) -> str:
    if raw is None:
        return "N/A"
    if isinstance(raw, (int, float)) or (isinstance(raw, str) and raw.isdigit()):
        return JOB_TYPE_MAP.get(str(raw), "N/A")
    low = str(raw).lower()
    for k in ("full-time", "full time", "part-time", "part time", "contract", "freelance", "intern"):
        if k in low:
            return _clean_text(raw)
    return _clean_text(raw)

def _fmt_compensation_str(min_salary, max_salary) -> str:
    """
    Single string for compensation. No currency symbol assumed.
    """
    comp_min = None if min_salary in (None, "", "N/A") else int(min_salary)
    comp_max = None if max_salary in (None, "", "N/A") else int(max_salary)
    if comp_min is not None and comp_max is not None:
        return f"{comp_min:,}–{comp_max:,}"
    if comp_min is not None:
        return f"{comp_min:,}+"
    if comp_max is not None:
        return f"up to {comp_max:,}"
    return "N/A"

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

# ---------------- DETAIL PAGE ----------------
def _parse_pcache_from_soup(soup: BeautifulSoup) -> dict:
    """
    Locate and parse:  var ___yt_cf_pcache = [ { ckey: [...], cval: {...job...} } ];
    Returns cval dict or {}.
    """
    for s in soup.find_all("script"):
        raw = (s.string or s.text or "").strip()
        if "___yt_cf_pcache" not in raw:
            continue
        m = re.search(r"var\s+___yt_cf_pcache\s*=\s*(\[.*\]);?", raw, flags=re.S)
        if not m:
            continue
        try:
            arr = json.loads(html.unescape(m.group(1)))
            if isinstance(arr, list) and arr and isinstance(arr[0], dict) and "cval" in arr[0]:
                return arr[0]["cval"]
        except Exception:
            pass
    return {}

def extract_detail_from_job_page(url: str) -> Dict:
    d, prof = launch_driver()
    try:
        if not safe_get(d, url):
            return {
                "title": "N/A", "job_type": "N/A", "location": "N/A", "company": "N/A",
                "subscribers": "N/A", "thumbnail": "N/A", "apply_link": _clean_url(url),
                "channel_url": "N/A", "youtube_channel_link": "N/A", "youtube_links": [],
                "posted_date": "N/A", "experience": "N/A", "content_format": "N/A",
                "compensation": "N/A",
                "job_description": "N/A",
            }

        WebDriverWait(d, 25).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body script")),
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-description']"))
            )
        )
        time.sleep(0.5)

        soup = BeautifulSoup(d.page_source, "html.parser")
        job = _parse_pcache_from_soup(soup)  # cval dict from ___yt_cf_pcache

        # ------ map fields from JSON ------
        title = _clean_text(job.get("jobTitle"))
        location = _clean_text(job.get("locationType"))
        job_type = _normalize_job_type(job.get("jobType"))

        comp = job.get("company") if isinstance(job.get("company"), dict) else {}
        company = _clean_text(comp.get("name")) if comp else "N/A"
        thumbnail = _clean_url(comp.get("avatar")) if comp else "N/A"
        subscribers = _clean_text(str(comp.get("abvSubscribers"))) if comp and comp.get("abvSubscribers") is not None else "N/A"

        channel_url = "N/A"
        if comp and comp.get("channelId"):
            channel_url = _clean_url(f"https://ytjobs.co/youtube-channel/{comp['channelId']}")
        else:
            a = soup.select_one('a[href^="/youtube-channel/"]')
            if a and a.has_attr("href"):
                channel_url = _clean_url(f"https://ytjobs.co{a['href']}")
        youtube_channel_link = _clean_url(comp.get("ytLink")) if comp else "N/A"

        # YouTube video URLs (use .url, not .id)
        youtube_links: List[str] = []
        vids = job.get("youtubeVideos")
        if isinstance(vids, list):
            for v in vids:
                if isinstance(v, dict) and v.get("url"):
                    youtube_links.append(_clean_url(v["url"]))
                else:
                    thumb = v.get("thumbnail", "") if isinstance(v, dict) else ""
                    if "/vi/" in thumb:
                        try:
                            vid_id = thumb.split("/vi/")[1].split("/")[0]
                            youtube_links.append(_clean_url(f"https://youtube.com/watch?v={vid_id}"))
                        except Exception:
                            pass

        posted_date = _clean_text(job.get("createdAt"))

        experience_text = "N/A"
        if job.get("minimumExperience") is not None:
            experience_text = _clean_text(str(job.get("minimumExperience")))

        vtype = job.get("videoType")
        if vtype == "short":
            content_format = "Short-form"
        elif vtype == "long":
            content_format = "Long-form"
        elif vtype == "all":
            content_format = "All"
        else:
            content_format = _clean_text(vtype) if vtype else "N/A"

        job_description = "N/A"
        if job.get("htmlContent"):
            job_description = BeautifulSoup(job["htmlContent"], "html.parser").get_text("\n", strip=True)
        else:
            details_div = soup.find("div", attrs={"data-testid": "job-description"}) \
                        or soup.find("div", class_=re.compile("job-description", re.I))
            if details_div:
                job_description = details_div.get_text("\n", strip=True)

        # Single compensation string
        compensation = _fmt_compensation_str(job.get("minSalary"), job.get("maxSalary"))

        # Fallbacks from DOM if essentials are missing
        if title == "N/A":
            h = soup.select_one("h1,h2,h3,h4") or soup.find(["h1","h2","h3","h4"])
            if h: title = _clean_text(h.get_text(strip=True))
        if (company == "N/A" or thumbnail == "N/A"):
            company_img = soup.select_one("img[alt]")
            if company == "N/A" and company_img and company_img.has_attr("alt"):
                company = _clean_text(company_img["alt"])
            if thumbnail == "N/A" and company_img and company_img.has_attr("src"):
                thumbnail = _clean_url(company_img["src"])

        return {
            "title": title,
            "job_type": job_type,
            "location": location,
            "company": company,
            "subscribers": subscribers,
            "thumbnail": thumbnail,
            "apply_link": _clean_url(url),
            "channel_url": channel_url,
            "youtube_channel_link": youtube_channel_link,
            "youtube_links": youtube_links,
            "posted_date": posted_date,
            "experience": experience_text,
            "content_format": content_format,
            "compensation": compensation,
            "job_description": job_description,
        }

    finally:
        cleanup_driver(d, prof)

async def get_detail_async(url: str) -> Dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(extract_detail_from_job_page, url))

# ---------------- LIST PAGE (get first job link) ----------------
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
            print("⚠ No job cards found on list page")
            dump_html("list_page", d)
            return None

        job_link_tag = first_card.select_one('a[href^="/job/"]')
        apply_link = _clean_url(f"https://ytjobs.co{job_link_tag['href']}") if job_link_tag and job_link_tag.has_attr("href") else "N/A"

    finally:
        cleanup_driver(d, prof)

    if apply_link == "N/A":
        print("⚠ Could not resolve apply_link from first card")
        return None

    detail = await get_detail_async(apply_link)
    detail["apply_link"] = detail.get("apply_link", _clean_url(apply_link))
    return detail

# ---------------- MAIN LOOP ----------------
async def main_loop():
    while True:
        job = await scrape_first_job()
        print("📦 Job payload:", job)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(WEBHOOK_URL, json=job, timeout=30) as resp:
                    print(f"📤 Sent to webhook. Status: {resp.status}")
                    if resp.status >= 400:
                        body = await resp.text()
                        print(f"⚠ Webhook error body: {body[:500]}...")
        except Exception as e:
            print(f"❌ Failed to send to webhook: {e}")
        await asyncio.sleep(300)  # every 5 minutes

if __name__ == "__main__":
    print("🔥 Python process booting (post-import)...")
    asyncio.run(main_loop())
