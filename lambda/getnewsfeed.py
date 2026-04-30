import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

THE_NEWS_API_TOKEN = (
    os.environ.get("THENEWS_API_TOKEN")
    or os.environ.get("THENEWSAPI_API_TOKEN")
    or os.environ.get("THENEWS_API_KEY")
    or os.environ.get("NEWS_API_KEY")
)
THE_NEWS_API_URL = "https://api.thenewsapi.com/v1/news/top"


def _extract_error_message(response):
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text if text else f"HTTP {response.status_code}"

    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict):
        code = error.get("code", "api_error")
        message = error.get("message", "Request failed")
        return f"{code}: {message}"
    if isinstance(error, str):
        return error
    return f"HTTP {response.status_code}"


def handler(event, context):
    if not THE_NEWS_API_TOKEN:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": "API token not set",
                    "details": "Set THENEWS_API_TOKEN (preferred) in project root .env",
                }
            ),
        }

    event = event or {}
    query = event.get("query", "technology")
    language = event.get("language", "en")
    locale = event.get("locale", "us")
    limit = int(event.get("limit", 20))
    limit = max(1, min(limit, 50))
    published_after = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    params = {
        "api_token": THE_NEWS_API_TOKEN,
        "search": query,
        "language": language,
        "locale": locale,
        "published_after": published_after,
        "sort": "published_at",
        "limit": limit,
        "page": 1,
    }

    try:
        response = requests.get(THE_NEWS_API_URL, params=params, timeout=15)
    except requests.RequestException as exc:
        return {
            "statusCode": 502,
            "body": json.dumps(
                {"error": "Failed to call TheNewsAPI", "details": str(exc)}
            ),
        }

    if not response.ok:
        return {
            "statusCode": response.status_code,
            "body": json.dumps(
                {
                    "error": "TheNewsAPI request failed",
                    "details": _extract_error_message(response),
                }
            ),
        }

    data = response.json()
    api_articles = data.get("data", [])
    meta = data.get("meta", {})

    articles = [
        {
            "title": a.get("title"),
            "source": a.get("source"),
            "publishedAt": a.get("published_at"),
            "url": a.get("url"),
            "description": a.get("description"),
        }
        for a in api_articles
    ]

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "query": query,
                "publishedAfter": published_after,
                "totalResults": meta.get("found", len(articles)),
                "returned": meta.get("returned", len(articles)),
                "articles": articles,
            }
        ),
    }


if __name__ == "__main__":
    result = handler({}, None)
    body = json.loads(result["body"])
    if result["statusCode"] != 200:
        print("Error:", body.get("error"))
        if body.get("details"):
            print("Details:", body.get("details"))
    else:
        print(
            f"Query: {body['query']}  |  Published after: {body['publishedAfter']}  |  "
            f"Returned: {body['returned']} / Total found: {body['totalResults']}\n"
        )
        if not body["articles"]:
            print("No articles found in the last 24 hours for this query.")
        for i, article in enumerate(body["articles"], 1):
            print(f"{i}. {article['title']}")
            print(
                f"   Source: {article['source']}  |  Published: {article['publishedAt']}"
            )
            print(f"   {article['description']}")
            print(f"   {article['url']}\n")
