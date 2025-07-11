# Accessibility Report to CSV Scraper

A Python script designed to scrape web accessibility reports from a specific format and export the identified issues into a structured CSV file. This tool automates the manual process of data extraction, making it easy to prepare issues for bulk import into project management systems like Jira.

## Features

-   **Dynamic URL Input**: Prompts the user to enter the report URL at runtime.
-   **Automatic Filename Generation**: Creates a uniquely named CSV file based on the current date and the website's domain name (e.g., `20250711-example-com.csv`).
-   **Structured Data Extraction**: Parses the HTML to extract key information for each issue, including the page title, issue title, screenshot URL, description, and solution.
-   **Intelligent Logging**: Provides clear, real-time feedback in the console, indicating which pages are being processed and how many issues are found.
-   **Handles Pages with No Issues**: Correctly identifies and logs pages that were scanned but had no accessibility issues, without adding them to the final CSV.

## Requirements

-   Python 3.7+

## Installation

Follow these steps to set up the project on your local machine.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/tereshenkov29/CSV-for-Jira-import.git
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

3.  **Let it run:**
    The script will display its progress in the console and, upon completion, will save a CSV file in the project's root directory.

## Output CSV Format

The script generates a CSV file with a semicolon (`;`) as the delimiter and `UTF-8` encoding for compatibility with Excel and other tools. The file contains the following columns:

-   **Page Title**: The name of the page or section where the issues were found (extracted from the `<h2>` tag).
-   **Issue Title**: The specific title of the accessibility issue (from the `<h3>` tag).
-   **Screenshot URL**: A direct, absolute URL to the screenshot associated with the issue.
-   **Description**: A detailed description of the issue, with multiple paragraphs joined by newlines.
-   **Solution**: The recommended solution, including the heading (from `<h4>`) and subsequent paragraphs, joined by newlines.
-   **Category** (if exists in the report): The column to indicate the category of the issue - Content or Technique