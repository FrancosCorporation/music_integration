# tiktok.py
from .base import SocialPlatform, VideoMeta
from playwright.async_api import async_playwright
from pathlib import Path

class TikTokPlatform(SocialPlatform):
    platform_name = "tiktok"
    LOGIN_URL = "https://www.tiktok.com/login"

    async def login_interactive(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, persistent_context=str(self.session_dir))
            page = await browser.new_page()
            await page.goto(self.LOGIN_URL)
            print("Please log in to TikTok in the opened browser.")
            await page.wait_for_url("https://www.tiktok.com/**", timeout=120000)
            cookies = await page.context.cookies()
            self._save_session(cookies)
            await browser.close()

    async def post_video(self, video: VideoMeta) -> dict:
        if not self.is_logged_in():
            raise RuntimeError("Not logged in")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, persistent_context=str(self.session_dir))
            page = await browser.new_page()
            await page.goto("https://www.tiktok.com/upload")
            await page.wait_for_selector('input[type="file"]')
            await page.set_input_files('input[type="file"]', str(video.file_path))
            await page.fill('div[contenteditable="true"]', video.description or "")
            await page.click('button:has-text("Post")')
            await page.wait_for_selector('text=Your video has been posted', timeout=120000)
            await browser.close()
        return {"status": "posted"}
