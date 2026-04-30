import re
import os
import boto3
import awsgi
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs

from flask import Flask, render_template_string

NEWSFEED_FILE = Path(__file__).parent / "newsfeed.txt"

HEADER_PATTERN = re.compile(
    r"^Query:\s*(.*?)\s*\|\s*Published after:\s*(.*?)\s*\|\s*"
    r"Returned:\s*(\d+)\s*/\s*Total found:\s*(\d+)\s*$"
)
ARTICLE_PATTERN = re.compile(r"^(\d+)\.\s+(.*)$")
SOURCE_LINE_PATTERN = re.compile(r"^Source:\s*(.*?)\s*\|\s*Published:\s*(.*)$")

app = Flask(__name__)


def parse_newsfeed(text):
    lines = text.splitlines()
    meta = {
        "query": "N/A",
        "published_after": "N/A",
        "returned": "0",
        "total_found": "0",
    }
    articles = []

    index = 0
    if lines:
        match = HEADER_PATTERN.match(lines[0].strip())
        if match:
            meta = {
                "query": match.group(1),
                "published_after": match.group(2),
                "returned": match.group(3),
                "total_found": match.group(4),
            }
            index = 1

    while index < len(lines):
        current_line = lines[index].strip()
        title_match = ARTICLE_PATTERN.match(current_line)
        if not title_match:
            index += 1
            continue

        title = title_match.group(2).strip()
        source = "Unknown"
        published_at = "Unknown"
        description = ""
        url = ""

        if index + 1 < len(lines):
            source_line = lines[index + 1].strip()
            source_match = SOURCE_LINE_PATTERN.match(source_line)
            if source_match:
                source = source_match.group(1).strip() or "Unknown"
                published_at = source_match.group(2).strip() or "Unknown"

        if index + 2 < len(lines):
            description = lines[index + 2].strip()

        if index + 3 < len(lines):
            url = lines[index + 3].strip()

        articles.append(
            {
                "title": title,
                "source": source,
                "published_at": published_at,
                "description": description,
                "url": url,
            }
        )

        index += 4
        while index < len(lines) and not lines[index].strip():
            index += 1

    return meta, articles


@app.route("/")
def index():
    feed_text = None
    error_message = None

    s3_bucket = os.environ.get("S3_BUCKET")
    if s3_bucket:
        s3 = boto3.client("s3", region_name="us-east-1")
        try:
            obj = s3.get_object(Bucket=s3_bucket, Key="newsfeed/newsfeed.txt")
            feed_text = obj["Body"].read().decode("utf-8")
        except Exception as exc:
            error_message = f"Failed to fetch newsfeed from S3: {exc}"
    else:
        if NEWSFEED_FILE.exists():
            feed_text = NEWSFEED_FILE.read_text(encoding="utf-8")
        else:
            error_message = "newsfeed.txt not found. Run getnewsfeed.py first."

    if not feed_text:
        return render_template_string(
            TEMPLATE,
            meta=None,
            articles=[],
            error_message=error_message or "No newsfeed data available.",
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    meta, articles = parse_newsfeed(feed_text)
    return render_template_string(
        TEMPLATE,
        meta=meta,
        articles=articles,
        error_message=None,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
	<meta charset="utf-8" />
	<meta name="viewport" content="width=device-width, initial-scale=1" />
	<title>News Feed Viewer</title>
	<style>
		:root {
			--bg: #f5f7fb;
			--ink: #132238;
			--muted: #5f6b7a;
			--panel: #ffffff;
			--line: #dde3eb;
			--accent: #0d8d6d;
			--shadow: 0 10px 30px rgba(14, 29, 46, 0.08);
		}

		* { box-sizing: border-box; }

		body {
			margin: 0;
			font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
			color: var(--ink);
			background:
				radial-gradient(1600px 700px at 20% -10%, #d9f5ed 0%, transparent 60%),
				radial-gradient(1200px 500px at 100% 0%, #dce7ff 0%, transparent 55%),
				var(--bg);
		}

		.container {
			max-width: 960px;
			margin: 0 auto;
			padding: 28px 18px 42px;
		}

		.header {
			background: linear-gradient(120deg, #0a5a7a, #0d8d6d);
			color: #f4fffb;
			border-radius: 18px;
			box-shadow: var(--shadow);
			padding: 22px;
			margin-bottom: 20px;
		}

		.title {
			margin: 0 0 8px;
			font-size: clamp(1.4rem, 2.5vw, 2rem);
			letter-spacing: 0.02em;
		}

		.meta-grid {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
			gap: 10px;
			margin-top: 14px;
			color: #d7ffef;
			font-size: 0.94rem;
		}

		.meta-pill {
			background: rgba(255, 255, 255, 0.16);
			border: 1px solid rgba(255, 255, 255, 0.28);
			border-radius: 999px;
			padding: 8px 12px;
			backdrop-filter: blur(2px);
		}

		.article {
			background: var(--panel);
			border: 1px solid var(--line);
			border-radius: 14px;
			box-shadow: var(--shadow);
			padding: 16px;
			margin-bottom: 14px;
			transition: transform 0.2s ease, box-shadow 0.2s ease;
		}

		.article:hover {
			transform: translateY(-2px);
			box-shadow: 0 14px 34px rgba(12, 30, 48, 0.12);
		}

		.article h2 {
			margin: 0 0 10px;
			font-size: 1.1rem;
			line-height: 1.35;
		}

		.article-info {
			color: var(--muted);
			font-size: 0.9rem;
			margin-bottom: 10px;
		}

		.article p {
			margin: 0 0 12px;
			line-height: 1.5;
		}

		.article a {
			color: #0a5a7a;
			text-decoration: none;
			font-weight: 600;
		}

		.article a:hover {
			text-decoration: underline;
		}

		.empty-state {
			background: #fff8e6;
			border: 1px solid #ffd98f;
			color: #6f4b00;
			border-radius: 12px;
			padding: 14px;
			margin-bottom: 14px;
		}

		.footer {
			color: var(--muted);
			text-align: center;
			font-size: 0.86rem;
			margin-top: 20px;
		}
	</style>
</head>
<body>
	<main class="container">
		<section class="header">
			<h1 class="title">Latest News Feed</h1>

			{% if meta %}
			<div class="meta-grid">
				<div class="meta-pill"><strong>Query:</strong> {{ meta.query }}</div>
				<div class="meta-pill"><strong>Since:</strong> {{ meta.published_after }}</div>
				<div class="meta-pill"><strong>Returned:</strong> {{ meta.returned }}</div>
				<div class="meta-pill"><strong>Total Found:</strong> {{ meta.total_found }}</div>
			</div>
			{% endif %}
		</section>

		{% if error_message %}
			<div class="empty-state">{{ error_message }}</div>
		{% elif not articles %}
			<div class="empty-state">No articles available in newsfeed.txt.</div>
		{% else %}
			{% for article in articles %}
			<article class="article">
				<h2>{{ loop.index }}. {{ article.title }}</h2>
				<div class="article-info">Source: {{ article.source }} | Published: {{ article.published_at }}</div>
				<p>{{ article.description or "No description available." }}</p>
				{% if article.url %}
					<a href="{{ article.url }}" target="_blank" rel="noopener noreferrer">Read full article</a>
				{% endif %}
			</article>
			{% endfor %}
		{% endif %}

		<div class="footer">Rendered at {{ generated_at }}</div>
	</main>
</body>
</html>
"""


def handler(event, context):
    event = event or {}

    if "httpMethod" not in event:
        request_context = event.get("requestContext") or {}
        http_context = request_context.get("http") or {}
        method = http_context.get("method")

        if method:
            raw_query = event.get("rawQueryString") or ""
            multi_query = parse_qs(raw_query, keep_blank_values=True)
            single_query = {
                key: values[-1] if values else "" for key, values in multi_query.items()
            }

            headers = event.get("headers") or {}
            event = {
                "resource": event.get("rawPath") or "/",
                "path": event.get("rawPath") or http_context.get("path") or "/",
                "httpMethod": method,
                "headers": headers,
                "multiValueHeaders": {key: [value] for key, value in headers.items()},
                "queryStringParameters": single_query or None,
                "multiValueQueryStringParameters": multi_query or None,
                "pathParameters": event.get("pathParameters") or {},
                "stageVariables": event.get("stageVariables") or {},
                "requestContext": request_context,
                "body": event.get("body"),
                "isBase64Encoded": event.get("isBase64Encoded", False),
            }
        else:
            event = {
                "httpMethod": "GET",
                "path": "/",
                "headers": {},
                "multiValueHeaders": {},
                "queryStringParameters": {},
                "multiValueQueryStringParameters": {},
                "pathParameters": {},
                "stageVariables": {},
                "requestContext": {},
                "body": None,
                "isBase64Encoded": False,
            }

    return awsgi.response(app, event, context)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
