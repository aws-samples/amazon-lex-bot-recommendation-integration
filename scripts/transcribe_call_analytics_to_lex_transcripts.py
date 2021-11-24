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
import uuid

import boto3


def get_random_time():
    TIME_STRING_FORMAT = '%02d:%02d:%02d'
    # Generate random number scaled to number of seconds in a day: (24*60*60) = 86,400
    time = int(random.random() * 86400)
    hours = int(time / 3600)
    minutes = int((time - hours * 3600) / 60)
    seconds = time - hours * 3600 - minutes * 60
    return TIME_STRING_FORMAT % (hours, minutes, seconds)


def convert_to_contact_lens_format(call_analytics_json):
    cur_json = dict()
    cur_json['ContentMetadata'] = call_analytics_json['ContentMetadata']
    if 'RedactionTypes' not in cur_json['ContentMetadata']:
        cur_json['ContentMetadata']['RedactionTypes'] = None
    cur_json['CustomerMetadata'] = dict()
    cur_str = str(int(random.random() * 10000))
    cur_uuid = uuid.uuid4()
    cur_json['CustomerMetadata']['ContactId'] = '{}-{}'.format(cur_str, cur_uuid)
    cur_json['Participants'] = list()

    for index in range(len(call_analytics_json['Participants'])):
        cur_json['Participants'].append(
            {'ParticipantId': index + 1,
             'ParticipantRole': call_analytics_json['Participants'][index]['ParticipantRole']})

    participant_role_to_id = dict()
    for entry in cur_json['Participants']:
        participant_role_to_id[entry['ParticipantRole']] = entry['ParticipantId']

    cur_json['Version'] = '1.1.0'
    cur_json['Transcript'] = list()

    for transcript in call_analytics_json['Transcript']:
        cur_transcript = dict()
        cur_transcript['Id'] = transcript['Id']
        cur_transcript['Content'] = transcript['Content']
        cur_transcript['ParticipantId'] = participant_role_to_id[transcript['ParticipantRole']]
        cur_json['Transcript'].append(cur_transcript)
    today = datetime.date.today()
    file_name = '{}_analysis_{}_T{}Z.json'.format(cur_str, today.strftime('%Y-%m-%d'), get_random_time())
    return file_name, cur_json


def main():
    arg_parser = argparse.ArgumentParser(description='Read Amazon Transcribe Call Analytics transcripts from a configured Amazon S3 '
                                                     'bucket, convert it into the Amazon Lex/Contact Lens transcript format  '
                                                     'and upload it into a different Amazon S3 bucket.')
    arg_parser.add_argument('--source', required=True, type=str, help="Set the source Amazon S3 bucket containing Amazon Transcribe "
                                                                      "Call Analytics transcripts")
    arg_parser.add_argument('--target', required=True, type=str, help="Set the target Amazon S3 bucket to upload the Amazon Lex "
                                                                      "transcripts")
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
                call_analytics_json = s3_file.get('Body').read().decode('utf-8')

                # Transform the file to the Contact Lens format.
                file_name, contact_lens_json = convert_to_contact_lens_format(json.loads(call_analytics_json))

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
