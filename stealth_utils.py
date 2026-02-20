import requests
import asyncio
import zendriver as zd

class StealthUtils:
    def __init__(self, tab):
        self.tab = tab

    async def fetch_proxy_metadata(self, proxy_url=None):
        """Fetches metadata (TZ, Locale, Geo) for the current IP."""
        try:
            response = requests.get("https://ipapi.co/json/", proxies={"http": proxy_url, "https": proxy_url} if proxy_url else None, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching metadata: {e}")
        return None

    async def sync_identity(self, metadata):
        """Programmatically set Timezone, Locale, and Geolocation via CDP."""
        if not metadata:
            return

        tz_id = metadata.get("timezone", "UTC")
        locale = metadata.get("languages", "en-US").split(",")[0]
        lat = metadata.get("latitude")
        lon = metadata.get("longitude")

        # Set Timezone
        await self.tab.send(zd.cdp.emulation.set_timezone_override(timezone_id=tz_id))
        
        # Set Locale
        await self.tab.send(zd.cdp.emulation.set_locale_override(locale=locale))

        # Set Geolocation
        if lat and lon:
            await self.tab.send(zd.cdp.emulation.set_geolocation_override(
                latitude=lat,
                longitude=lon,
                accuracy=100
            ))

    async def spoof_devices(self):
        """CDP commands to spoof media devices enumeration."""
        script = """
        (function() {
            const mockDevices = [
                {
                    deviceId: "default",
                    kind: "audioinput",
                    label: "Realtek High Definition Audio",
                    groupId: "default"
                },
                {
                    deviceId: "cam1",
                    kind: "videoinput",
                    label: "Integrated Webcam HD",
                    groupId: "camera"
                }
            ];

            Object.defineProperty(navigator.mediaDevices, 'enumerateDevices', {
                value: async () => mockDevices
            });
        })();
        """
        await self.tab.send(zd.cdp.page.add_script_to_evaluate_on_new_document(source=script))
