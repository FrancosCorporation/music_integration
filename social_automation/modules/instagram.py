# instagram.py
from .base import SocialPlatform, VideoMeta
from playwright.async_api import async_playwright
from pathlib import Path

class InstagramPlatform(SocialPlatform):
    platform_name = "instagram"
    LOGIN_URL = "https://www.instagram.com/accounts/login/"

    async def login_interactive(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, persistent_context=str(self.session_dir))
            page = await browser.new_page()
            await page.goto(self.LOGIN_URL)
            print("Please log in to Instagram in the opened browser.")
            await page.wait_for_url("https://www.instagram.com/", timeout=120000)
            # Save cookies
            cookies = await page.context.cookies()
            self._save_session(cookies)
            await browser.close()

    async def post_video(self, video: VideoMeta) -> dict:
        if not self.is_logged_in():
            raise RuntimeError("Not logged in")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, persistent_context=str(self.session_dir))
            page = await browser.new_page()
            await page.goto("https://www.instagram.com/")
            # Navigate to Reels creation (simplified)
            await page.click('svg[aria-label="New post"]')
            await page.wait_for_selector('input[type="file"]')
            await page.set_input_files('input[type="file"]', str(video.file_path))
            # fill caption
            await page.fill('textarea[placeholder="Write a caption..."]', video.description or "")
            await page.click('text=Share')
            await page.wait_for_selector('text=Your reel has been shared', timeout=120000)
            await browser.close()
        return {"status": "posted"}
