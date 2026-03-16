"""
test_analyze.py

This module tests the functions in analyzes.py
"""
import os
from unittest import mock

import requests
import analyze
import constants

def test_get_repo_data():
    """
    Testing get_repo_data function
    :return:
    a dictionary that includes owner and repo name
    """
    owner = "owner"
    repo_name = "repo_name"

    result = analyze.get_repo_data("https://github.com/owner/repo_name")
    assert result["owner"] == owner
    assert result["repo_name"] == repo_name

def test_get_api_url():
    """
    Testing get_api_url function
    :return:
    a url as a string to be used to make api calls (filename has not been added yet.)
    """
    api_url = "https://api.github.com/repos/owner/repo_name/contents/"
    result = analyze.get_api_url("owner", "repo_name", False)
    assert result == api_url

def test_make_request_success(mocker):
    """
    Mocking call that returns a 200 response. File requested exists.
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200

    mocker.patch('requests.get', return_value=mock_response)
    github_token = os.environ.get("GITHUB_PAT")
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json" # Recommended header for GitHub API
    }

    result = analyze.make_request(["filename1", "filename2"],
                                  "https://api.github.com/repos/owner/repo_name/contents/")

    assert result.status_code == 200
    requests.get.assert_called_once_with("https://api.github.com/repos/owner/repo_name/contents/filename1",
                                         headers=headers,
                                         timeout=(2, 5))

def test_make_request_timeout(mocker):
    """
    Mocking call to test when the call times out
    """
    mocker.patch('requests.get', side_effect=requests.exceptions.Timeout)
    github_token = os.environ.get("GITHUB_PAT")
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json" # Recommended header for GitHub API
    }

    result = analyze.make_request(["filename"],
                                  "https://api.github.com/repos/owner/repo_name/contents/")

    assert result == constants.ERROR
    requests.get.assert_called_once_with("https://api.github.com/repos/owner/repo_name/contents/filename",
                                         headers=headers,
                                         timeout=(2,5))

def test_make_request_exception(mocker):
    """
    Mocking call to test when an exception is raised
    """
    mocker.patch('requests.get', side_effect=requests.exceptions.RequestException)
    github_token = os.environ.get("GITHUB_PAT")
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json" # Recommended header for GitHub API
    }

    result = analyze.make_request(["filename"], "https://api.github.com/repos/owner/repo_name/contents/")

    assert result == constants.ERROR
    requests.get.assert_called_once_with("https://api.github.com/repos/owner/repo_name/contents/filename",
                                         headers=headers,
                                         timeout=(2,5))

def test_check_readme_exists_returns_true_when_found(mocker):
    """
    A readme file was found
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"html_url": "https://github.com/owner/repo_name/blob/main/README.md"}
    mocker.patch('requests.get', return_value=mock_response)

    repo_data = {"owner": "owner", "repo_name": "repo_name"}
    result = analyze.check_readme_exists(repo_data)
    assert result == "https://github.com/owner/repo_name/blob/main/README.md"

def test_check_readme_exists_returns_false_when_not_found(mocker):
    """
    A readme file does not exist
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mocker.patch('requests.get', return_value=mock_response)

    repo_data = {"owner": "owner", "repo_name": "repo_name"}
    result = analyze.check_readme_exists(repo_data)
    assert result == constants.NO_FILE

def test_check_readme_exists_returns_error(mocker):
    mock_response = mocker.MagicMock()
    mock_response.status_code = 500
    mocker.patch('requests.get', return_value=mock_response)

    repo_data = {"owner": "owner", "repo_name": "repo_name"}
    result = analyze.check_readme_exists(repo_data)
    assert result == constants.ERROR