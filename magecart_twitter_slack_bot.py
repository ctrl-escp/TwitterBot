import json
from tb import TwitterBot
from datetime import datetime
from slack_notifier import SlackNotifier

keywords = ["magecart"]

tb = TwitterBot()
tbks = tb.get_latest_tweets_by_keywords(keywords, 30)
published_counter = 0
if tbks:
	with open(".config.json", encoding="utf-8") as f:
		config = json.load(f)
	sn = SlackNotifier(config["token"], config["channel_id"])
	for kw in tbks:
		for tweet in tbks[kw]:
			sn.post_message(f"{tweet['text']}\n\n{tweet['url']}")
			published_counter += 1

if published_counter:
	print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Published {published_counter} tweets")
else:
	print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Nothing new...")
