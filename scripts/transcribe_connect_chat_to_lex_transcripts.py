"""
  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
  SPDX-License-Identifier: MIT-0

  Permission is hereby granted, free of charge, to any person obtaining a copy of this
  software and associated documentation files (the "Software"), to deal in the Software
  without restriction, including without limitation the rights to use, copy, modify,
  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 """

import argparse
import datetime
import json
import random
import sys

import boto3

DATE_CHARACTERS = 10
TIME_CHARACTERS = 8

def get_random_time():
    TIME_STRING_FORMAT = '%02d:%02d:%02d'
    # Generate a random number scaled to the number of seconds in a day
    time = int(random.random() * 86400)
    hours = int(time / 3600)
    minutes = int((time - hours * 3600) / 60)
    seconds = time - hours * 3600 - minutes * 60
    return TIME_STRING_FORMAT % (hours, minutes, seconds)


def convert_to_contact_lens_format(connect_chat_json):
    contact_lens_json = dict()
    contact_lens_json['ContentMetadata'] = dict()
    contact_lens_json['ContentMetadata']['Output'] = 'Raw'
    contact_lens_json['ContentMetadata']['RedactionTypes'] = None

    contact_lens_json['CustomerMetadata'] = dict()
    contact_lens_json['CustomerMetadata']['ContactId'] = connect_chat_json['ContactId']

    contact_lens_json['Version'] = '1.1.0'
    contact_lens_json['Transcript'] = list()
    contact_lens_json['Participants'] = list()

    for transcript in connect_chat_json['Transcript']:
        if transcript['ContentType'] == 'text/plain':
            contact_lens_transcript = dict()
            contact_lens_transcript['ParticipantId'] = transcript['ParticipantId']
            contact_lens_transcript['Id'] = transcript['Id']
            contact_lens_transcript['Content'] = transcript['Content']
            contact_lens_json['Transcript'].append(contact_lens_transcript)

            participant = dict()
            participant['ParticipantId'] = transcript['ParticipantId']
            if transcript['ParticipantRole'] == 'SYSTEM':
                participant['ParticipantRole'] = 'AGENT'
            else:
                participant['ParticipantRole'] = transcript['ParticipantRole']
            if participant not in contact_lens_json['Participants']:
                contact_lens_json['Participants'].append(participant)

    if len(connect_chat_json['Transcript']) > 0:
        date = connect_chat_json['Transcript'][0]['AbsoluteTime'][:DATE_CHARACTERS]
        time = connect_chat_json['Transcript'][0]['AbsoluteTime'][DATE_CHARACTERS + 1:DATE_CHARACTERS + 1 + TIME_CHARACTERS]
        file_name = '{}_analysis_{}_T{}Z.json'.format(contact_lens_json['CustomerMetadata']['ContactId'], date, time)
    else:
        today = datetime.date.today()
        file_name = '{}_analysis_{}_T{}Z.json'.format(contact_lens_json['CustomerMetadata']['ContactId'],
                                                      today.strftime('%Y-%m-%d'), get_random_time())

    return file_name, contact_lens_json


def main():
    arg_parser = argparse.ArgumentParser(description='Read Amazon Connect chat transcripts from a configured Amazon S3 '
                                                     'bucket, convert them into the Amazon Lex/Contact Lens transcript '
                                                     'format, and upload them into a different Amazon S3 bucket.')
    arg_parser.add_argument('--source', required=True, type=str, help="Set the source Amazon S3 bucket containing "
                                                                      "Amazon Connect Chat transcripts")
    arg_parser.add_argument('--target', required=True, type=str, help="Set the target Amazon S3 bucket to upload the "
                                                                      "Amazon Lex transcripts")
    arg_parser.add_argument('--access_key', required=False, type=str,
                            help="Access key of the credentials needed to query Amazon S3")
    arg_parser.add_argument('--secret_key', required=False, type=str,
                            help="Secret key of the credentials needed to query Amazon S3")
    arg_parser.add_argument('--region', required=True, help="Specify the region. This flag is required")

    arg = arg_parser.parse_args()
    source = arg.source
    target = arg.target
    access_key = arg.access_key
    secret_key = arg.secret_key
    region = arg.region

    s3_client = boto3.client('s3',
                             aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key,
                             region_name=region)

    more_keys_left = True
    continuation_token = None
    processed_keys = 0

    # Call Amazon S3 ListObjects to fetch all the keys in the bucket.
    while more_keys_left:
        if continuation_token:
            s3_objects = s3_client.list_objects_v2(Bucket=source,
                                                   ContinuationToken=continuation_token)
        else:
            s3_objects = s3_client.list_objects_v2(Bucket=source)

        # For each Amazon S3 object, attempt performing the transformation.
        for s3_object in s3_objects.get('Contents'):
            if s3_object.get('Key').endswith('.json'):
                # Retrieve the object and read the file.
                s3_file = s3_client.get_object(Bucket=source,
                                               Key=s3_object.get('Key'))
                connect_chat_json = s3_file.get('Body').read().decode('utf-8')

                # Transform the file to the Contact Lens format.
                file_name, contact_lens_json = convert_to_contact_lens_format(json.loads(connect_chat_json))

                # Upload the object back into the original bucket under a new path.
                s3_client.put_object(Bucket=target,
                                     Key=file_name,
                                     Body=bytes(json.dumps(contact_lens_json).encode('UTF-8')))

                processed_keys = processed_keys + 1

        # If more results are available, continue pagination.
        if s3_objects.get('IsTruncated'):
            continuation_token = s3_objects.get('NextContinuationToken')
        else:
            more_keys_left = False

        print('[IN PROGRESS] Successfully transformed [{0}] keys'.format(processed_keys))

    print('[COMPLETE] Successfully transformed [{0}] keys'.format(processed_keys))


if __name__ == '__main__':
    sys.exit(main())
