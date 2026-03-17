"""
analyze.py

This module analyzes a GitHub repo to ensure it has consistent requirements.

Limitations:
1. Works only for Python code
2. Dependencies file must be located at the root directory.
"""
import re
import os
import base64
import json
import requests
from packaging import version
from packaging.version import InvalidVersion

import constants

REQUIREMENTS_FILE = ["requirements.txt", "pyproject.toml"]

def get_repo_data(github_url: str) -> dict[str, str]:
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

def make_request(list_of_filenames: list[str], api_url: str, request_timeout=(3, 10)) -> dict[str, object]:
    """
    :param list_of_filenames: files to search for
    :param api_url: API to call
    :param request_timeout: how long to wait until requests.get times out
    :return: Exceptions return as an ERROR, otherwise, response from API call is returned regardless of status code.

    IMPORTANT: Status codes of 200 and 404 should be handled by calling method and not generalized here.
    All other status codes are returned as ERROR
    """
    if len(list_of_filenames) == 0:
        print(constants.FILE_NAME_MISSING)
        return None

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
            return None
        except requests.exceptions.RequestException as e:
            print(constants.REQUEST_ERROR.format(e))
            return None
        else:
            if response.status_code == 200:
                data = json.loads(response.text)
                if "total_count" in data and data["total_count"] == 0:
                    # GitHub shut down the request due to their 30-second time out limit.
                    print(constants.REQUEST_TIMEDOUT.format(request_url))
                    return None
                else:
                    # file found; break out of for loop
                    return response

    if response.status_code == 404:
        return response
    return None

def get_latest_version(package_name: str) -> str:
    """
    Fetches the latest version of the specified package from the PyPi API
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        latest_version = response.json()['info']['version']
    except requests.exceptions.HTTPError:
        return None
    except requests.exceptions.RequestException as e:
        print(f"While fetching data for {package_name}, " + constants.REQUEST_ERROR.format(e))
        return None

    return latest_version

def check_readme_exists(repo_data: dict[str, str]) -> str:
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
    if response:
        status_code = response.status_code
        if status_code == 200:
            return response.json()["html_url"]

        if status_code == 404:
            return constants.NO_FILE

    return constants.ERROR

def decode_content_from_base64(content_base64: str) -> str:
    return base64.b64decode(content_base64).decode("utf-8")

def get_list_of_outdated_dependencies(requirements_file_contents) -> list(str):
    """
    Given a string of file contents, creates a list of any outdated dependencies,
    along with the current version and the latest version.
    If no version is listed, or if the version is current, just continue
    """
    outdated_dependencies = []
    for line in requirements_file_contents.splitlines():
        if line.startswith("#"):
            continue
        elif "==" in line:
            package_name, current_version = line.split("==")
            latest_version = get_latest_version(package_name)
            try:
                if version.parse(latest_version) > version.parse(current_version):
                    outdated_dependencies.append(f"Package: {package_name}, Current: {current_version}, Latest: {latest_version}")
            except InvalidVersion:
                # Unable to parse values so add to the report. User can decide how to handle it
                outdated_dependencies.append(f"Package: {package_name}, Current: {current_version}, Latest: {latest_version}")
        else:
            continue
    return outdated_dependencies

def check_outdated_dependencies(repo_data: dict[str, str]) -> str:
    """
    Searches for a requirements file from the root directory since we can find it here for over 80% of repos.
    If not found, conduct a search of the repo for the filename
    Check the file for any dependencies that need updating
    """
    keys = ["location", "filename", "file_contents", "outdated_dependencies"]
    dependencies = dict.fromkeys(keys)

    api_url = get_api_url(repo_data["owner"], repo_data["repo_name"])

    response = make_request(REQUIREMENTS_FILE, api_url)

    # if not found in root directory, search throughout the repo
    if response == constants.ERROR or response == constants.NO_FILE or response.status_code == 404:
        api_url = get_api_url(repo_data["owner"], repo_data["repo_name"], True)
        response = make_request(REQUIREMENTS_FILE, api_url, (3,27))
        if not response:
            return constants.ERROR

        # if the file was still not found, return
        if response.status_code == 404:
            return constants.NO_FILE

    if response.status_code == 200:
        data = response.json()
        dependencies["location"] = data["html_url"]
        dependencies["filename"] = data["name"]
        dependencies["file_contents"] = decode_content_from_base64(data["content"])
        dependencies["outdated_dependencies"] = get_list_of_outdated_dependencies(dependencies["file_contents"])
        return dependencies

    return constants.ERROR

def final_report(repo: str, readme_file: str, dependencies: list(str)) -> str:
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
    report += "2.  "
    if dependencies == constants.NO_FILE:
        report += constants.NO_REQUIREMENTS_FILE
    elif dependencies == constants.ERROR:
        report += constants.REQUIREMENTS_FILE_RETRIEVAL_ERROR
    else:
        report += constants.REQUIREMENTS_FILE_FOUND.format(dependencies["location"]) + "\n\n"
        report += constants.REQUIREMENTS_NEED_UPDATING
        for package in dependencies["outdated_dependencies"]:
            report += "\n" + package

    report += "\n\n"

    report += constants.END_OF_REPORT
    return report


