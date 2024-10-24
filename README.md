# Hive Community Post Checker Script

## Description

This Python script interacts with the Hive blockchain to retrieve posts published in a specific community (e.g., `hive-146620`), checks if the posts meet certain requirements, and saves the eligible ones in a TXT file. The requirements checked by the script include:

- The post must be written in Italian or contains a translation in Italian from another language.
- The post must have at least 500 words or 1000 words if there's more than one language.
- The post author must have replied to a post in the target community in the past 7 days.
- The post author must have voted in one of the last 3 polls published by a specific account.

The script also generate a list with all the eligible authors, the number of comments published (in the last 7 days) and of polls voted (up to 3).

Moreover, the script also keep track of all the previous winners of the contests in a TXT file.

## Main Features

- **Post Retrieval**: Retrieves posts from a specific community on Hive.
- **Language Filtering**: Verifies if the post content is in Italian (a translation is ok).
- **Word Count**: Counts the number of words in the post body (excluding images and links).
- **Comment Reply Check**: Verifies if the post author has replied to comments in the past 7 days.
- **Poll Voting Check**: Verifies if the author voted in one of the last 3 polls.
- **Authors' Stats**: Check autors' stats and save them in a TXT file
- **Winners List**: Keep track of the winners of the contest

## System Requirements

Make sure you have Python 3.x installed. Additionally, install the following dependencies using `pip`:

```bash
pip install -r requirements.txt
