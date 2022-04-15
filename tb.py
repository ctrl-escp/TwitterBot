"""
Twitter Bot
Retrieve recent tweets by keywords.
"""
import re
import requests
from db import DatabaseSqlite3


class TwitterBot:
	default_creds_filename = ".creds"
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

	def __init__(self, creds_filename=None):
		self.creds_filename = creds_filename or self.default_creds_filename
		self.bearer_token = self._get_creds()
		self.db = DatabaseSqlite3(self.default_db_filename)
		self._init_db()

	def _init_db(self):
		table_created = self.db.run_query(self._tb_schema)
		if not table_created["success"]:
			raise Exception(table_created["error"])

	def _get_creds(self):
		with open(self.creds_filename, encoding="utf-8") as f:
			bearer_token = f"Bearer {f.read().strip()}"
		return bearer_token

	def get_tweets_by_keyword(self, keyword, max_results):
		result = {"success": False}
		if not 100 >= max_results >= 10:
			result["error"] = f"The results limit must be between 10 and 100. Got {max_results}"
		else:
			try:
				params = {"query": f"{keyword} -is:retweet", "max_results": max_results}
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
		return self.url_regex.sub("", text).strip()

	def _exists_in_db_in_either_text_or_id(self, tweet_details):
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
			res = self.get_tweets_by_keyword(keyword, max_results)
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
	parser.add_argument("keywords", metavar="KEYWORD", action="extend", nargs="+", type=str,
						help="Keyword(s) to retrieve results for")
	parser.add_argument("-l", "--limit", action="store", type=int, default=10,
						help="Max number of tweets to retrieve per keyword")
	args = parser.parse_args()

	tb = TwitterBot()
	tbks = tb.get_latest_tweets_by_keywords(args.keywords, args.limit)
	print(json.dumps(tbks, indent=2))
