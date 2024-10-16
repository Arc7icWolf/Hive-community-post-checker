import time
import requests
import json
import csv
from datetime import datetime, timedelta
import re
import markdown
from bs4 import BeautifulSoup
from langdetect import detect_langs, LangDetectException as lang_e
import logging


# logger
def logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("community_post_checker.log", mode="a")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = logger()


### Interaction with Hive API


# Send request, get response, return decoded JSON response
def get_response(data, session: requests.Session):
    urls = [
        "https://api.deathwing.me",
        "https://api.hive.blog",
        "https://hive-api.arcange.eu",
        "api.openhive.network"
    ]
    for url in urls:
        request = requests.Request("POST", url=url, data=data).prepare()
        response_json = session.send(request, allow_redirects=False)
        if response_json.status_code == 502:
            continue
        response = response_json.json()["result"]
        return response


### Check requirements of the posts // API interaction --> no


# Check it target language is among the top languages and number of languages
def text_language(text):
    try:
        languages = detect_langs(text)
        num_languages = len(languages)

        # Double check the presence of the target language to avoid false negatives
        if not any(lang.lang == "it" for lang in languages):
            text_length = len(text)
            half_length = text_length // 2
            first_half = text[:half_length]
            second_half = text[half_length:]
            for _ in range(2):
                languages = detect_langs(first_half)
                if any(lang.lang == "it" for lang in languages):
                    num_languages = 2  # Set to 2 because there's another language
                    break
                languages = detect_langs(second_half)
                if any(lang.lang == "it" for lang in languages):
                    num_languages = 2  # Same as above
                    break
    except lang_e:
        logger.error(f"Language error: {lang_e}")
        return False, 0

    # In case there are more than 2 languages, sort and take only the 2 most prob
    languages_sorted = sorted(languages, key=lambda x: x.prob, reverse=True)
    top_languages = (
        languages_sorted[:2] if len(languages_sorted) > 1 else languages_sorted
    )

    contains_target_lang = any(lang.lang == "it" for lang in top_languages)
    return contains_target_lang, num_languages


# Clean text before converting and counting words
def clean_markdown(md_text):
    # Remove images
    md_text = re.sub(r"!\[.*?\]\(.*?\)", "", md_text)

    # Remove hyperlinks
    md_text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", md_text)

    return md_text


# Convert to plain text and check post's length
def convert_and_count_words(md_text):
    cleaned_md_text = clean_markdown(md_text)
    html = markdown.markdown(cleaned_md_text, output_format="html")

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()

    words = re.findall(r"\b\w+\b", text)
    return len(words)


### Check requirements of the posts // API interaction --> yes


# Check if target account commented a post in the past 7 days in the target community
def has_replied(author, seven_days, session: requests.Session):
    # Get replies from target author
    data = (
        f'{{"jsonrpc":"2.0", "method":"bridge.get_account_posts", '
        f'"params":{{"sort":"comments", "account": "{author}", "limit": 100}}, "id":1}}'
    )
    replies = get_response(data, session)
    for reply in replies:
        reply_time = reply["created"]
        reply_time_formatted = datetime.strptime(reply_time, "%Y-%m-%dT%H:%M:%S")

        if reply_time_formatted < seven_days:
            continue

        if "hive-146620" not in reply["json_metadata"].get("tags", []):
            continue  # If the comment is not in the target community, skip

        return True

    return False


# Check if target account voted in one of the 3 last polls
def has_voted_poll(last_poll, author, session: requests.Session):
    today = datetime.now()
    three_weeks_ago = today - timedelta(days=21, hours=23)
    num = -1
    while True:
        # Get all custom operations from target account, poll votes included
        data = (
            f'{{"jsonrpc":"2.0", "method":"condenser_api.get_account_history", '
            f'"params":["{author}", {num}, 1000, 262144], "id":1}}'
        )
        custom_json = get_response(data, session)
        for op in custom_json:
            link = op[1]["op"][1]["id"]
            if link in last_poll:
                return True
        timestamp = custom_json[0][1]["timestamp"]
        timestamp_formatted = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        if timestamp_formatted < three_weeks_ago:
            return False
        num = custom_json[0][0]


# Fetches the last 3 polls published by the target account
def get_last_polls(session: requests.Session):
    # Get replies from balaenoptera
    data = (
        f'{{"jsonrpc":"2.0", "method":"bridge.get_account_posts", '
        f'"params":{{"sort":"comments", "account": "balaenoptera", '
        f'"limit": 100}}, "id":1}}'
    )
    replies = get_response(data, session)
    polls = []
    for reply in replies:
        # Only look for threads with a poll inside
        is_poll = reply.get("json_metadata", {}).get("isPoll", [])
        if is_poll and len(polls) < 3:  # Get 3 last polls
            poll_link = reply["permlink"]
            polls.append(f"leo_poll_{poll_link}")
    logger.info(polls)
    return polls


# Found and check eligible posts published in the last 7 days in the target community
def eligible_posts(session: requests.Session):
    today = datetime.now()
    seven_days = today - timedelta(days=6, hours=23)

    less_than_seven_days = True

    entries = []

    last_poll = get_last_polls(session)

    author = ""
    permlink = ""
    i = 1

    while less_than_seven_days:
        # Get posts published in the target community
        data = (
            f'{{"jsonrpc":"2.0", "method":"bridge.get_ranked_posts", '
            f'"params":{{"sort":"created","tag":"hive-146620","observer":"", '
            f'"limit": 100, "start_author":"{author}", "start_permlink":"{permlink}"}}, '
            f'"id":1}}'
        )
        posts = get_response(data, session)
        for post in posts:
            author = post["author"]
            body = post["body"]
            created = post["created"]
            permlink = post["permlink"]
            title = post["title"]
            is_pinned = post.get("stats", {}).get("is_pinned", [])

            if author == "libertycrypto27":
                continue  # Skip the author of the contest :(

            if is_pinned:
                continue  # Skip pinned posts, if any

            created_formatted = datetime.strptime(created, "%Y-%m-%dT%H:%M:%S")
            if created_formatted < seven_days:
                less_than_seven_days = False
                print("Work completed", end=" ")
                break  # Stop if post is more than 7 days old

            valid_language, lang_num = text_language(body)

            if valid_language is False:
                continue

            word_count = convert_and_count_words(body)

            if (lang_num == 1 and word_count < 500) or (
                lang_num > 1 and word_count < 1000
            ):
                continue

            if has_replied(author, seven_days, session) is False:
                continue

            if has_voted_poll(last_poll, author, session) is False:
                continue

            message = f"{i}) {author} published ['{title}'](https://www.peakd.com/@{author}/{permlink})"

            entries.append(message)

            print(message)

            i += 1

    with open("entries.csv", "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        for entry in entries:
            csv_writer.writerow([entry])


def main():
    start = time.time()

    try:
        with requests.Session() as session:
            eligible_posts(session)
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"JSON decode error or missing key: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

    elapsed_time = time.time() - start
    print(f"in {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()