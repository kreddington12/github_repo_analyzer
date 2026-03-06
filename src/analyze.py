"""
analyze.py

This module analyzes a GitHub repo to ensure it has consistent requirements.

Limitations:
1. Works only for Python code
2. Dependencies file must be located at the root directory.
"""
import sys
import re
import requests

NO_FILE = "no file found"
ERROR = "error"
INVALID = "invalid url"

def get_api_url(github_url, search_in_repo=False):
    """
    Creates a URL for the API from the GitHub URL
    """
    github_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", github_url)
    if not github_match:
        print("Invalid repo URL format.")
        return False

    owner, repo_name = github_match.groups()

    if search_in_repo:
        api_url = f"https://api.github.com/search/code?q=repo:{owner}/{repo_name}+filename:"
    else:
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/"

    return api_url

def get_latest_version(package_name):
    """
    Check the latest version of a Python package
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        return data['info']['version']
    return None

def check_readme_exists(github_url):
    """
    Checks for README file in root directory or docs directory as allowed by GitHub
    """
    readme_file_options = [
        "README.md",
        "README",
        "docs/README.md",
        "docs/README",
    ]

    api_url = get_api_url(github_url)
    if not api_url:
        return INVALID

    for readme_file in readme_file_options:
        readme_url = f"{api_url}{readme_file}"
        try:
            response = requests.get(readme_url, timeout=5)
        except requests.exceptions.Timeout:
            print("The request timed out")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        else:
            status_code = response.status_code
            if status_code == 200:
                return response.json()["html_url"]

    if status_code == 404:
        return NO_FILE

    return ERROR

def check_dependencies(github_url):
    """
    Searches for a requirements file from the root directory since we can find it here for over 80% of repos.
    If not found, conduct a search of the repo for the filename
    Check the file for any dependencies that need updating
    """
    requirements_file = ["requirements.txt"]

    api_url = get_api_url(github_url)

    for file in requirements_file:
        dependency_url = f"{api_url}{file}"
        try:
            response = requests.get(dependency_url, timeout=5)
        except requests.exceptions.Timeout:
            print("The request timed out")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
        else:
            status_code = response.status_code
            if status_code == 200:
                u_content = response.json()["content"]
                break

    # if not found in root directory, search throughout the repo
    if status_code in locals() and status_code == 404:
        api_url = get_api_url(github_url, True)
        for file in requirements_file:
            dependency_url = f"{api_url}{file}"
            try:
                response = requests.get(dependency_url, timeout=(2, 60))
            except requests.exceptions.Timeout:
                print("The request timed out")
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
            else:
                status_code = response.status_code
                if status_code == 200:
                    u_content = response.json()["content"]
                    break

    if status_code:
        if status_code == 200:
            return analyze_dependencies()
        if status_code == 404:
            return NO_FILE
    return ERROR

def analyze_dependencies():
    """
    Collect a list of dependencies that should be updated.
    """
    return "dependencies analyzed"

def final_report(repo, readme_file, dependencies):
    """
    Creates a report of a GitHub repo.
    """
    report = f"****** GitHub Repo Analysis Report *******\n"
    report += f"The following repo has been analyzed:\n{repo}\n\n"

    if readme_file == NO_FILE:
        report += f"No readme file was found"
    elif readme_file == ERROR:
        report += f"There was an error trying to retrieve a readme file. No analysis was completed on the readme."
    else:
        report += f"A readme file was found at this location: {readme_file}"

    report += "\n\n"
    if dependencies == NO_FILE:
        report += f"No requirements file was found"
    elif readme_file == ERROR:
        report += f"There was an error trying to retrieve a requirements file. No analysis was completed on the dependencies."
    else:
        report += "dependencies analyzed"

    report += "\n\n"
    report += f"****** End of Analysis Report *******\n"
    return report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Repo URL is missing. Retry by adding the Repo URL as an argument.")
        sys.exit(1)
    repo_url = sys.argv[1]
    print(f"Checking {repo_url}")

    readme_file_exists= check_readme_exists(repo_url)
    if readme_file_exists == INVALID:
        print(f"Invalid repo URL format")
        sys.exit(1)

    print(final_report(repo_url, readme_file_exists, check_dependencies(repo_url)))
