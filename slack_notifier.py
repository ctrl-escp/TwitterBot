import json
import requests


class SlackNotifier:
	chat_post_message_url = "https://slack.com/api/chat.postMessage"

	def __init__(self, token, channel_id):
		self.channel_id = channel_id
		self.headers = {
			"Content-Type": "application/json; charset=utf-8",
			"Authorization": f"Bearer {token}"
		}

	def post_message(self, text):
		msg = {
			"channel": self.channel_id,
			"text": text
		}
		r = requests.post(self.chat_post_message_url, data=json.dumps(msg), headers=self.headers)
		if r.status_code != 200:
			print(json.dumps(r.json(), indent=2))


if __name__ == '__main__':
	with open(".config.json", encoding="utf-8") as f:
		config = json.load(f)
	sn = SlackNotifier(config["token"], config["channel_id"])
	sn.post_message("Hello world!")
