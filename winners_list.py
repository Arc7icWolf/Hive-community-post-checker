import requests
import json
import logging
import ast

# logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler("winners_list.log", mode="a")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# INTERACTION WITH HIVE API


# Send request, get response, return decoded JSON response
def get_response(data, session: requests.Session):
    urls = [
        "https://api.deathwing.me",
        "https://api.hive.blog",
        "https://hive-api.arcange.eu",
        "https://api.openhive.network",
    ]
    for url in urls:
        request = requests.Request("POST", url=url, data=data).prepare()
        response_json = session.send(request, allow_redirects=False)
        if response_json.status_code == 502:
            continue
        response = response_json.json()["result"]
        return response


# Get and update list of users who won at least a contest
def get_contest_winners(session: requests.Session):
    # Get replies from target author
    data = (
        f'{{"jsonrpc":"2.0", "method":"bridge.get_account_posts", '
        f'"params":{{"sort":"posts", "account": "balaenoptera", "limit": 100}}, "id":1}}'
    )
    posts = get_response(data, session)
    winners = []
    with open("winners.txt", "r", newline="", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                winner_dict = ast.literal_eval(line)
                winners.append(winner_dict)
    logger.info(f"Previous winners:\n{winners}")
    new_posts_num = 0
    for post in posts:
        if post["created"] == winners[0]["timestamp"]:
            break
        new_posts_num += 1
    if new_posts_num == 0:
        print("No new posts from @balaenoptera found")
        return False
    else:
        print(
            f"Found {new_posts_num} new posts from @baleanoptera: updating winners list..."
        )
        winners[0]["timestamp"] = posts[0]["created"]
    not_winners = ["weeklytops", "libertycrypto27", "balaenoptera"]
    for post in posts[:new_posts_num]:
        beneficiaries = post["beneficiaries"]
        for beneficiary in beneficiaries:
            if (
                beneficiary["weight"] >= 1500
                and beneficiary["account"] not in not_winners
            ):
                winner_found = False
                for winner in winners:
                    if winner.get("author", []) == beneficiary["account"]:
                        winner["wins"] += 1
                        winner_found = True
                        break
                if not winner_found:
                    winners.append({"author": beneficiary["account"], "wins": 1})
    return winners


def update_winners_list(session: requests.Session):
    hall_of_fame = get_contest_winners(session)
    if hall_of_fame:
        with open("winners.txt", "w", newline="", encoding="utf-8") as file:
            for winner in hall_of_fame:
                file.write(json.dumps(winner) + "\n")
            logger.info("Winners list updated")


def main():
    try:
        with requests.Session() as session:
            update_winners_list(session)
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"JSON decode error or missing key: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
