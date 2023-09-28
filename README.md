# stargazers-reloaded
LLM-Powered Analyses of your GitHub Community using EvaDB

GitHub stars offer unique perspective into what resonates with the coding community, capturing emerging trends and timeless staples. This app utilizes [EvaDB](https://github.com/georgia-tech-db/evadb) to extract deeper insights directly from stargazers' profiles using large language models (LLMs).

Inspired by the original [Stargazers app](https://github.com/spencerkimball/stargazers), this LLM-powered version analyzes unstructured data from web pages to derive key details about your audience. EvaDB streamlines access to leading LLMs, enabling a 360-degree view of your community's interests and needs.

Let AI illuminate the minds of your stargazers - and guide you closer to your audience.

## Getting Started

First install the dependencies:

```bash
pip install -r requirements.txt
```

Then, add the following environment variables to a `.env` file in the root directory of the project (see `example.env`):

```
REPO_URL=<url of the repo to analyze>
GITHUB_API=<your-github-personal-access-token>
OPENAI_API=<your-openai-api-key>
```

Finally, run the app:

```bash
python stargarzers.py
```