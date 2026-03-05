"""
analyze.py

This module analyzes a GitHub repo to ensure it has consistent requirements
"""
import sys
import re
import requests

def check_readme_exists(github_url):
    """
    Checks for README file in root directory or docs directory as allowed by GitHub
    """
    github_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", github_url)
    if not github_match:
        print("Invalid repo URL format.")
        return False

    owner, repo_name = github_match.groups()

    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/"

    readme_file_options = [
        "README.md",
        "README",
        "docs/README.md",
        "docs/README",
    ]

    for readme_file in readme_file_options:
        readme_url = f"{api_url}{readme_file}"
        try:
            response = requests.get(readme_url, timeout=(5))
        except requests.exceptions.Timeout:
            print("The request timed out")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")

        status_code = response.status_code
        if status_code == 200:
            print(f"Status 200: Found a readme file at {readme_url}")
            return True

    if status_code == 404:
        print(f"Status 404: no readme file found")
        return False

    print(f"Status {response.status_code}: Error found")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Repo URL is missing. Retry by adding the Repo URL as an argument.")
        sys.exit(1)
    repo_url = sys.argv[1]
    print(f"Checking {repo_url}")
    exists = check_readme_exists(repo_url)
    print(f"Result: {exists}\n")
