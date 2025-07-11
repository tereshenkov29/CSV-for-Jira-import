# Accessibility Report to CSV Scraper

A Python script designed to scrape web accessibility reports from a specific format and export the identified issues into a structured CSV file. This tool automates the manual process of data extraction, making it easy to prepare issues for bulk import into project management systems like Jira or for raw data analysis.

## Features

-   **Dynamic User Input**: Prompts the user to enter the report URL and choose an export format at runtime.
-   **Multiple Export Formats**: Offers a choice between a Jira-optimized format and a comprehensive raw data export.
-   **Automatic Filename Generation**: Creates a uniquely named CSV file based on the current date, the website's domain, and the chosen export format (e.g., `20250711-example-com-jira-import.csv`).
-   **Structured Data Extraction**: Parses the HTML to extract key information for each issue, including the page title, issue title, screenshot URL, description, solution, and category.
-   **Intelligent Logging**: Provides clear, real-time feedback in the console, indicating which pages are being processed and how many issues are found.
-   **Handles Pages with No Issues**: Correctly identifies and logs pages that were scanned but had no accessibility issues, without adding them to the final CSV.

## Requirements

-   Python 3.7+

## Installation

Follow these steps to set up the project on your local machine.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/tereshenkov29/CSV-for-Jira-import.git](https://github.com/tereshenkov29/CSV-for-Jira-import.git)
    cd CSV-for-Jira-import
    ```

2.  **Create and activate a virtual environment:**
    * On Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install the required dependencies:**
    The project uses a `requirements.txt` file to manage its dependencies. Install them with pip:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Once the installation is complete, you can run the script.

1.  **Execute the script from your terminal:**
    ```bash
    python main.py
    ```

2.  **Provide the report URL:**
    The script will prompt you to provide the URL of the accessibility report you want to scrape.
    ```
    Please paste the report URL and press Enter: [your_url_here]
    ```

3.  **Choose the Export Format:**
    Next, you will be prompted to select the desired output format.
    ```
    Choose export format:
    1: Jira Import (Summary, Description, Labels, Attachments)
    2: Raw Export (Page Title, Issue Title, Screenshot URL, Description, Solution, Category)
    Enter your choice (1 or 2): 
    ```

4.  **Let it run:**
    The script will display its progress in the console and, upon completion, will save a CSV file in the project's root directory.

## Output Formats

The script can generate two types of CSV files, both using a semicolon (`;`) as the delimiter and `UTF-8` encoding.

### Option 1: Jira Import Format

This format is optimized for direct bulk import into Jira, creating issues with pre-filled fields and attachments. The filename will have a `-jira-import.csv` suffix.

-   **Summary**: A concise title for the Jira ticket, formatted as `[site-name][Page Title] Issue Title`.
-   **Description**: A detailed, multi-line description formatted with Jira's markup, including the issue title, description, category (if present), solution, and environment details.
-   **Labels**: A static label (e.g., `Proper_Access`) for easy filtering in Jira.
-   **Attachments**: A direct URL to the screenshot, which Jira will download and attach to the ticket upon import.

### Option 2: Raw Export Format

This format provides a comprehensive dump of all data parsed from the report, suitable for analysis or custom processing. The filename will have a `-raw-export.csv` suffix.

-   **Page Title**: The name of the page or section where the issues were found (from `<h2>`).
-   **Issue Title**: The specific title of the accessibility issue (from `<h3>`).
-   **Screenshot URL**: The direct URL to the screenshot.
-   **Description**: The raw descriptive text of the issue.
-   **Solution**: The raw solution text.
-   **Category**: (Optional) This column is only created if at least one issue in the report has a category defined.