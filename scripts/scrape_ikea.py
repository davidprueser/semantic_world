import re
import csv
import os
import urllib.parse
import requests
from playwright.sync_api import sync_playwright

CATEGORY_URL = "https://www.ikea.com/de/en/cat/desks-computer-desks-20649/"

def get_product_urls(page, category_url):
    page.goto(category_url)
    page.wait_for_selector("a[href*='/p/']")
    product_links = list({a.get_attribute("href") for a in page.query_selector_all("a[href*='/p/']")})
    print(f"Found {len(product_links)} desks")

    products = []
    for link in product_links:
        full_url = link if link.startswith("http") else "https://www.ikea.com" + link
        print(f"Scraping {full_url}...")
        products.append(full_url)

    return products

def get_product_id_from_url(url):
    match = re.search(r"(\d{8})", url)
    return match.group(1) if match else None

def fetch_ikea_data(product_urls, output_csv="ikea_products.csv"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        csv_headers = ["Name", "Dimensions", "3D Model URL", "Product URL"]
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(csv_headers)

            glb_url_container = {"url": None}

            def on_request(req):
                if ".glb" in req.url or "glb_draco" in req.url:
                    glb_url_container["url"] = req.url

            context.on("request", on_request)

            for full_url in product_urls:
                print(f"Processing {full_url}...")
                glb_url_container["url"] = None

                page.goto(full_url)
                page.wait_for_load_state("domcontentloaded")

                # --- Name ---
                try:
                    name = page.query_selector(
                        ".pip-price-module__name-decorator"
                    ).inner_text().strip()
                except:
                    name = "unknown"

                # --- Dimensions ---
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

                dims_str = ", ".join(f"{k}: {v}" for k, v in dims.items())

                # --- Click 3D button if exists ---
                if click_3d_button(page):
                    # Wait for GLB request
                    try:
                        req = page.wait_for_event(
                            "request",
                            lambda r: (".glb" in r.url or "glb_draco" in r.url),
                            timeout=10000
                        )
                        glb_url_container["url"] = req.url
                    except:
                        pass

                glb_url = glb_url_container["url"]

                # --- Image ---
                img_url = None
                try:
                    img = page.query_selector("picture img")
                    if img:
                        src = img.get_attribute("src")
                        if src:
                            img_url = urllib.parse.urljoin(full_url, src)
                except:
                    pass

                # Save CSV row
                writer.writerow([name, dims_str, glb_url, full_url])

                # --- Download files ---
                product_id = get_product_id_from_url(full_url)
                safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
                if product_id:
                    safe_name = f"{safe_name}_{product_id}"
                os.makedirs("ikea_downloads", exist_ok=True)

                if glb_url:
                    try:
                        r = requests.get(glb_url, timeout=20)
                        with open(f"ikea_downloads/{safe_name}.glb", "wb") as f_glb:
                            f_glb.write(r.content)
                    except Exception as e:
                        print(f"Failed to download GLB for {name}: {e}")

        browser.close()
        
def click_3d_button(page):
    try:
        # Scroll to bottom to trigger lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)

        # Wait up to 10s for the button to appear
        page.wait_for_selector(".pip-xr-button", timeout=10000)
        btn = page.query_selector(".pip-xr-button")

        if btn and btn.is_enabled():
            btn.click()
            return True
    except:
        pass
    return False



if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        product_links = get_product_urls(page, CATEGORY_URL)
        browser.close()

    print(f"Found {len(product_links)} product links.")
    fetch_ikea_data(product_links)
