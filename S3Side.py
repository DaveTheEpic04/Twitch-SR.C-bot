import signal
import boto3
import os
import json
import sys

Bucket_Name = os.environ['S3_BUCKET_NAME']

s3 = boto3.client('s3')
s3.download_file(Bucket_Name, 'Streamers.json', 'Streamers.json')
print("File Downloaded")

def sigterm_handler(signum, frame):
	streamers = open("Streamers.json", "rb")
	s3.upload_fileobj(streamers, Bucket_Name, 'Streamers.json')
	streamers.close()
	print("File Uploaded")
	sys.exit()

signal.signal(signal.SIGTERM, sigterm_handler)