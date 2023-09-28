import pandas as pd
from github import Github
import time
import concurrent.futures

from evadb.catalog.catalog_type import ColumnType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe


class GithubUserDetails(AbstractFunction):
    """
    Arguments:
        None

    Input Signatures:
        github_username (str) : The GitHub username for the user whose details you want to retrieve.
        github_token (str) : GitHub personal access token for authentication.

    Output Signatures:
        user_name (str) : The name of the GitHub user.
        user_login (str) : The login (username) of the GitHub user.
        user_following (int) : The number of users the GitHub user is following.
        user_followers (int) : The number of followers the GitHub user has.
        user_email (str) : The email address of the GitHub user.
        user_id (int) : The unique ID of the GitHub user.
        user_location (str) : The location of the GitHub user.
        user_bio (str) : The bio of the GitHub user.
        user_company (str) : The company associated with the GitHub user.
        user_blog (str) : The blog URL of the GitHub user.
        user_url (str) : The URL of the GitHub user's profile.
        user_twitter_username (str) : The Twitter username of the GitHub user.
        user_repos (list) : A list of dictionaries representing the user's repositories with 10+ stars.
        user_starred (list) : A list of dictionaries representing repositories starred by the user with 10+ stars.

    Example Usage:
        You can use this function to retrieve details about a GitHub user as follows:

        github_username = "username"
        github_token = "your_personal_access_token"
        cursor.function("GithubUserDetails", github_username, github_token)
    """

    @property
    def name(self) -> str:
        return "GithubUserDetails"

    @setup(cacheable=False, function_type="web-scraping")
    def setup(self) -> None:
        # Any setup or initialization can be done here if needed
        pass

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["github_username", "github_token"],
                column_types=[ColumnType.TEXT, ColumnType.TEXT],
                column_shapes=[(1,), (1,)],
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=[
                    "user_name", "user_login", 
                    "user_following", "user_followers",
                    "user_email", 
                    "user_id", 
                    "user_location", "user_bio",
                    "user_company", "user_blog", "user_url", "user_twitter_username",
                    "user_repos", "user_starred",
                ],
                column_types=[
                    ColumnType.TEXT, ColumnType.TEXT,
                    ColumnType.INTEGER, ColumnType.INTEGER,
                    ColumnType.TEXT,
                    ColumnType.INTEGER,
                    ColumnType.TEXT, ColumnType.TEXT,
                    ColumnType.TEXT, ColumnType.TEXT, ColumnType.TEXT, ColumnType.TEXT,
                    ColumnType.TEXT,
                    ColumnType.TEXT,
                    ColumnType.TEXT
                ],
                column_shapes=[
                    (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,), (1,)
                    ],
            )
        ],
    )
    def forward(self, input_df):
        # Ensure the GitHub username is provided
        if input_df.empty or input_df.iloc[0, 0] is None:
            raise ValueError("GitHub username must be provided.")

        # Extract inputs from the DataFrame
        github_username = input_df.iloc[0, 0]
        github_token = input_df.iloc[0, 1]

        # Initialize GitHub API client
        if github_token:
            github = Github(github_token)
        else:
            github = Github()

        # Create an empty list to store user details
        user_details_list = []

        # Define a function to fetch user details for a range of rows
        def fetch_user_details_range(start_index, end_index):

            # Process a range of rows from start_index to end_index
            api_limit_error = False
            i = 0
            for index in range(start_index, end_index):
                i = i + 1

                # Avoid hitting API limit
                if i != 0 and i % 10 == 0:
                    print(f"Downloading details of user: {i}")
                    time.sleep(30)

                if api_limit_error == True:
                    api_limit_error = False
                    index = index - 1

                github_username = input_df.iloc[index]["github_username"]

                try:
                    # Retrieve the user object
                    user = github.get_user(github_username)

                    # Gather user details into separate variables
                    user_name = user.name
                    user_login = user.login
                    user_following = user.following
                    user_followers = user.followers
                    user_email = user.email
                    user_id = user.id
                    user_location = user.location
                    user_bio = user.bio
                    user_company = user.company
                    user_blog = user.blog
                    user_url = user.url
                    user_twitter_username = user.twitter_username

                    # Repos of user with 10+ stars
                    user_repos =  user.get_repos()
                    user_created_repos = []
                    for repo in user_repos:
                        if repo.fork is False:
                            if repo.stargazers_count > 10:
                                user_created_repos.append({
                                    repo.name,
                                    repo.description,
                                    repo.html_url,
                                    repo.language
                                })

                    # Repos starred by user with 10+ stars
                    starred_repos = user.get_starred()
                    user_starred_repos = []
                    j = 0
                    for repo in starred_repos:
                        j = j + 1
                        if j > 10:
                            break
                        if repo.stargazers_count > 100:
                            user_starred_repos.append({
                                repo.name,
                                repo.description,
                                repo.html_url,
                                repo.language
                            })

                    # Gather user details into a dictionary
                    user_details = {
                        "user_name": user.name,
                        "user_login": user.login,
                        "user_following": user.following,
                        "user_followers": user.followers,
                        "user_email": user.email,
                        "user_id": user.id,
                        "user_location": user.location,
                        "user_bio": user.bio,
                        "user_company": user.company,
                        "user_blog": user.blog,
                        "user_url": user.url,
                        "user_twitter_username": user.twitter_username,
                        "user_repos": f"{user_created_repos}",
                        "user_starred_repos": f"{user_starred_repos}"
                    }

                    # Append user details to the list
                    user_details_list.append(user_details)

                except Exception as e:
                    print(f"Error: {str(e)}")
                    api_limit_error = True
                    # sleep for 5 minutes
                    time.sleep(300)

        num_workers = 1
        num_rows = len(input_df)
        rows_per_worker = num_rows // num_workers

        print(f"Downloading details of {num_rows} users")

        # Create a list of tuples defining the ranges for each worker
        # Include any remaining rows in the last worker's range
        worker_ranges = [
            (i * rows_per_worker, (i + 1) * rows_per_worker) 
            for i in range(num_workers)
        ]
        worker_ranges[-1] = (worker_ranges[-1][0], num_rows)

        # Iterate over rows in the input DataFrame using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            for start_index, end_index in worker_ranges:
                executor.submit(
                    fetch_user_details_range, start_index, end_index
                )

        # Create a DataFrame from the list of user details
        user_details_df = pd.DataFrame(user_details_list)

        return user_details_df