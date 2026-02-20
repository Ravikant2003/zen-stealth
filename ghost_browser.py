import asyncio
import os
import zendriver as zd
from humanizer import Humanizer
from stealth_utils import StealthUtils
from dotenv import load_dotenv

load_dotenv()

async def run_ghost_browser(url, proxy_url=None):
    # Wait for Xwayland to fully initialize (race condition fix)
    await asyncio.sleep(5)

    # Setup zendriver config with increased timeouts for Rosetta emulation
    config = zd.Config(
        browser_connection_max_tries=20,
        browser_connection_timeout=5
    )
    if proxy_url:
        config.proxy = proxy_url
    
    # Use built-in Google Chrome with explicit path for container stability
    config.browser_executable_path = "/usr/bin/google-chrome"
    
    # Start browser with config and sandbox disabled
    browser = await zd.start(config, no_sandbox=True)
    
    # In zendriver/nodriver, we work with the main_tab
    tab = browser.main_tab
    
    stealth = StealthUtils(tab)
    human = Humanizer(tab)

    # 1. Identity Sync
    metadata = await stealth.fetch_proxy_metadata(proxy_url)
    await stealth.sync_identity(metadata)
    
    # 2. Device Spoofing
    await stealth.spoof_devices()

    # 4. Cookie Management (Session Warmth) - Import BEFORE navigation
    cookie_file = "cookies.json"
    if os.path.exists(cookie_file):
        import json
        try:
            with open(cookie_file, "r") as f:
                content = f.read().strip()
                saved = json.loads(content) if content else []
        except (json.JSONDecodeError, ValueError):
            print("Warning: cookies.json is invalid, starting fresh.")
            saved = []
        if saved:
            for c in saved:
                try:
                    await tab.send(zd.cdp.network.set_cookie(
                        name=c["name"],
                        value=c["value"],
                        domain=c.get("domain"),
                        path=c.get("path", "/"),
                        secure=c.get("secure", False),
                        http_only=c.get("httpOnly", False),
                    ))
                except Exception:
                    pass
            print("Cookies imported successfully.")

    # 3. Navigate
    page = await browser.get(url)
    
    # Wait for page to fully load
    await page.wait_for("body")

    # Periodically save cookies every 15s for 1 hour
    # This captures cf_clearance and other challenge cookies whenever you solve them via VNC
    import json

    async def save_cookies():
        try:
            raw = await page.send(zd.cdp.network.get_cookies())
            clist = [{
                "name": c.name, "value": c.value, "domain": c.domain,
                "path": c.path, "secure": c.secure, "httpOnly": c.http_only,
                "sameSite": str(c.same_site) if c.same_site else None,
            } for c in raw]
            with open(cookie_file, "w") as f:
                json.dump(clist, f, indent=4)
            has_cf = any(c["name"] == "cf_clearance" for c in clist)
            print(f"Cookies saved: {len(clist)} total {'✅ (cf_clearance present!)' if has_cf else '⏳ (waiting for challenge solve...)'}")
            return has_cf
        except Exception as e:
            print(f"Browser disconnected ({type(e).__name__}). Final cookies saved to {cookie_file}.")
            return None  # Signal to stop the loop

    # Save every 15 seconds for up to 1 hour
    for _ in range(240):
        result = await save_cookies()
        if result is None:
            break  # Chrome crashed/closed — exit cleanly
        if result:
            print("Challenge solved! Cookies are ready for next run.")
        await asyncio.sleep(15)

if __name__ == "__main__":
    proxy = os.getenv("SOCKS5_PROXY")
    target_url = "https://www.scrapingcourse.com/antibot-challenge"
    asyncio.run(run_ghost_browser(target_url, proxy))
