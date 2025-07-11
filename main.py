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

    Args:
        soup (BeautifulSoup): The parsed HTML of the report page.

    Returns:
        str: The extracted domain name (e.g., "example-com") or "unknown-site" if not found.
    """
    sample_list = soup.find("ul", class_="sample-list")
    if sample_list:
        first_link = sample_list.find("a", class_="sample_link")
        if first_link and first_link.has_attr('href'):
            # Parse the URL to extract the network location (domain)
            href = first_link['href']
            parsed_url = urlparse(href)
            # Replace dots with hyphens for a cleaner filename
            return parsed_url.netloc.replace('.', '-')
    return "unknown-site"


def main():
    """
    The main function that orchestrates the entire scraping and CSV generation process.
    """

    # --- Step 1: Get user input for the target URL ---
    target_url = input("Please paste the report URL and press Enter: ")
    if not target_url:
        print("URL not provided. Exiting.")
        return
    # --- End of Step 1 ---

    print(f"\n🚀 Starting process for page: {target_url}")

    try:
        response = requests.get(target_url, headers=HEADERS)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        print("✅ Page loaded successfully.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to load the page: {e}")
        return

    soup = BeautifulSoup(response.text, "lxml")

    # --- Step 2: Generate dynamic output filename ---
    site_name = get_site_name_from_soup(soup)
    today_date = datetime.now().strftime("%Y%m%d")
    output_csv_file = f"{today_date}-{site_name}.csv"
    print(f"📄 The output file will be named: {output_csv_file}")
    # --- End of Step 2 ---

    issues_section = soup.find("section", id="issues")
    if not issues_section:
        print("❌ Could not find the main issues container (<section id=\"issues\">).")
        return

    all_issues_data = []

    # Find all <article> blocks, each representing a page or a section of the report.
    issue_articles = issues_section.find_all("article", class_="issue")
    print(f"🔍 Found {len(issue_articles)} <article> blocks to analyze.\n---")

    # --- Step 3: Iterate through each article block to find issues ---
    for article in issue_articles:
        # Find the h2 title inside the article, which represents the page name.
        page_title_element = article.find("h2", class_="issue-title")
        if not page_title_element:
            continue  # Skip articles that don't have a title.
        page_title = page_title_element.text.strip()

        # Find all h3 tags, as each h3 represents a single accessibility issue.
        issue_titles_h3 = article.find_all("h3")

        # If no h3 tags are found, log it and skip to the next article.
        if not issue_titles_h3:
            print(f"📄 Section '{page_title}': No issues found.")
            continue

        print(f"📄 Section '{page_title}': Found {len(issue_titles_h3)} issues. Processing...")

        # --- Step 4: Process each individual issue (h3) ---
        for h3_element in issue_titles_h3:
            issue_title = h3_element.text.strip()

            # Initialize variables for the data to be collected.
            screenshot_url = "not found"
            description_parts = []
            solution_parts = []
            is_collecting_solution = False

            # Iterate through all sibling elements that come after the h3 tag.
            for sibling in h3_element.find_next_siblings():
                # Stop when the next h3 is found, as it marks the beginning of the next issue.
                if sibling.name == "h3":
                    break
                # Ignore non-tag elements like whitespace.
                if not isinstance(sibling, Tag):
                    continue

                # Find the screenshot URL.
                if sibling.name == "figure" and sibling.find("img"):
                    img_tag = sibling.find("img")
                    if img_tag and 'src' in img_tag.attrs:
                        screenshot_url = requests.compat.urljoin(target_url, img_tag['src'])

                # The h4 tag marks the beginning of the solution text.
                if sibling.name == "h4":
                    is_collecting_solution = True
                    solution_parts.append(sibling.text.strip())
                    continue

                # Collect paragraphs for either the description or the solution.
                if sibling.name == "p" and sibling.text.strip():
                    if is_collecting_solution:
                        solution_parts.append(sibling.text.strip())
                    else:
                        description_parts.append(sibling.text.strip())

            # Join the collected parts into final strings.
            full_description = "\n".join(description_parts)
            full_solution = "\n".join(solution_parts)

            # Append the structured data for this issue to the main list.
            all_issues_data.append({
                "Page Title": page_title,
                "Issue Title": issue_title,
                "Screenshot URL": screenshot_url,
                "Description": full_description,
                "Solution": full_solution
            })
    # --- End of main loop ---

    print("---\n")
    # --- Step 5: Save the collected data to a CSV file ---
    if all_issues_data:
        df = pd.DataFrame(all_issues_data)
        print(f"📊 Creating CSV from {len(df)} found issues.")
        df.to_csv(output_csv_file, index=False, sep=";", encoding="utf-8-sig")
        print(f"✅ Done! Data saved to: {output_csv_file}")
    else:
        print("⚠️ No issues were found to save to the file.")
    # --- End of script ---


if __name__ == "__main__":
    main()