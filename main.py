import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag
from datetime import datetime
from urllib.parse import urlparse

# --- SETTINGS ---
# Define headers to mimic a browser request, which can help avoid blocking.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def get_site_name_from_soup(soup):
    """
    Finds the site's domain name from the first relevant link on the report page.
    This is used for generating a dynamic output filename.
    """
    sample_list = soup.find("ul", class_="sample-list")
    if sample_list:
        first_link = sample_list.find("a", class_="sample_link")
        if first_link and first_link.has_attr('href'):
            href = first_link['href']
            parsed_url = urlparse(href)
            return parsed_url.netloc.replace('.', '-')
    return "unknown-site"


def main():
    """
    The main function that orchestrates the entire scraping and CSV generation process.
    """

    target_url = input("Please paste the report URL and press Enter: ")
    if not target_url:
        print("URL not provided. Exiting.")
        return

    print(f"\n🚀 Starting process for page: {target_url}")

    try:
        response = requests.get(target_url, headers=HEADERS)
        response.raise_for_status()
        print("✅ Page loaded successfully.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to load the page: {e}")
        return

    soup = BeautifulSoup(response.text, "lxml")

    site_name = get_site_name_from_soup(soup)
    today_date = datetime.now().strftime("%Y%m%d")
    output_csv_file = f"{today_date}-{site_name}.csv"
    print(f"📄 The output file will be named: {output_csv_file}")

    issues_section = soup.find("section", id="issues")
    if not issues_section:
        print("❌ Could not find the main issues container (<section id=\"issues\">).")
        return

    all_issues_data = []
    is_category_present_in_report = False  # Flag to track if the "Category" column should be created

    issue_articles = issues_section.find_all("article", class_="issue")
    print(f"🔍 Found {len(issue_articles)} <article> blocks to analyze.\n---")

    for article in issue_articles:
        page_title_element = article.find("h2", class_="issue-title")
        if not page_title_element:
            continue
        page_title = page_title_element.text.strip()

        issue_titles_h3 = article.find_all("h3")

        if not issue_titles_h3:
            print(f"📄 Section '{page_title}': No issues found.")
            continue

        print(f"📄 Section '{page_title}': Found {len(issue_titles_h3)} issues. Processing...")

        for h3_element in issue_titles_h3:
            issue_title = h3_element.text.strip()

            issue_category = ""
            screenshot_url = "not found"
            description_parts = []
            solution_parts = []
            is_collecting_solution = False

            # --- NEW LOGIC: Check for "Categorie" ---
            # Find the first paragraph right after the h3
            first_sibling = h3_element.find_next_sibling()
            if first_sibling and first_sibling.name == 'p' and first_sibling.text.strip().startswith("Categorie:"):
                # Extract category text, e.g., "Content/Techniek"
                category_text = first_sibling.text.strip().replace("Categorie: ", "")
                issue_category = category_text
                is_category_present_in_report = True  # Set the global flag

                # Start collecting siblings AFTER the category paragraph
                start_node = first_sibling
            else:
                # Start collecting siblings right after the h3
                start_node = h3_element
            # --- END OF NEW LOGIC ---

            for sibling in start_node.find_next_siblings():
                if sibling.name == "h3":
                    break
                if not isinstance(sibling, Tag):
                    continue

                if sibling.name == "figure" and sibling.find("img"):
                    img_tag = sibling.find("img")
                    if img_tag and 'src' in img_tag.attrs:
                        screenshot_url = requests.compat.urljoin(target_url, img_tag['src'])

                if sibling.name == "h4":
                    is_collecting_solution = True
                    solution_parts.append(sibling.text.strip())
                    continue

                if sibling.name == "p" and sibling.text.strip():
                    if is_collecting_solution:
                        solution_parts.append(sibling.text.strip())
                    else:
                        description_parts.append(sibling.text.strip())

            full_description = "\n".join(description_parts)
            full_solution = "\n".join(solution_parts)

            # Always add the category, even if it's empty. We'll remove it later if not needed.
            all_issues_data.append({
                "Page Title": page_title,
                "Issue Title": issue_title,
                "Screenshot URL": screenshot_url,
                "Description": full_description,
                "Solution": full_solution,
                "Category": issue_category
            })

    print("---\n")
    if all_issues_data:
        # --- NEW LOGIC: Conditionally remove the category column ---
        if not is_category_present_in_report:
            print("ℹ️ 'Categorie' text not found in any issue. The 'Category' column will not be created.")
            for item in all_issues_data:
                del item['Category']
        # --- END OF NEW LOGIC ---

        df = pd.DataFrame(all_issues_data)
        print(f"📊 Creating CSV from {len(df)} found issues.")
        df.to_csv(output_csv_file, index=False, sep=";", encoding="utf-8-sig")
        print(f"✅ Done! Data saved to: {output_csv_file}")
    else:
        print("⚠️ No issues were found to save to the file.")


if __name__ == "__main__":
    main()