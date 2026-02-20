import asyncio
import random
import numpy as np
import zendriver as zd
from scipy.interpolate import interp1d

class Humanizer:
    def __init__(self, tab):
        self.tab = tab

    async def sleep_random(self, min_ms=200, max_ms=800):
        """Randomized pause to mimic human behavior."""
        delay = random.uniform(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)

    def _generate_bezier_path(self, start, end, steps=25):
        """Generates a cubic Bézier curve path between two points."""
        start = np.array(start)
        end = np.array(end)
        
        # Random control points for natural curve
        dist = np.linalg.norm(end - start)
        offset = dist * 0.2
        
        cp1 = start + (end - start) * 0.3 + np.random.uniform(-offset, offset, 2)
        cp2 = start + (end - start) * 0.7 + np.random.uniform(-offset, offset, 2)
        
        t = np.linspace(0, 1, steps)
        path = (1-t)**3 * start[:, None] + \
               3*(1-t)**2 * t * cp1[:, None] + \
               3*(1-t) * t**2 * cp2[:, None] + \
               t**3 * end[:, None]
        
        return path.T

    async def move_mouse(self, x, y, steps=30):
        """Move mouse along a Bézier curve to target coordinates."""
        # Note: In zendriver, we use tab.send for CDP Input.dispatchMouseEvent
        start_pos = (0, 0) # Placeholder
        path = self._generate_bezier_path(start_pos, (x, y), steps)
        
        for px, py in path:
            await self.tab.send(zd.cdp.input_.dispatch_mouse_event(
                type_="mouseMoved",
                x=float(px),
                y=float(py)
            ))
            await asyncio.sleep(random.uniform(0.005, 0.015))

    async def type_text(self, element, text):
        """Type text with human-like cadence (variable per-character delays)."""
        for char in text:
            # element.send_keys is available in zendriver (nodriver)
            await element.send_keys(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))
        
        await self.sleep_random(300, 600)

    async def click_element(self, element):
        """Move to element and click with a human-like delay."""
        # Get element coordinates
        box = await element.get_bounding_client_rect()
        center_x = box.x + box.width / 2
        center_y = box.y + box.height / 2
        
        await self.move_mouse(center_x, center_y)
        await self.sleep_random(150, 400) # Hover time
        await element.click()
        await self.sleep_random(200, 500)
