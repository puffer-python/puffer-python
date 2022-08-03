import os
import requests

from catalog import celery


@celery.task
def slack_alert(title, content):
    env = (os.getenv('FLASK_ENV') or 'develop').upper()
    slack_url = os.getenv('SLACK_HOOK_URL')
    tag_users = os.getenv('SLACK_HOOK_TAGS') or 'quang.lm'
    if slack_url:
        pretext = f'[{env}] {title}'
        if tag_users:
            tag_users = tag_users.split(',')
            tag_users = map(lambda x: f'<@{x}>', tag_users)
            tag_users = ' '.join(tag_users)
            pretext = f'{pretext} {tag_users}'
        data = {
            'attachments': [
                {
                    'mrkdwn_in': ['pretext', 'text'],
                    'color': '#F35A00',
                    'pretext': pretext,
                    'text': content
                }
            ]
        }
        requests.post(slack_url, json=data)
