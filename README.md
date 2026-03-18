# github_repo_analyzer
A GitHub Repository Analyzer written in Python to learn Python and showcase my skills. This analyzer will check for a readme file and any outdated dependencies. A report will display the results.

Analyzer works on Python projects only.

For the analysis to work, the repository you are analyzing must be indexed on GitHub. To force an index, conduct a search for a file or keyword using the GitHub search code API.

Current Limitations:
1. Readme file must be found in the root or docs (as recommended by GitHub) directory and be named one of:
    *README.md
    *README
    *docs/README.md
    *docs/README
2. Dependencies must be found in the root directory with the filename of 'requirements.txt'

Future Feature:
1. Analyze a pyproject.toml
