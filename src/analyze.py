import sys

import requests
import re

# Checks for README.md file in root directory
def check_readme_exists(github_url):
    github_match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", github_url)
    if not github_match:
        print("Invalid repo URL format.")
        return False

    owner, repo_name = github_match.groups()

    api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/README.md"

    response = requests.get(api_url)
    if response.status_code == 200:
        print(f"Status 200: Found README.md: {github_url}")
        return True
    elif response.status_code == 404:
        print(f"Status 404: README.md not found")
        return False
    else:
        print(f"Status {response.status_code}: Error found")
        return False
if len(sys.argv) < 2:
    print(f"Repo URL is missing. Retry by adding the Repo URL as an argument.")
    sys.exit(1)
repo_url = sys.argv[1]
print(f"Checking {repo_url}")
exists = check_readme_exists(repo_url)
print(f"Result: {exists}\n")
