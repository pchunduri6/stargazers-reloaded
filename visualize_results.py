import os

import pandas as pd
from dotenv import load_dotenv
import numpy as np
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = 'DejaVu Sans Mono'

from wordcloud import WordCloud


if not load_dotenv():
    print(
        "Could not load .env file or it is empty. Please check if it exists and is readable."
    )
    exit(1)

# REPO DETAILS
repo_url = os.environ.get('REPO_URL')
# Parse the repository URL to extract owner and repo name
parts = repo_url.strip("/").split("/")
repo_name = parts[-1]


def plot_pie_chart(data, title, output_path):

    fig, ax = plt.subplots(figsize=(12, 8))

    # explode first slice if it is not Other
    explode = [0] * len(data)
    if data.index.tolist()[0] != "Other":
        explode[0] = 0.1

    colors = ["#005F73", "#AE2012", "#EE9B00", "#94D2BD"]
    wedges, texts, autotexts = ax.pie(data, explode=explode, colors=colors, autopct=lambda pct: "{:.1f}%".format(pct),
                                    textprops=dict(color="w"), shadow=True, startangle=90)

    labels = [x[0] for x in data.index.tolist()]

    # if "Other is in the list, it will be placed at the end of the pie chart
    if "Other" in labels:
        order_indices = [labels.index(x) for x in labels if x != "Other"]
        other_index = labels.index("Other")
        order_indices.append(other_index)
    else:
        order_indices = list(range(len(labels)))

    ax.legend([wedges[x] for x in order_indices], [labels[x] for x in order_indices],
            loc="center left",
            fancybox=True, shadow=True,
            bbox_to_anchor=(1, 0, 0.5, 1), prop={"size": 18})

    # if any of the percentages is less than 10%, change the font size to 10
    textsize = 20
    for autotext in autotexts:
        if float(autotext.get_text().strip("%")) < 10:
            textsize = 15
            break
    # if the percentage is less  than 4%, don't show the percentage
    for autotext in autotexts:
        if float(autotext.get_text().strip("%")) < 4:
            autotext.set_visible(False)

    plt.setp(autotexts, size=textsize, weight="bold")

    ax.set_title(title, fontsize=20, weight="bold")

    # move title to the right
    ax.title.set_position([0.725, 0.5])
    ax.axis('equal')
    plt.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')


def clean_topics_list(topics_list):
    # each row is a string of topics with various formats
    # extract the strings "Machine Learning", "Databases", and "Web Development" into a list
    # return the list
    output = []
    for row in topics_list:
        output_row = []
        if pd.isna(row):
            output_row.append("Other")
            output.append(output_row)
            continue
        if "Machine Learning".lower() in row.lower():
            output_row.append("Machine Learning")
        if "Databases".lower() in row.lower():
            output_row.append("Databases")
        if "Web development".lower() in row.lower():
            output_row.append("Web development")
        if len(output_row) == 0:
            output_row.append("Other")
        output.append(output_row)

    return output


if __name__ == '__main__':

    output_dir = "images"
    os.makedirs(output_dir, exist_ok=True)

    # 1. Visualize gpt-35 interests insights in a Word Cloud

    gpt35_insights_df = pd.read_csv(f"results/{repo_name}_insights_gpt35.csv", dtype=str)

    all_topics = gpt35_insights_df[f"{repo_name}_stargazerinsights.topics_of_interest"].tolist()
    all_topics = [x for x in all_topics if not pd.isna(x)]

    all_topics = pd.DataFrame(all_topics, columns=['Topics'])
    # Combine all topics into a single text
    all_topics_text = ', '.join(all_topics['Topics'].tolist())

    # Generate the word cloud
    wordcloud = WordCloud(width=1920, height=1080, background_color='white').generate(all_topics_text)
    # Display the word cloud
    plt.figure(figsize=(12, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.title(f"Word Cloud of {repo_name} user interests", fontsize=20, weight="bold", loc="center", y=1.05)
    # move title to the right
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{repo_name}_topics_wordcloud.png"), dpi=300)

    # 2. Visualize gpt-4 topic insights in a pie chart

    insights_df = pd.read_csv(f"results/{repo_name}_insights_gpt4.csv", dtype=str)
    topics_df = insights_df[f"{repo_name}_stargazerinsightsgpt4.response"].tolist()
    topics_list = clean_topics_list(topics_df)

    all_topics = []
    for topics in topics_list:
        all_topics.extend(topics)

    all_topics = pd.DataFrame(all_topics, columns=['Topics'])

    # Count the occurrences of each topic
    topic_counts = all_topics.value_counts()
    plot_pie_chart(data=topic_counts,
                   title=f"Topics of Interest Distribution for {repo_name} users",
                   output_path=os.path.join(output_dir, f"{repo_name}_topics_pie_chart.png"))
    print("Results saved to images folder.")
