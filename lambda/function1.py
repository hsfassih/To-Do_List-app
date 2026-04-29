import json


# testing with a simple hello function at first
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"message": "Hello from Lambda!"})}
