"""
test_analyze.py

This module tests the functions in analyzes.py
"""
import os
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
                                         timeout=(3, 10))

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

    assert result is None
    requests.get.assert_called_once_with("https://api.github.com/repos/owner/repo_name/contents/filename",
                                         headers=headers,
                                         timeout=(3, 10))

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

    assert result is None
    requests.get.assert_called_once_with("https://api.github.com/repos/owner/repo_name/contents/filename",
                                         headers=headers,
                                         timeout=(3, 10))

def test_check_readme_exists_returns_success(mocker):
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

def test_check_readme_exists_returns_no_file_found(mocker):
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
    """
    Returns constants.ERROR when an error is received from the API call
    """
    mocker.patch('requests.get', return_value=None)

    repo_data = {"owner": "owner", "repo_name": "repo_name"}
    result = analyze.check_readme_exists(repo_data)
    assert result == constants.ERROR

def test_get_latest_version_package_success(mocker):
    """
    Calls the pypi API to get the latest version of a package
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"info": {"version": "3.0.1"}}
    mocker.patch('requests.get', return_value=mock_response)

    result = analyze.get_latest_version("pandas")
    assert result == "3.0.1"

def test_get_latest_version_package_not_found(mocker):
    """
    Calls the pypi API to get the latest version of a package
    """
    mocker.patch('requests.get', side_effect = requests.exceptions.HTTPError)

    result = analyze.get_latest_version("not_there")
    assert result is None

def test_get_list_of_outdated_dependencies(mocker):
    """
    Testing returned list of strings for each package
    """
    content = "# This is a comment\nnumpy==2.2.2\n# This is a comment\npandas==2.2.3"
    mocker.patch('analyze.get_latest_version', return_value="3.0.0")

    result = analyze.get_list_of_outdated_dependencies(content)
    assert result == ["Package: numpy, Current: 2.2.2, Latest: 3.0.0",
                      "Package: pandas, Current: 2.2.3, Latest: 3.0.0"]

def test_check_outdated_dependencies_returns_success(mocker):
    """
    A requirements file was found and a list of outdated dependencies has been created
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"html_url": "https://github.com/owner/repo_name/blob/main/filename",
                                       "name": "requirements.txt",
                                       "content": "YXN0cm9pZD09Mi40LjIKYXR0"}
    mocker.patch('requests.get', return_value=mock_response)

    content = "# This is a comment\nnumpy==2.2.2\n# This is a comment\npandas==2.2.3"
    mocker.patch('analyze.decode_content_from_base64', return_value=content)

    outdated_dependencies = ["Package: numpy, Current: 1.0.0, Latest: 2.0.0"]
    mocker.patch('analyze.get_list_of_outdated_dependencies', return_value=outdated_dependencies)

    repo_data = {"owner": "owner", "repo_name": "repo_name"}
    dependencies = {'location': 'https://github.com/owner/repo_name/blob/main/filename',
                    'filename': 'requirements.txt',
                    'file_contents': '# This is a comment\nnumpy==2.2.2\n# This is a comment\npandas==2.2.3',
                    'outdated_dependencies': ['Package: numpy, Current: 1.0.0, Latest: 2.0.0']}

    result = analyze.check_outdated_dependencies(repo_data)
    assert result == dependencies

def test_check_outdated_dependencies_returns_no_file_found(mocker):
    """
    No requirements file was found.
    """
    mock_response = mocker.MagicMock()
    mock_response.status_code = 404
    mocker.patch('requests.get', return_value=mock_response)

    repo_data = {"owner": "owner", "repo_name": "repo_name"}
    result = analyze.check_outdated_dependencies(repo_data)
    assert result == constants.NO_FILE

def test_check_outdated_dependencies_returns_error(mocker):
    """
    Returns constants.ERROR when an error is received from the API call
    """
    mocker.patch('requests.get', return_value=None)
    repo_data = {"owner": "owner", "repo_name": "repo_name"}
    result = analyze.check_outdated_dependencies(repo_data)
    assert result == constants.ERROR

def test_final_report_no_readme_no_requirements():
    """
    Tests that the report reflects when files were not found
    """
    result = analyze.final_report("https://github.com/owner/repo", constants.NO_FILE, constants.NO_FILE)
    assert constants.NO_README_FILE in result
    assert constants.NO_REQUIREMENTS_FILE in result

def test_final_report_readme_error():
    """
    Tests that a search for a readme file properly reports there was an error
    """
    result = analyze.final_report("https://github.com/owner/repo", constants.ERROR, constants.NO_FILE)
    assert constants.README_FILE_RETRIEVAL_ERROR in result

def test_final_report_readme_found():
    """
    Tests that the report properly analyzed a successful readme file
    """
    readme_url = "https://github.com/owner/repo/blob/main/README.md"
    result = analyze.final_report("https://github.com/owner/repo", readme_url, constants.NO_FILE)
    assert readme_url in result

def test_final_report_dependencies_error():
    """
    Tests that a search for a requirements file properly reports there was an error
    """
    result = analyze.final_report("https://github.com/owner/repo", constants.ERROR, constants.ERROR)
    assert constants.REQUIREMENTS_FILE_RETRIEVAL_ERROR in result

def test_final_report_dependencies_found():
    """
    Tests that the report properly analyzed a successful requirements file and it's outdated dependencies
    """
    dependencies = {
        "location": "requirements.txt",
        "outdated_dependencies": ["Package: numpy, Current: 1.0.0, Latest: 2.0.0"]
    }
    result = analyze.final_report("https://github.com/owner/repo", "https://github.com/owner/repo/blob/main/README.md", dependencies)
    assert "requirements.txt" in result
    assert "Package: numpy, Current: 1.0.0, Latest: 2.0.0" in result
