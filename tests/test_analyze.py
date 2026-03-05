"""
test_analyze.py

This module tests the functions in analyzes.py
"""
import requests
from analyze import check_readme_exists

def test_check_readme_exists_returns_true_when_found(mocker):
    """
    Mocking call to test when a readme file exists
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mocker.patch('requests.get', return_value=mock_response)

    result = check_readme_exists("https://github.com/kreddington12/github_repo_analyzer")

    assert result == True
    requests.get.assert_called_once_with("https://api.github.com/repos/kreddington12/github_repo_analyzer/contents/README.md")

def test_check_readme_exists_returns_false_when_not_found(mocker):
    """
    Mocking call to test when a readme file does not exist
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mocker.patch('requests.get', return_value=mock_response)

    result = check_readme_exists("https://github.com/kreddington12/github_repo_analyzer")

    assert result == False
    requests.get.assert_has_calls([
        mocker.call("https://api.github.com/repos/kreddington12/github_repo_analyzer/contents/README.md"),
        mocker.call("https://api.github.com/repos/kreddington12/github_repo_analyzer/contents/README"),
        mocker.call("https://api.github.com/repos/kreddington12/github_repo_analyzer/contents/docs/README.md"),
        mocker.call("https://api.github.com/repos/kreddington12/github_repo_analyzer/contents/docs/README"),
    ])
