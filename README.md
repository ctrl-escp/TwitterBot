# TwitterBot
Fetch the latest tweets from Twitter by keyword.

## Installation
Requires Python 3.10 and above
>python3 -m pip install -r requirements.txt

## Usage
### Command-Line Usage
>python3 tb.py keyword -l 20

You can always run `python3 tb.py -h`
```
usage: tb.py [-h] [-l LIMIT] KEYWORD [KEYWORD ...]

Twitter Bot

positional arguments:
  KEYWORD               Keyword(s) to retrieve results for

options:
  -h, --help            show this help message and exit
  -l LIMIT, --limit LIMIT
                        Max number of tweets to retrieve per keyword
```

### Programmatically
```python
from tb import TwitterBot
tb = TwitterBot()
tbks = tb.get_latest_tweets_by_keywords(["keyword"], 20)
```
