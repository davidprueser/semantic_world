from playwright.sync_api import sync_playwright
import json
import re
import os
import requests
import time

CATEGORY_URL = "https://www.ikea.com/de/en/cat/desks-computer-desks-20649/"
MODEL_DIR = "models"

os.makedirs(MODEL_DIR, exist_ok=True)

def safe_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '', name)

def scrape_desks():
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Get all product links from category page
        page.goto(CATEGORY_URL)
        page.wait_for_selector("a[href*='/p/']")
        product_links = list({a.get_attribute("href") for a in page.query_selector_all("a[href*='/p/']")})
        print(f"Found {len(product_links)} desks")

        for link in product_links:
            full_url = link if link.startswith("http") else "https://www.ikea.com" + link
            print(f"Scraping {full_url}...")

            glb_url = None

            # Intercept requests
            def on_request(req):
                nonlocal glb_url
                if ".glb" in req.url or "glb_draco" in req.url:
                    glb_url = req.url
            context.on("request", on_request)

            page.goto(full_url)
            page.wait_for_load_state("domcontentloaded")

            # Get product name
            try:
                name = page.query_selector(".pip-price-module__name-decorator").inner_text().strip()
            except:
                name = "unknown"

            # Get dimensions
            dims = {}
            try:
                detail_section = page.query_selector("div#pip-product-details")
                if detail_section:
                    text = detail_section.inner_text()
                    for dim in ["Width", "Depth", "Height"]:
                        m = re.search(rf"{dim}:\s*([\d.,]+)\s*cm", text)
                        if m:
                            dims[dim] = m.group(1) + " cm"
            except:
                pass

            # Click the 3D button to trigger GLB load
            try:
                btn = page.query_selector(".pip-xr-button")
                if btn:
                    btn.click()
                    # page.wait_for_timeout(4000)  # Wait for model request
                for _ in range(30):
                    if glb_url:
                        break
                    context.on("request", on_request)
                    time.sleep(0.5)
            except:
                pass

            # Download the model
            model_path = None
            if glb_url and glb_url.startswith("http"):
                try:
                    # Extract article number from URL
                    article_match = re.search(r'/p/[^/]+-(\d{8})/', full_url)
                    article_id = article_match.group(1) if article_match else "noid"

                    filename = f"{safe_filename(name)}_{article_id}" or "ikea_product"
                    model_path = os.path.join(MODEL_DIR, filename + ".glb")
                    print(f"  Downloading model: {model_path}")
                    r = requests.get(glb_url)
                    r.raise_for_status()
                    with open(model_path, "wb") as f:
                        f.write(r.content)
                except Exception as e:
                    print(f"  Failed to download model: {e}")
            else:
                print("  No 3D model found")

            results.append({
                "name": name,
                "url": full_url,
                "dimensions": dims,
                "model_url": glb_url,
                "model_file": model_path
            })

        browser.close()

    return results


if __name__ == "__main__":
    desks = scrape_desks()
    with open("ikea_desks.json", "w", encoding="utf-8") as f:
        json.dump(desks, f, indent=2, ensure_ascii=False)
    print("Saved ikea_desks.json and models/")
