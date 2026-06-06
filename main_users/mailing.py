import os

import requests


def send_simple_message():
    api_key = os.environ["MAILGUN_API_KEY"]
    return requests.post(
        "https://api.mailgun.net/v3/sandboxdbe25fb91481494cbf024bccbbef0d5f.mailgun.org/messages",
        auth=("api", api_key),
        data={
            "from": "Excited User <mailgun@sandboxdbe25fb91481494cbf024bccbbef0d5f.mailgun.org>",
            "to": [
                "alejandroiglesiasg@gmail.com",
                "YOU@sandboxdbe25fb91481494cbf024bccbbef0d5f.mailgun.org",
            ],
            "subject": "Hello",
            "text": "Testing some Mailgun awesomeness!",
        },
    )
