import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import boto3

_cached_token = None


def _get_api_token():
    global _cached_token
    if _cached_token:
        return _cached_token
    secret_arn = os.environ.get("SECRET_ARN")
    if secret_arn:
        client = boto3.client("secretsmanager", region_name="us-east-1")
        response = client.get_secret_value(SecretId=secret_arn)
        _cached_token = json.loads(response["SecretString"])["THENEWS_API_TOKEN"]
    else:
        _cached_token = os.environ.get("THENEWS_API_TOKEN") or os.environ.get(
            "NEWS_API_KEY"
        )
    return _cached_token


THE_NEWS_API_URL = "https://api.thenewsapi.com/v1/news/top"
IS_LAMBDA_RUNTIME = "AWS_LAMBDA_FUNCTION_NAME" in os.environ
NEWSFEED_FILE = (
    Path("/tmp/newsfeed.txt")
    if IS_LAMBDA_RUNTIME
    else Path(__file__).parent / "newsfeed.txt"
)


def _render_newsfeed_text(payload):
    lines = [
        (
            f"Query: {payload['query']}  |  Published after: {payload['publishedAfter']}  |  "
            f"Returned: {payload['returned']} / Total found: {payload['totalResults']}"
        ),
        "",
    ]

    articles = payload.get("articles", [])
    if not articles:
        lines.append("No articles found in the last 24 hours for this query.")
        return "\n".join(lines) + "\n"

    for i, article in enumerate(articles, 1):
        lines.append(f"{i}. {article.get('title') or 'Untitled'}")
        lines.append(
            "   "
            f"Source: {article.get('source') or 'Unknown'}  |  "
            f"Published: {article.get('publishedAt') or 'Unknown'}"
        )
        lines.append(f"   {article.get('description') or 'No description available.'}")
        lines.append(f"   {article.get('url') or ''}")
        lines.append("")

    return "\n".join(lines)


def _write_newsfeed_file(payload):
    content = _render_newsfeed_text(payload)
    NEWSFEED_FILE.write_text(content, encoding="utf-8")

    s3_bucket = os.environ.get("S3_BUCKET")
    if s3_bucket:
        s3 = boto3.client("s3", region_name="us-east-1")
        try:
            s3.put_object(
                Bucket=s3_bucket,
                Key="newsfeed/newsfeed.txt",
                Body=content.encode("utf-8"),
                ContentType="text/plain",
            )
        except Exception as exc:
            raise OSError(f"Failed to upload to S3: {exc}")


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
    token = _get_api_token()
    if not token:
        return {"statusCode": 500, "body": json.dumps({"error": "API token not set"})}

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
        "api_token": token,
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

    payload = {
        "query": query,
        "publishedAfter": published_after,
        "totalResults": meta.get("found", len(articles)),
        "returned": meta.get("returned", len(articles)),
        "articles": articles,
    }

    try:
        _write_newsfeed_file(payload)
    except OSError as exc:
        payload["fileWriteWarning"] = f"Could not write {NEWSFEED_FILE.name}: {exc}"

    return {
        "statusCode": 200,
        "body": json.dumps(payload),
    }


if __name__ == "__main__":
    result = handler({}, None)
    body = json.loads(result["body"])
    if result["statusCode"] != 200:
        print("Error:", body.get("error"))
        if body.get("details"):
            print("Details:", body.get("details"))
    else:
        print(_render_newsfeed_text(body), end="")
        print(f"Saved feed to: {NEWSFEED_FILE}")
        if body.get("fileWriteWarning"):
            print("Warning:", body["fileWriteWarning"])
