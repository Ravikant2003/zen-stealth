from stealth_browser_controller import StealthBrowserController
import os

class VisualFailSafe:
    def __init__(self, browser_name="zen-browser"):
        self.controller = StealthBrowserController(browser=browser_name)

    def perform_visual_fallback(self, target_image_path):
        """Performs a visual click if CDP-based interaction fails."""
        if not os.path.exists(target_image_path):
            print(f"Error: Target image {target_image_path} not found.")
            return False
        
        try:
            # stealth-browser-controller uses OpenCV for image matching
            return self.controller.click_element_by_image(target_image_path)
        except Exception as e:
            print(f"Visual interaction failed: {e}")
            return False
