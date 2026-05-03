import json
import os
import boto3
from botocore.exceptions import ClientError

RECIPIENT = "fasih.hasny@softbuilds.co"
REGION = "us-east-1"


def handler(event, context):
    sender = os.environ["SENDER_EMAIL"]
    displaynews_url = os.environ["DISPLAYNEWS_URL"]

    ses = boto3.client("ses", region_name=REGION)

    subject = "News Feed - View Latest News"
    body_text = (
        f"Click the link below to view the latest news feed:\n\n{displaynews_url}"
    )
    body_html = f"""
    <html><body>
      <h2>Latest News Feed</h2>
      <p>Click the link below to view the latest news:</p>
      <p><a href="{displaynews_url}">{displaynews_url}</a></p>
    </body></html>
    """

    try:
        response = ses.send_email(
            Source=sender,
            Destination={"ToAddresses": [RECIPIENT]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                },
            },
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"message": "Email sent", "messageId": response["MessageId"]}
            ),
        }
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }
