# Constants used for error checking
NO_FILE = "no file found"
ERROR = "error"
INVALID = "invalid url"

# Constants used as text displayed to the user through messages
REQUEST_TIMEDOUT = "A request to search the GitHub repo has timed out: {}"
INVALID_REPO_URL = "The format of the repo URL is invalid."
REQUEST_ERROR = "An error occurred: {}"


#Constants used in the final report

# Report Header
ANALYSIS_REPORT_HEADER = "****** GitHub Repo Analysis Report *******"
REPO_ANALYZED = "The following repo has been analyzed:\n{}"

# Readme File
NO_README_FILE = "No readme file was found.\n\n\
A README file is highly recommended as it serves as the project's primary documentation\
for users and potential contributors.\n\n"
README_FILE_RETRIEVAL_ERROR = "There was an error trying to retrieve a readme file. No analysis was completed on the readme."
README_FILE_FOUND = "A readme file was found at this location: {}"

# Dependencies
NO_REQUIREMENTS_FILE = "No requirements file was found.\n\
A requirements file is essential in Python for ensuring reproducibility, enabling yourself and others\
to recreate the exact environment required to run a project, regardless of the machine. It prevents \
version conflicts, simplifies dependency management, and facilitates seamless deployment and collaboration\
by documenting all necessary libraries and their versions.\n\n\
Your README file should have the following information:\n\
    - The name of the package, library or tool\n\
    - Badges for the packages current published version, documentation and test suite build. \
    (OPTIONAL: test coverage)\n\
    - Easy-to-understand explanation (2-4 sentences) of what your tool does\n\
    - Context for how the tool fits into the broader ecosystem\n\
    - If your library/package 'wraps' around another package, link to the package that it is wrapping \
    and any associated documentation.\n\
    - A simple quick-start code example that a user can follow to provide a demonstration of what the package can do for them\
    - Links to your package's documentation / website, if applicable.\
    - A few descriptive links to any tutorials you've created for your package."
REQUIREMENTS_FILE_RETRIEVAL_ERROR = "There was an error trying to retrieve a requirements file. No analysis was completed on the dependencies."
REQUIREMENTS_FILE_FOUND = "A requirements file was found at this location: {}"

# Report End
END_OF_REPORT = "****** End of Analysis Report *******\n"