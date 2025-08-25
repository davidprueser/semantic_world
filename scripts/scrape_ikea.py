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
        products.append(full_url)

    return products

def get_product_id_from_url(url):
    match = re.search(r"(\d{8})", url)
    return match.group(1) if match else None

def scrape_product_page(page, full_url, writer, context, parent_name=None, parent_url=None):
    print(f"Processing {full_url}...")
    glb_url_container = {"url": None}

    def on_request(req):
        if ".glb" in req.url or "glb_draco" in req.url:
            glb_url_container["url"] = req.url

    context.on("request", on_request)
    glb_url_container["url"] = None

    page.goto(full_url)
    page.wait_for_load_state("domcontentloaded")

    # --- Name ---
    try:
        name = page.query_selector(".pip-price-module__name-decorator").inner_text().strip()
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
    writer.writerow([name, dims_str, glb_url, full_url, parent_name or "", parent_url or ""])

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

    # --- Scrape included parts ---
    scrape_included_parts(page, writer, context, parent_name=name, parent_url=full_url)


def scrape_included_parts(page, writer, context, parent_name=None, parent_url=None):
    """Find and scrape included parts if available"""
    try:
        # Scroll to load content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)

        # Find button by text
        btn = page.query_selector("button:has-text(\"What's included\")")
        if btn:
            print("Found 'What's included' button, clicking...")

            # Bring into view & click (with JS fallback)
            page.evaluate("el => el.scrollIntoView()", btn)
            try:
                btn.click(timeout=5000)
            except:
                page.evaluate("el => el.click()", btn)

            # Wait for the list container
            page.wait_for_selector(".pip-included-products__list", timeout=5000)

            # --- Wait until number of parts stabilizes ---
            last_count = -1
            stable_count = 0
            while stable_count < 3:  # 3 consecutive checks stable (~1.5s)
                part_containers = page.query_selector_all(".pip-included-products__list .pip-included-products__container")
                count = len(part_containers)
                if count == last_count:
                    stable_count += 1
                else:
                    stable_count = 0
                last_count = count
                page.wait_for_timeout(500)

            print(f"Found {len(part_containers)} included parts")

            # Extract part URLs
            part_urls = []
            for container in part_containers:
                link = container.query_selector("a[href*='/p/']")
                if not link:
                    continue
                href = link.get_attribute("href")
                if not href:
                    continue
                full_url = href if href.startswith("http") else "https://www.ikea.com" + href
                part_urls.append(full_url)

            # Deduplicate
            part_urls = list(dict.fromkeys(part_urls))

            # Scrape each included part
            for part_url in part_urls:
                print(f" -> Subpart: {part_url}")
                scrape_product_page(page, part_url, writer, context, parent_name=parent_name, parent_url=parent_url)

    except Exception as e:
        print(f"No included parts found or failed to scrape parts: {e}")


def fetch_ikea_data(product_urls, output_csv="ikea_products.csv"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        csv_headers = ["Name", "Dimensions", "3D Model URL", "Product URL", "Parent Name", "Parent URL"]
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(csv_headers)

            limit = min(len(product_urls), 10)
            product_urls = product_urls[:limit]
            for full_url in product_urls:
                scrape_product_page(page, full_url, writer, context)

        browser.close()

def click_3d_button(page):
    try:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        page.wait_for_selector(".pip-xr-button", timeout=5000)
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
