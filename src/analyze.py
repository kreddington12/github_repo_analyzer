"""
analyze.py

This module analyzes a GitHub repo to ensure it has consistent requirements.

Limitations:
1. Works only for Python code
2. Dependencies file must be located at the root directory.
"""
import re
import os
from typing import Dict, List
import requests
import constants

REQUIREMENTS_FILE = ["requirements.txt", "pyproject.toml"]

def get_repo_data(github_url: str) -> Dict[str, str]:
    """
    Pulls out the owner and repo name from the GitHub URL.
    Values are returned as INVALID if the repo URL format is invalid.
    """
    keys = ["owner", "repo_name"]
    repo_data = {key: "" for key in keys}

    github_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", github_url)
    if not github_match:
        repo_data["owner"] = constants.INVALID
        repo_data["repo_name"] = constants.INVALID
        return repo_data

    repo_data["owner"], repo_data["repo_name"] = github_match.groups()
    return repo_data

def get_api_url(owner: str, repo_name: str, search_in_repo:bool = False) -> str:
    """
    Creates a URL for the API based on the owner, repo name and search criteria
    """
    if search_in_repo:
        api_url = f"https://api.github.com/search/code?q=repo:{owner}/{repo_name}+filename:"
    else:
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/"

    return api_url

def make_request(list_of_filenames: List[str], api_url: str, request_timeout=(2, 5)) -> dict[str, object]:
    for file in list_of_filenames:
        request_url = f"{api_url}{file}"
        github_token = os.environ.get("GITHUB_PAT")
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json" # Recommended header for GitHub API
        }

        try:
            response = requests.get(request_url, headers=headers, timeout=request_timeout)
        except requests.exceptions.Timeout:
            print(constants.REQUEST_TIMEDOUT.format(request_url))
            return constants.ERROR
        except requests.exceptions.RequestException as e:
            print(constants.REQUEST_ERROR.format(e))
            return constants.ERROR
        else:
            if response.status_code == 200:
                break

    return response

def get_latest_version(package_name: str) -> str:
    """
    Check the latest version of a Python package
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        return data['info']['version']
    return ""

def check_readme_exists(repo_data: Dict[str, str]) -> str:
    """
    Checks for README file in root directory or docs directory as allowed by GitHub
    """
    readme_file_options = [
        "README.md",
        "README",
        "docs/README.md",
        "docs/README",
    ]

    api_url: str = get_api_url(repo_data["owner"], repo_data["repo_name"])

    response = make_request(readme_file_options, api_url)
    status_code = response.status_code
    if status_code == 200:
        return response.json()["html_url"]

    if status_code == 404:
        return constants.NO_FILE

    return constants.ERROR

def check_dependencies(repo_data: Dict[str, str]) -> str:
    """
    Searches for a requirements file from the root directory since we can find it here for over 80% of repos.
    If not found, conduct a search of the repo for the filename
    Check the file for any dependencies that need updating
    """
    keys = ["location", "filename", "file_contents", "dict_of_dependencies"]
    dependencies = dict.fromkeys(keys)

    github_token = os.environ.get("GITHUB_PAT")
    api_url = get_api_url(repo_data["owner"], repo_data["repo_name"])
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json" # Recommended header for GitHub API
    }


    for file in REQUIREMENTS_FILE:
        dependency_url = f"{api_url}{file}"
        try:
            response = requests.get(dependency_url, headers=headers, timeout=5)
        except requests.exceptions.Timeout:
            print(constants.REQUEST_TIMEDOUT)
        except requests.exceptions.RequestException as e:
            print(constants.REQUEST_ERROR.format(e))
        else:
            status_code = response.status_code
            if status_code == 200:
                dependencies["filename"] = file
                break

    # if not found in root directory, search throughout the repo
    if status_code in locals() and status_code == 404:
        api_url = get_api_url(repo_data["owner"], repo_data["repo_name"], True)
        for file in REQUIREMENTS_FILE:
            dependency_url = f"{api_url}{file}"
            try:
                response = requests.get(dependency_url, timeout=(2, 60))
            except requests.exceptions.Timeout:
                print(constants.REQUEST_TIMEDOUT)
            except requests.exceptions.RequestException as e:
                print(constants.REQUEST_ERROR.format(e))
            else:
                status_code = response.status_code
                if status_code == 200:
                    dependencies["filename"] = file
                    break

    if status_code:
        if status_code == 200:
            dependencies["location"] = api_url
            u_content = response.json()["content"]
            dependencies["dict_of_dependencies"] = get_list_of_dependencies(dependencies["file_contents"])
            return dependencies
        if status_code == 404:
            return constants.NO_FILE
    return constants.ERROR

def get_list_of_dependencies(requirements_file_contents) -> Dict[str, str, str]:
    """
    Given a string of file contents, creates a list of dependencies and any current version used
    Returns a dictionary with the following keys:
        1. dependency
        2. current version
        3. placeholder for latest version
    """
    keys = ["dependency", "current_version", "latest_version"]
    dict_of_dependencies = dict.fromkeys(keys)
    return dict_of_dependencies

def analyze_dependencies(dependencies: Dict[str, str]) -> List[str]:
    """
    Collect a list of dependencies that should be updated.
    """

    return "dependencies analyzed"

def final_report(repo: str, readme_file: str, dependencies: Dict[str, str]) -> str:
    """
    Creates a report of a GitHub repo.
    """
    report = "\n\n" + constants.ANALYSIS_REPORT_HEADER + "\n"
    report += constants.REPO_ANALYZED.format(repo) + "\n\n"

    # README file
    report += "1.  "
    if readme_file == constants.NO_FILE:
        report += constants.NO_README_FILE

    elif readme_file == constants.ERROR:
        report += constants.README_FILE_RETRIEVAL_ERROR
    else:
        report += constants.README_FILE_FOUND.format(readme_file)

    report += "\n\n"

    # Dependencies
    if dependencies == constants.NO_FILE:
        report += constants.NO_REQUIREMENTS_FILE
    elif readme_file == constants.ERROR:
        report += constants.REQUIREMENTS_FILE_RETRIEVAL_ERROR
    else:
        report +=  constants.REQUIREMENTS_FILE_FOUND.format(dependencies["dependency_location"])

    report += "\n\n"

    report += constants.END_OF_REPORT
    return report


