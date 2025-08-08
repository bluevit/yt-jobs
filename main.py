import discord
from discord.ext import commands, tasks
import os
import time
import aiohttp
import asyncio
from functools import partial
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_YTBOT_TOKEN")
WEBHOOK_URL = "https://automationsinc.app.n8n.cloud/webhook/ytjobs"  # Your webhook

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# === Blocking function to extract job details from individual job page ===
# def extract_youtube_links_from_page(url):
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")

#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     driver.get(url)
#     time.sleep(5)
#     soup = BeautifulSoup(driver.page_source, "html.parser")
#     driver.quit()
#     # print(soup.prettify())

#     # YouTube links
#     containers = soup.find_all("div", class_="yt-video-img-container")
#     youtube_links = []
#     for container in containers:
#         img = container.find("img", class_="yt-video-img-el")
#         if img and img.has_attr("src"):
#             src = img["src"]
#             try:
#                 video_id = src.split("/vi/")[1].split("/")[0]
#                 youtube_url = f"https://www.youtube.com/watch?v={video_id}"
#                 youtube_links.append(youtube_url)
#             except IndexError:
#                 continue

#     # Posted date
#     posted_div = soup.find("div", class_="Couww")
#     posted_date = posted_div.get_text(strip=True) if posted_div else "N/A"

#     # Experience
#     experience_p = soup.find("p", string=lambda text: "Minimum years of experience" in text if text else False)
#     if experience_p:
#         experience_h6 = experience_p.find_previous("h6")
#         experience_text = experience_h6.get_text(strip=True) if experience_h6 else "N/A"
#     else:
#         experience_text = "N/A"

#     # Job description
#     details_div = soup.find("div", class_="jQzvkT")
#     job_details = details_div.get_text(separator="\n", strip=True) if details_div else "N/A"
#     job_details = re.sub(r'\s+', ' ', job_details.replace('\n', ' '))

#     return {
#         "youtube_links": youtube_links,
#         "posted_date": posted_date,
#         "experience": experience_text,
#         "job_description": job_details
#     }

def extract_youtube_links_from_page(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    # driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=options)   
    driver.get(url)
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Step 1: Get the channel page URL
    channel_anchor = soup.select_one("a.sc-EElJA.kAvggH[href^='/youtube-channel/']")
    channel_url = "https://ytjobs.co" + channel_anchor["href"] if channel_anchor else "N/A"

    # Step 2: Open the channel page to get YouTube channel link
    youtube_channel_link = "N/A"
    if channel_url != "N/A":
        driver.get(channel_url)
        time.sleep(3)
        channel_soup = BeautifulSoup(driver.page_source, "html.parser")
        yt_link_tag = channel_soup.select_one("section.channel-page-header a[href*='youtube.com']")
        if yt_link_tag and yt_link_tag.has_attr("href"):
            youtube_channel_link = yt_link_tag["href"]

    driver.quit()

    # Other job details (unchanged)
    containers = soup.find_all("div", class_="yt-video-img-container")
    youtube_links = []
    for container in containers:
        img = container.find("img", class_="yt-video-img-el")
        if img and img.has_attr("src"):
            src = img["src"]
            try:
                video_id = src.split("/vi/")[1].split("/")[0]
                youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                youtube_links.append(youtube_url)
            except IndexError:
                continue

    posted_div = soup.find("div", class_="Couww")
    posted_date = posted_div.get_text(strip=True) if posted_div else "N/A"

    experience_p = soup.find("p", string=lambda text: "Minimum years of experience" in text if text else False)
    experience_text = experience_p.find_previous("h6").get_text(strip=True) if experience_p else "N/A"

    form_p = soup.find("p", string=lambda text: "Content Format" in text if text else False)
    form_text = form_p.find_previous("h6").get_text(strip=True) if form_p else "N/A"

    details_div = soup.find("div", class_="jQzvkT")
    job_details = re.sub(r'\s+', ' ', details_div.get_text(separator="\n", strip=True)) if details_div else "N/A"

    return {
        "youtube_links": youtube_links,
        "youtube_channel_link": youtube_channel_link,
        "posted_date": posted_date,
        "experience": experience_text,
        "job_description": job_details,
        "content_format": form_text
    }

# === Async wrapper to run the blocking detail extraction in a thread ===
async def get_extra_details_async(url):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(extract_youtube_links_from_page, url))

# === Main scraper (async version) ===
async def scrape_yt_jobs():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])


    CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    # driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", options=options)
    driver.get("https://ytjobs.co/job/search/all_categories")
    time.sleep(5)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    root_div = soup.find("div", id="root")
    if not root_div:
        return []

    job_cards = root_div.find_all("div", class_="search-job-card")
    jobs = []

    async def extract_job_data(card):
        try:
            title = card.select_one("h4.sc-ddcbSj")
            job_type = card.select_one("h5.sc-bmCPhp")
            info_tags = card.select("h5.sc-cCAuRX")
            location = info_tags[0] if len(info_tags) > 0 else None
            compensation = info_tags[1] if len(info_tags) > 1 else None
            company_img = card.select_one("a.sc-knuQbY img")
            channel_stats = card.select_one(".sc-ERObt")
            apply_link_tag = card.select_one("a[href]")

            apply_link = "https://ytjobs.co" + apply_link_tag["href"] if apply_link_tag and apply_link_tag.has_attr("href") else "N/A"
            extra_details = await get_extra_details_async(apply_link) if apply_link != "N/A" else {}

            return {
                "title": title.get_text(strip=True) if title else "N/A",
                "job_type": job_type.get_text(strip=True) if job_type else "N/A",
                "location": location.get_text(strip=True) if location else "N/A",
                "compensation": compensation.get_text(strip=True) if compensation else "N/A",
                "company": company_img["alt"].strip() if company_img and company_img.has_attr("alt") else "N/A",
                "subscribers": channel_stats.get_text(strip=True) if channel_stats else "N/A",
                "thumbnail": company_img["src"] if company_img and company_img.has_attr("src") else "N/A",
                "apply_link": apply_link,
                **extra_details
            }

        except Exception as e:
            print(f"❌ Error parsing job card: {e}")
            return None

    jobs = await asyncio.gather(*(extract_job_data(card) for card in job_cards))
    return [job for job in jobs if job is not None]

# === Bot ready event ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    post_jobs.start()

# === Scheduled task to run every 5 minutes ===
@tasks.loop(minutes=5)
async def post_jobs():
    print("🔄 Scraping jobs...")
    jobs = await scrape_yt_jobs()

    if not jobs:
        print("❌ No jobs found.")
        return

    for job in jobs[:5]:  # send first 5 only
        if WEBHOOK_URL:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(WEBHOOK_URL, json=job) as resp:
                        print(f"📤 Sent job: {job['title']} | Status: {resp.status}")
            except Exception as e:
                print(f"❌ Failed to send to webhook: {e}")

# === Run the bot ===
bot.run(TOKEN)
