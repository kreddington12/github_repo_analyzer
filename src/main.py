import sys
import constants
import analyze

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Repo URL is missing. Retry by adding the Repo URL as an argument.")
        sys.exit(1)
    repo_url = sys.argv[1]
    print(f"Checking {repo_url}")

    repo_data = analyze.get_repo_data(repo_url)
    if repo_data["owner"] == constants.INVALID:
        print(constants.INVALID_REPO_URL)
        sys.exit(1)

    print(analyze.final_report(
        repo_url,
        analyze.check_readme_exists(repo_data),
        analyze.check_outdated_dependencies(repo_data)
    ))