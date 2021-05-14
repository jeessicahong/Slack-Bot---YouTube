import slack
import os
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from googleapiclient.discovery import build

app = Flask(__name__)

# SLACK CREDENTIALS
slack_events_adapter = SlackEventAdapter(os.environ.get("SLACK_EVENTS_TOKEN"), "/slack/", app)
slack_web_client = slack.WebClient(token=os.environ.get("SLACKBOT_TOKEN"))

# YOUTUBE CREDENTIALS/CONSTANTS
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'
YOUTUBE_URL = 'https://www.youtube.com/watch?v='
YOUTUBE_VIDEO_SEARCH_RESULT = 'youtube#video'

# ERROR MESSAGES
PROFANITY_ERR = "*Your query contains profanity/NFSW material. Please try again!*"


def message_channel(channel_id, text):
    slack_web_client.chat_postMessage(channel=channel_id, text=text)


def get_youtube_video_links(youtube, text):
    search_results = youtube.search().list(
        q=text,
        part='id'
    ).execute()

    videos = []

    for search_result in search_results.get('items', []):
        if search_result['id']['kind'] == YOUTUBE_VIDEO_SEARCH_RESULT:
            videos.append(search_result['id']['videoId'])

    return videos[0]


def check_if_bad_word(text):
    with open('bad-words.txt') as file:
        contents = file.read()

        if text in contents:
            print("yikes! there's a bad word in here")
            return True
        return False


@app.route('/slack/youtube', methods=['POST'])
def youtube():
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')

    if check_if_bad_word(text):
        message_channel(channel_id, text=PROFANITY_ERR)
    else:
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)
        youtube_url = YOUTUBE_URL + get_youtube_video_links(youtube, text)
        message_channel(channel_id, youtube_url)

    return Response(), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
