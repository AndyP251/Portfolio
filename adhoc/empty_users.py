from dotenv import load_dotenv
load_dotenv()

import boto3
import os

# Get credentials from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Upload empty array
try:
    response = s3.put_object(
        Bucket=BUCKET_NAME,
        Key='users.json',
        Body='[]',
        ContentType='application/json'
    )
    
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("Successfully emptied users.json")
    else:
        print("Failed to empty users.json")
except Exception as e:
    print(f"Error: {e}")