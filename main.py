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
WEBHOOK_URL = "https://zealancy.app.n8n.cloud/webhook/ytjobs" 

DEBUG_DIR = "debug_pages"
os.makedirs(DEBUG_DIR, exist_ok=True)

JOB_TYPE_MAP = {
    "1": "Projects and Gigs",
    "3": "Full Time",
    "5": "Part-time",
}

def _normalize_job_type(raw) -> str:
    """Strictly map numeric code → label; anything else → 'N/A'."""
    try:
        code = str(int(float(str(raw).strip())))
        return JOB_TYPE_MAP.get(code, "N/A")
    except Exception:
        return "N/A"


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

# add near your other maps/utilities
VIDEO_TYPE_MAP = {
    "short": "Short-form",
    "shorts": "Short-form",
    "short-form": "Short-form",
    "long": "Long-form",
    "normal": "Long-form",   
    "long-form": "Long-form",
    "all": "Short-form, Long-form",
    "both": "Short-form, Long-form",
}

def _normalize_video_type(v) -> str:
    if not v:
        return "N/A"
    key = str(v).strip().lower()
    return VIDEO_TYPE_MAP.get(key, key.capitalize())

def _fmt_compensation_str(min_salary, max_salary, period: str | None = None) -> str:
    comp_min = None if min_salary in (None, "", "N/A") else int(min_salary)
    comp_max = None if max_salary in (None, "", "N/A") else int(max_salary)

    if comp_min is not None and comp_max is not None:
        base = f"{comp_min:,}–{comp_max:,}"
    elif comp_min is not None:
        base = f"{comp_min:,}+"
    elif comp_max is not None:
        base = f"up to {comp_max:,}"
    else:
        base = "N/A"

    if base != "N/A" and period:
        return f"{base} per {period.lower()}"
    return base

def _extract_pay_period(job: dict, soup: BeautifulSoup) -> str | None:
    """
    Your provided pcache doesn't include period fields, so:
    1) (If ever added) try common JSON keys.
    2) Fallback: scan DOM text for 'per {year|month|week|hour|day}'.
    """
    # 1) If YTJobs ever adds a key, it'll be picked up here:
    for k in ("salaryPeriod", "salaryType", "payPeriod", "payType", "compensationPeriod"):
        v = job.get(k)
        if v:
            return str(v).strip().lower()

    # 2) DOM fallback: look for "per year/month/week/hour/day"
    text = soup.get_text(" ", strip=True)
    m = re.search(r"\bper\s+(year|month|week|hour|day)\b", text, re.I)
    if m:
        return m.group(1).lower()
    return None    


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

        content_format = _normalize_video_type(job.get("videoType"))

        job_description = "N/A"
        if job.get("htmlContent"):
            job_description = BeautifulSoup(job["htmlContent"], "html.parser").get_text("\n", strip=True)
        else:
            details_div = soup.find("div", attrs={"data-testid": "job-description"}) \
                        or soup.find("div", class_=re.compile("job-description", re.I))
            if details_div:
                job_description = details_div.get_text("\n", strip=True)

        # Single compensation string
        period = _extract_pay_period(job, soup)  # <- NEW
        compensation = _fmt_compensation_str(job.get("minSalary"), job.get("maxSalary"), period)
        # compensation = _fmt_compensation_str(job.get("minSalary"), job.get("maxSalary"))

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
            "minimum_experience(year)": experience_text,
            "content_format": content_format,
            "compensation($)": compensation,
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
        # print("📦 Job payload:", job)  # uncomment to view the extracted job details
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
