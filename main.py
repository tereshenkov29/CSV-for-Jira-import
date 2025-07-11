import requests
import pandas as pd
from bs4 import BeautifulSoup, Tag
from datetime import datetime
from urllib.parse import urlparse
import os

# --- SETTINGS ---
# Define headers to mimic a browser request, which can help avoid blocking.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


# --- PARSER ---
def extract_raw_data(soup, target_url):
    """
    Parses the HTML soup to extract all issues into a structured list of dictionaries.
    """
    issues_section = soup.find("section", id="issues")
    if not issues_section:
        print("❌ Could not find the main issues container (<section id=\"issues\">).")
        return [], False

    all_issues_data = []
    is_category_present_in_report = False

    issue_articles = issues_section.find_all("article", class_="issue")
    print(f"🔍 Found {len(issue_articles)} <article> blocks to analyze.\n---")

    for article in issue_articles:
        page_title_element = article.find("h2", class_="issue-title")
        if not page_title_element:
            continue
        page_title = page_title_element.text.strip()

        # Extract environment info (the specific page URL) if it exists for this section.
        environment_info = None
        for p_tag in article.find_all("p"):
            if "Link naar pagina:" in p_tag.get_text():
                link_tag = p_tag.find("a")
                if link_tag and link_tag.has_attr('href'):
                    environment_info = {
                        "name": link_tag.text.strip(),
                        "url": link_tag.get('href')
                    }
                    break  # Stop searching once found

        issue_titles_h3 = article.find_all("h3")
        if not issue_titles_h3:
            print(f"📄 Section '{page_title}': No issues found.")
            continue

        print(f"📄 Section '{page_title}': Found {len(issue_titles_h3)} issues. Processing...")
        for h3_element in issue_titles_h3:
            issue_title = h3_element.text.strip()
            issue_category, screenshot_url = "", "not found"
            description_parts, solution_parts = [], []
            is_collecting_solution = False

            # Check if the first paragraph after the h3 is a category definition.
            first_sibling = h3_element.find_next_sibling()
            if first_sibling and first_sibling.name == 'p' and first_sibling.text.strip().startswith("Categorie:"):
                issue_category = first_sibling.text.strip().replace("Categorie: ", "")
                is_category_present_in_report = True
                start_node = first_sibling  # Start collecting data after the category paragraph.
            else:
                start_node = h3_element  # Start collecting data right after the issue title.

            # Iterate through all subsequent sibling elements to gather issue data.
            for sibling in start_node.find_next_siblings():
                if sibling.name == "h3":
                    break  # Stop when the next issue starts.
                if not isinstance(sibling, Tag):
                    continue

                if sibling.name == "figure" and sibling.find("img"):
                    img_tag = sibling.find("img")
                    if img_tag and 'src' in img_tag.attrs:
                        screenshot_url = requests.compat.urljoin(target_url, img_tag['src'])
                elif sibling.name == "h4":
                    is_collecting_solution = True
                    solution_parts.append(sibling.text.strip())
                elif sibling.name == "p" and sibling.text.strip():
                    if is_collecting_solution:
                        solution_parts.append(sibling.text.strip())
                    else:
                        description_parts.append(sibling.text.strip())

            all_issues_data.append({
                "Page Title": page_title,
                "Issue Title": issue_title,
                "Screenshot URL": screenshot_url,
                "Description": "\n".join(description_parts),
                "Solution": "\n".join(solution_parts),
                "Category": issue_category,
                "Environment": environment_info
            })
    return all_issues_data, is_category_present_in_report


# --- TRANSFORMERS ---
def transform_for_jira_import(raw_data, site_name):
    """
    Transforms raw data into a format optimized for Jira import.
    """
    jira_data = []
    for issue in raw_data:
        description_parts = [
            f"h3. {issue['Issue Title']}",
            issue['Description']
        ]

        if issue['Category']:
            description_parts.append(f"\n*Category:* {issue['Category']}")

        description_parts.append("\n\n---\n")

        if issue['Solution']:
            solution_lines = issue['Solution'].split('\n', 1)
            solution_header = solution_lines[0]
            description_parts.append(f"h4. {solution_header}")
            if len(solution_lines) > 1:
                description_parts.append(solution_lines[1])

        if issue['Environment']:
            env = issue['Environment']
            env_string = f"h5. Environment\n_{env['name']}_ - {env['url']}"
            description_parts.append(f"\n\n{env_string}")

        jira_data.append({
            "Summary": f"[{site_name}][{issue['Page Title']}] {issue['Issue Title']}",
            "Description": "\n".join(description_parts),
            "Labels": "Proper_Access",
            "Attachments": issue['Screenshot URL'] if issue['Screenshot URL'] != "not found" else ""
        })
    return jira_data

