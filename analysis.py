#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import pandas as pd
import evadb

pd.set_option("display.max_columns", None)  # Show all columns
pd.set_option("display.expand_frame_repr", False)
pd.set_option("display.max_colwidth", None)


if not load_dotenv():
    print(
        "Could not load .env file or it is empty. Please check if it exists and is readable."
    )
    exit(1)

# REPO DETAILS
repo_url = os.environ.get('REPO_URL')
github_pat = os.environ.get('GITHUB_API')

# Parse the repository URL to extract owner and repo name
parts = repo_url.strip("/").split("/")
repo_name = parts[-1]

DEFAULT_CSV_PATH = f"{repo_name}.csv"


if __name__ == "__main__":
    try:
        # establish evadb api cursor
        print("⏳ Connect to EvaDB...")
        cursor = evadb.connect().cursor()
        print("✅ Connected to EvaDB...")

        cursor.query(
            f"""
            CREATE OR REPLACE FUNCTION GithubStargazers
            INPUT (repo_url TEXT(1000), github_pat TEXT(1000))
            OUTPUT (github_username TEXT(1000))
            TYPE  Webscraping
            IMPL  'functions/github_stargazers.py';
        """
        ).df()

        cursor.query(
            f"""
            CREATE OR REPLACE FUNCTION WebPageTextExtractor
            INPUT (urls TEXT(1000))
            OUTPUT (extracted_text TEXT(1000))
            TYPE  Webscraping
            IMPL  'functions/webpage_text_extractor.py';
        """
        ).df()

        cursor.query(
            f"""
            CREATE OR REPLACE FUNCTION GithubUserdetails
            INPUT (github_username TEXT(1000), github_pat TEXT(1000))
            OUTPUT (
                user_name TEXT(1000),
                user_login TEXT(1000),
                user_following INTEGER,
                user_followers INTEGER,
                user_email TEXT(1000),
                user_id INTEGER,
                user_location TEXT(1000),
                user_bio TEXT(1000),
                user_company TEXT(1000),
                user_blog TEXT(1000),
                user_url TEXT(1000),
                user_twitter_username TEXT(1000),
                user_repos TEXT(1000),
                user_starred_repos TEXT(1000)
            )
            TYPE  Webscraping
            IMPL  'functions/github_user_details.py';
        """
        ).df()

        cursor.query(
            """
            CREATE OR REPLACE FUNCTION StringToDataframe
            INPUT (input_string TEXT(1000))
            OUTPUT (
                name TEXT(1000),
                country TEXT(1000),
                city TEXT(1000),
                email TEXT(1000),
                occupation TEXT(1000),
                programming_languages TEXT(1000),
                topics_of_interest TEXT(1000),
                social_media TEXT(1000)
            )
            TYPE  Webscraping
            IMPL  'functions/string_to_dataframe.py';
        """
        ).df()

        cursor.query(
            """CREATE OR REPLACE FUNCTION GPT35
                IMPL 'functions/chatgpt.py'
                MODEL 'gpt-35-turbo-16k'
            """
        ).df()

        cursor.query(
            """CREATE OR REPLACE FUNCTION GPT4
                IMPL 'functions/chatgpt_batch.py'
                MODEL 'gpt-4-32k'
            """
        ).df()

        print(
            cursor.query(
                f"""
           CREATE TABLE IF NOT EXISTS {repo_name}_StargazerList AS
           SELECT GithubStargazers("{repo_url}", "{github_pat}");
        """
            ).df()
        )

        select_query = cursor.query(
            f"SELECT * FROM {repo_name}_StargazerList;"
        ).df()

        print(select_query)

        print(
            cursor.query(
                f"""
           CREATE TABLE IF NOT EXISTS {repo_name}_StargazerDetails AS
           SELECT GithubUserdetails(github_username, "{github_pat}")
           FROM {repo_name}_StargazerList
           LIMIT 10;
        """
            ).df()
        )

        select_query = cursor.query(
            f"""
        SELECT * FROM {repo_name}_StargazerDetails;
        """
        ).df()

        print(select_query)

        print(
            cursor.query(
                f"""
           CREATE TABLE IF NOT EXISTS {repo_name}_StargazerScrapedDetails AS
           SELECT github_username, WebPageTextExtractor(github_username)
           FROM {repo_name}_StargazerList;
        """
            ).df()
        )

        select_query = cursor.query(
            f"""
                SELECT *
                FROM {repo_name}_StargazerScrapedDetails;
        """
        ).df()

        print("Processing insights...")

        LLM_prompt = """You are given a block of disorganized text extracted from the GitHub user profile of a user using an automated web scraper. The goal is to get structured results from this data.
                Extract the following fields from the text: name, country, city, email, occupation, programming_languages, topics_of_interest, social_media.
                If some field is not found, just output fieldname: N/A. Always return all the 8 field names. DO NOT add any additional text to your output.
                The topic_of_interest field must list a broad range of technical topics that are mentioned in any portion of the text.  This field is the most important, so add as much information as you can. Do not add non-technical interests.
                The programming_languages field can contain one or more programming languages out of only the following 4 programming languages - Python, C++, JavaScript, Java. Do not include any other language outside these 4 languages in the output. If the user is not interested in any of these 4 programming languages, output N/A.
                If the country is not available, use the city field to fill the country. For example, if the city is New York, fill the country as United States.
                If there are social media links, including personal websites, add them to the social media section. Do NOT add social media links that are not present.
                Here is an example (use it only for the output format, not for the content):

                name: logicx
                country: United States
                city: Atlanta
                email: abc@gatech.edu
                occupation: PhD student at Georgia Tech
                programming_languages: Python, Java
                topics_of_interest: Google Colab, fake data generation, Postgres
                social_media: https://www.logicx.io, https://www.twitter.com/logicx, https://www.linkedin.com/in/logicx
                """
        # GPT-35 fuzzy topics
        cursor.query(
            f"""
            CREATE TABLE IF NOT EXISTS {repo_name}_StargazerInsights AS
            SELECT StringToDataframe(
                GPT35("{LLM_prompt}", extracted_text
                )
            )
            FROM {repo_name}_StargazerScrapedDetails;
        """
        ).df()

        select_query = cursor.query(
            f"""
                SELECT *
                FROM {repo_name}_StargazerInsights;
        """
        ).df()

        print(select_query)

        LLM_prompt = """You are given 10 rows of input, each row is separated by two new line characters.
                     Categorize the topics listed in each row into one or more of the following 3 technical areas - Machine Learning, Databases, and Web development. If the topics listed are not related to any of these 3 areas, output a single N/A. Do not miss any input row. Do not add any additional text or numbers to your output.
                     The output rows must be separated by two new line characters. Each input row must generate exactly one output row. For example, the input row [Recommendation systems, Deep neural networks, Postgres] must generate only the output row [Machine Learning, Databases].
                     The input row [enterpreneurship, startups, venture capital] must generate the output row N/A.
                     """

        cursor.query(
            f"""CREATE TABLE IF NOT EXISTS
                 {repo_name}_StargazerInsightsGPT4 AS
                    SELECT name,
                            country,
                            city,
                            email,
                            occupation,
                            programming_languages,
                            social_media,
                            GPT4("{LLM_prompt}", topics_of_interest)
                    FROM {repo_name}_StargazerInsights;
        """
        ).df()

        select_query = cursor.query(
            f"""
                SELECT *
                FROM {repo_name}_StargazerInsightsGPT4;
        """
        ).df()

        select_query.to_csv(f"{repo_name}_insights.csv", index=False)

    except Exception as e:
        print(f"❗️ EvaDB Session ended with an error: {e}")
