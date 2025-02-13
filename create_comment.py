import json
from community_post_checker import main as get_data


def create_post():
    with open("entries.txt", "r", newline="", encoding="utf-8") as entries_file:
        entries_list = entries_file.read()

    with open("authors_list.txt", "r", newline="", encoding="utf-8") as authors_file:
        authors_list = authors_file.read()

    winners = []
    with open("winners.txt", "r", newline="", encoding="utf-8") as winners_file:
        for winner_line in winners_file:
            winner_line.strip()
            if winner_line:
                winner = json.loads(winner_line)
                winners.append(winner)
    winners.pop(0)
    winners_formatted = [
        f"- **{winner["author"]}** ha vinto {winner["wins"]} volte" for winner in winners
    ]
    winners_formatted.sort(key=lambda x: int(x.split()[-2]), reverse=True)

    with open("comment.txt", "w", newline="", encoding="utf-8") as comment_file:
        comment_file.write(
            f"I post validi per il contest pubblicati nell'ultima settimana sono:\n\n"
            f"{entries_list}\n\n"
            f"Queste invece le statistiche degli autori selezionati:\n\n"
            f"{authors_list}\n\n"
            f"Per finire, ecco la classifica dei vincitori del contest:\n\n"
            + "\n".join(f"{winner}" for winner in winners_formatted)
            + "\n"
        )

    return True


def main():
    data = get_data()
    if data:
        print("Success! Gathered all required data")
    else:
        print("Unable to gather all required data: something went wrong")
    post = create_post()
    if post:
        print("comment.txt is ready to be used!")
    else:
        print("Unable to create comment.txt: something went wrong")


if __name__ == "__main__":
    main()