def transform_for_raw_export(raw_data, is_category_present):
    """
    Transforms raw data for a direct, unprocessed export.
    """
    # Remove environment data for raw export as it's not part of its spec.
    for item in raw_data:
        del item['Environment']

    # Conditionally remove the category column if it was never found.
    if not is_category_present:
        print("ℹ️ 'Categorie' text not found in any issue. The 'Category' column will not be created.")
        for item in raw_data:
            del item['Category']
    return raw_data


# --- HELPERS ---
def get_site_name_from_soup(soup):
    """
    Finds the site's domain name from the first relevant link on the report page.
    """
    sample_list = soup.find("ul", class_="sample-list")
    if sample_list:
        first_link = sample_list.find("a", class_="sample_link")
        if first_link and first_link.has_attr('href'):
            href = first_link['href']
            parsed_url = urlparse(href)
            return parsed_url.netloc
    return "unknown-site"

def get_unique_filename(base_path):
    """
    Checks if a file exists and appends a number if it does to prevent overwriting.
    Example: 'file.csv' -> 'file (2).csv'
    """
    if not os.path.exists(base_path):
        return base_path

    name, ext = os.path.splitext(base_path)
    counter = 2
    while True:
        new_path = f"{name} ({counter}){ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1

# --- MAIN ---
def main():
    """
    The main function that orchestrates the entire scraping and CSV generation process.
    """
    # Get all user inputs at the beginning.
    target_url = input("Please paste the report URL and press Enter: ")
    if not target_url:
        print("URL not provided. Exiting.")
        return

    print("\nChoose export format:")
    print("1: Jira Import (Summary, Description, Labels, Attachments)")
    print("2: Raw Export (Page Title, Issue Title, Screenshot URL, Description, Solution, Category)")
    choice = input("Enter your choice (1 or 2): ")

    if choice not in ['1', '2']:
        print("❌ Invalid choice. Exiting.")
        return

    # Start the scraping process.
    print(f"\n🚀 Starting process for page: {target_url}")
    try:
        response = requests.get(target_url, headers=HEADERS)
        response.raise_for_status()
        # Explicitly set the encoding to UTF-8 to prevent character issues.
        response.encoding = 'utf-8'
        print("✅ Page loaded successfully.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to load the page: {e}")
        return

    soup = BeautifulSoup(response.text, "lxml")

    # Extract raw data from the page.
    raw_issues, is_category_present = extract_raw_data(soup, target_url)

    if not raw_issues:
        print("⚠️ No issues were found to save to the file.")
        return

    # Transform data based on the user's choice.
    site_name = get_site_name_from_soup(soup)

    if choice == '1':
        print("\nFormatting data for Jira import...")
        processed_data = transform_for_jira_import(raw_issues, site_name)
        file_suffix = "jira-import"
    else:  # choice == '2'
        print("\nFormatting data for raw export...")
        processed_data = transform_for_raw_export(raw_issues, is_category_present)
        file_suffix = "raw-export"

    # Generate a unique filename and save the data to a CSV file.
    today_date = datetime.now().strftime("%Y%m%d")
    base_output_file = f"{today_date}-{site_name.replace('.', '-')}-{file_suffix}.csv"
    output_csv_file = get_unique_filename(base_output_file)

    print(f"📄 The output file will be named: {output_csv_file}")

    df = pd.DataFrame(processed_data)
    print(f"📊 Creating CSV from {len(df)} found issues.")
    df.to_csv(output_csv_file, index=False, sep=";", encoding="utf-8-sig")
    print(f"✅ Done! Data saved to: {output_csv_file}")


if __name__ == "__main__":
    main()