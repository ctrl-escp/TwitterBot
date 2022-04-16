"""
Twitter Bot
Retrieve recent tweets by keywords.
"""
import re
import requests
try:
	from sqliter3.sqliter3 import Sqliter3
except ModuleNotFoundError:
	# noinspection PyUnresolvedReferences,PyPackageRequirements
	from TwitterBot.sqliter3.sqliter3 import Sqliter3


class TwitterBot:
	search_url = "https://api.twitter.com/2/tweets/search/recent"
	default_db_filename = "tb.db"
	url_to_tweet = "https://twitter.com/i/web/status"
	_tb_schema = """
	CREATE TABLE IF NOT EXISTS "seen_tweets" (
	"id"			INTEGER NOT NULL UNIQUE PRIMARY KEY AUTOINCREMENT,
	"tweet_id"		TEXT NOT NULL UNIQUE,
	"text"			TEXT NOT NULL,
	"parsed_text"	TEXT
	);"""
	url_regex = re.compile(r"\bhttps?://t\.co/\S+")

	def __init__(self, token, db_filename=None):
		"""
		:param str token: The Twitter bot's bearer token.
		:param str db_filename: (optional) The name of the database file to save tweets to.
		"""
		self.bearer_token = f"Bearer {token}"
		self.db = Sqliter3(db_filename or self.default_db_filename)
		table_created = self.db.run_query(self._tb_schema)
		if not table_created["success"]:
			raise Exception(table_created["error"])

	def get_tweets_for_phrase(self, search_phrase, max_results):
		"""

		:param str search_phrase: The phrase to search for.
		:param int max_results: The maximum number of retrieved results. Must be between 10 and 100.
		:return dict: Success=True and results if successful; success=False and error message otherwise.
		"""
		result = {"success": False}
		if not 100 >= max_results >= 10:
			result["error"] = f"The results limit must be between 10 and 100. Got {max_results}"
		else:
			try:
				params = {"query": f"{search_phrase} -is:retweet", "max_results": max_results}		# Skip retweets.
				headers = {"Authorization": self.bearer_token}
				resp = requests.get(self.search_url, headers=headers, params=params)
				if resp.status_code == 200:
					result["results"] = resp.json()
					result["success"] = True
				else:
					result["error"] = f"Got status code {resp.status_code}; text: {resp.text}"
			except Exception as exp:
				result["error"] = f"{exp}"
		return result

	def _parse_tweet(self, text):
		"""
		Remove Twitter shortened URLs as many links to the same source are given different addresses, making the
		Tweet appear different even though the content is the same.
		:param str text: The tweet to parse.
		:return str: The parsed tweet.
		"""
		return self.url_regex.sub("", text).strip()

	def _exists_in_db_in_either_text_or_id(self, tweet_details):
		"""
		:param dict tweet_details: The tweet id and its parsed text.
		:return Boolean: True if the tweet was seen before; False otherwise.
		"""
		query = """
		SELECT * FROM seen_tweets
		WHERE
			tweet_id = ?
			OR parsed_text = ?;"""
		result = self.db.run_query(query, (tweet_details["id"], tweet_details["parsed"]))
		if not result["success"]:
			raise Exception(result["error"])
		return len(list(result["rows"])) == 1

	def _save_to_db(self, t):
		query = """
		INSERT INTO seen_tweets (tweet_id, text, parsed_text)
		VALUES (?, ?, ?);"""
		return self.db.run_query(query, (t["id"], t["text"], t["parsed"]))["success"]

	def _is_a_new_tweet(self, t):
		t["parsed"] = self._parse_tweet(t["text"])
		if not self._exists_in_db_in_either_text_or_id(t):
			return self._save_to_db(t)
		return False

	def get_latest_tweets_by_keywords(self, keywords, max_results):
		tbk = {}
		for keyword in keywords:
			res = self.get_tweets_for_phrase(keyword, max_results)
			if not res["success"]:
				raise Exception(res["error"])
			new_tweets = []
			for tweet in res["results"]["data"]:
				if self._is_a_new_tweet(tweet):
					new_tweets.append({"text": tweet["text"], "url": f"{self.url_to_tweet}/{tweet['id']}"})
			if new_tweets:
				tbk[keyword] = new_tweets
		return tbk


if __name__ == '__main__':
	import json
	from argparse import ArgumentParser
	parser = ArgumentParser(description="Twitter Bot")
	parser.add_argument("token", action="store", type=str, help="Bearer token for Twitter.")
	parser.add_argument("keywords", metavar="KEYWORD", action="extend", nargs="+", type=str,
						help="Keyword(s) to retrieve results for")
	parser.add_argument("-l", "--limit", action="store", type=int, default=10,
						help="Max number of tweets to retrieve per keyword")
	args = parser.parse_args()

	tb = TwitterBot(args.token)
	tbks = tb.get_latest_tweets_by_keywords(args.keywords, args.limit)
	print(json.dumps(tbks, indent=2))
