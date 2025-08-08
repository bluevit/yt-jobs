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
WEBHOOK_URL = "https://automationsinc.app.n8n.cloud/webhook/ytjobs"

def get_chrome_options():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-sync")
    options.add_argument("--metrics-recording-only")
    options.add_argument("--disable-default-apps")
    options.add_argument("--mute-audio")
    options.add_argument("--remote-debugging-port=9222")  # ✅ important for Chrome startup
    options.add_argument("--user-data-dir=/tmp/chrome-profile")  # ✅ fixes session errors


      # ✅ FIX: prevent session not created
    return options

def extract_youtube_links_from_page(url):
    options = get_chrome_options()
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        channel_anchor = soup.select_one("a.sc-EElJA.kAvggH[href^='/youtube-channel/']")
        channel_url = "https://ytjobs.co" + channel_anchor["href"] if channel_anchor else "N/A"

        youtube_channel_link = "N/A"
        if channel_url != "N/A":
            driver.get(channel_url)
            time.sleep(3)
            channel_soup = BeautifulSoup(driver.page_source, "html.parser")
            yt_link_tag = channel_soup.select_one("section.channel-page-header a[href*='youtube.com']")
            if yt_link_tag and yt_link_tag.has_attr("href"):
                youtube_channel_link = yt_link_tag["href"]

        containers = soup.find_all("div", class_="yt-video-img-container")
        youtube_links = []
        for container in containers:
            img = container.find("img", class_="yt-video-img-el")
            if img and img.has_attr("src"):
                src = img["src"]
                try:
                    video_id = src.split("/vi/")[1].split("/")[0]
                    youtube_links.append(f"https://www.youtube.com/watch?v={video_id}")
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

    finally:
        driver.quit()

async def get_extra_details_async(url):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(extract_youtube_links_from_page, url))

async def scrape_yt_jobs():
    options = get_chrome_options()
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://ytjobs.co/job/search/all_categories")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    root_div = soup.find("div", id="root")
    if not root_div:
        return []

    job_cards = root_div.find_all("div", class_="search-job-card")

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

async def main_loop():
    while True:
        print("🔄 Scraping jobs...")
        jobs = await scrape_yt_jobs()
        if not jobs:
            print("❌ No jobs found.")
        else:
            for job in jobs[:5]:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(WEBHOOK_URL, json=job) as resp:
                            print(f"📤 Sent {len(jobs)} jobs | Status: {resp.status}")
                except Exception as e:
                    print(f"❌ Failed to send to webhook: {e}")
        await asyncio.sleep(300)  # wait 5 minutes

if __name__ == "__main__":
    print("🚀 Scraper starting...")
    asyncio.run(main_loop())
