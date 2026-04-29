import json


# testing workflow fristly with a simple hello function
def handler(event, context):
    return {"statusCode": 200, "body": json.dumps({"message": "Hello from Lambda!"})}
