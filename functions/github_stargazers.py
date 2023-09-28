import pandas as pd
from tqdm import tqdm
from github import Github

from evadb.catalog.catalog_type import NdArrayType, ColumnType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe


class GithubStargazers(AbstractFunction):
    """
    Arguments:
        None

    Input Signatures:
        repo_url (str) : The URL of the GitHub repository to scrape stargazers from.
        github_token (str) : GitHub personal access token for authentication.

    Output Signatures:
        stargazers (str) : A list of GitHub usernames who have starred the repository.

    Example Usage:
        You can use this function to scrape stargazers of a GitHub repository as follows:

        repo_url = "https://github.com/owner/repo"
        github_token = "your_github_token" (Personal Access Token)
        cursor.function("GithubStargazersScraper", repo_url, github_token)
    """

    @property
    def name(self) -> str:
        return "GithubStargazers"

    @setup(cacheable=False, function_type="web-scraping")
    def setup(self) -> None:
        # Any setup or initialization can be done here if needed
        pass

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["repo_url", "github_token"],
                column_types=[ColumnType.TEXT, ColumnType.TEXT],
                column_shapes=[(1,), (1,), (1,)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["stargazers"],
                column_types=[NdArrayType.STR],
                column_shapes=[(None,)],
            )
        ],
    )
    def forward(self, input_df):
        # Ensure the URL is provided
        if input_df.empty or input_df.iloc[0, 0] is None:
            raise ValueError("Repository URL must be provided.")

        # Extract inputs from the DataFrame
        repo_url = input_df.iloc[0, 0]
        github_token = input_df.iloc[0, 1]

        # Initialize GitHub API client
        if github_token:
            github = Github(github_token)
        else:
            github = Github()

        try:
            # Parse the repository URL to extract owner and repo name
            parts = repo_url.strip("/").split("/")
            owner = parts[-2]
            repo_name = parts[-1]

            # Get the repository and its stargazers
            repository = github.get_repo(f"{owner}/{repo_name}")
            stargazers = []
            stargazers = [stargazer.login for stargazer in repository.get_stargazers()[:1000]]

        except Exception as e:
            print(f"Error: {str(e)}")

        df = pd.DataFrame({"github_username": stargazers})

        return df
