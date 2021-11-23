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

# !/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json
import sys
import uuid
from dateutil import parser

import boto3


def main():
    arg_parser = argparse.ArgumentParser(description='Read Contact Lens transcripts from a configured S3 bucket, '
                                                     'look-up corresponding Lex conversation logs from a configured '
                                                     'CloudWatch Logs ARN, stitch them together and upload it into the '
                                                     'same S3 bucket under a new path'
                                                     'S3 bucket.')
    arg_parser.add_argument('--source', required=True, type=str, help="Set the source S3 bucket containing Contact "
                                                                      "Lens transcripts")
    arg_parser.add_argument('--access_key', required=False, type=str,
                            help="Access key of the credentials needed to query "
                                 "S3 and CloudWatch")
    arg_parser.add_argument('--secret_key', required=False, type=str,
                            help="Secret key of the credentials needed to query "
                                 "S3 and CloudWatch")
    arg_parser.add_argument('--region', required=True, help="Specify the region. This flag is required")
    arg_parser.add_argument('--cloudwatch_log_group_name', required=True, help="Specify the CloudWatch Log Group name "
                                                                               "containing the Lex Conversation Logs")

    arg = arg_parser.parse_args()
    source = arg.source
    access_key = arg.access_key
    secret_key = arg.secret_key
    region = arg.region
    cloudwatch_log_group_name = arg.cloudwatch_log_group_name

    s3_client = boto3.client('s3',
                             aws_access_key_id=access_key,
                             aws_secret_access_key=secret_key,
                             region_name=region)
    cloudwatch_client = boto3.client('logs',
                                     aws_access_key_id=access_key,
                                     aws_secret_access_key=secret_key,
                                     region_name=region)

    more_keys_left = True
    continuation_token = None
    processed_keys = 0
    matched_keys = 0

    # Call S3 ListObjects to fetch all the keys in the bucket.
    while more_keys_left:
        if continuation_token:
            s3_objects = s3_client.list_objects_v2(Bucket=source,
                                                   ContinuationToken=continuation_token,
                                                   Prefix='Analysis/')
        else:
            s3_objects = s3_client.list_objects_v2(Bucket=source,
                                                   Prefix='Analysis/')

        # For each S3 object, attempt performing the transformation.
        for s3_object in s3_objects.get('Contents'):
            if s3_object.get('Key').endswith('.json'):
                # Retrieve the object and read the file.
                s3_file = s3_client.get_object(Bucket=source,
                                               Key=s3_object.get('Key'))
                data = s3_file.get('Body').read().decode('utf-8')

                # Transform the file by appending Lex Conversation Logs, if any is present.
                updated_data, found_match = stitch_conversation_logs(data,
                                                                     s3_object.get('Key'),
                                                                     cloudwatch_log_group_name,
                                                                     cloudwatch_client)

                # Upload the object back into the original bucket under a new path.
                s3_client.put_object(Bucket=source,
                                     Key='AnalysisWithLexLogs/' + s3_object.get('Key'),
                                     Body=bytes(json.dumps(updated_data).encode('UTF-8')))

                # Keep track of number of original Contact Lens files processed.
                processed_keys = processed_keys + 1

                if found_match:
                    # Keep track of how many of those Contact Lens files were successfully matched and stitched with
                    # Lex Conversation Logs.
                    matched_keys = matched_keys + 1

        # If more results are available, continue pagination.
        if s3_objects.get('IsTruncated'):
            continuation_token = s3_objects.get('NextContinuationToken')
        else:
            more_keys_left = False

        print('[IN PROGRESS] Successfully stitched [{0}/{1}] keys'.format(matched_keys, processed_keys))

    print('[COMPLETE] Successfully stitched [{0}/{1}] keys'.format(matched_keys, processed_keys))


def stitch_conversation_logs(data,
                             file_name,
                             cloudwatch_log_group_name,
                             cloudwatch_client):
    json_data = json.loads(data)
    contact_id = json_data['CustomerMetadata']['ContactId']
    customer_id = get_participant_id(json_data, 'CUSTOMER')
    agent_id = get_participant_id(json_data, 'AGENT')
    conversation_timestamp = file_name[(len(file_name) - 25):(len(file_name) - 5)]
    utc_time = parser.parse(conversation_timestamp)
    epoch_time = int(utc_time.timestamp() * 1000)

    # Lex Conversation Logs use the Connect Contact ID as the Session ID. Attempt to find any matching logs.
    lex_logs, found_match = get_cloudwatch_logs(cloudwatch_log_group_name,
                                                cloudwatch_client,
                                                epoch_time,
                                                contact_id)

    # Reverse the list of Lex logs (ordered by time) and add each to the top of the list of transcripts.
    lex_logs.reverse()
    for lex_log in lex_logs:
        lex_json = json.loads(lex_log)
        if 'messages' in lex_json:
            lex_json['messages'].reverse()
            for bot_prompt in lex_json['messages']:
                json_data['Transcript'].insert(0, get_transcript(bot_prompt.get('content'), agent_id))
        if 'inputTranscript' in lex_json:
            json_data['Transcript'].insert(0, get_transcript(lex_json['inputTranscript'], customer_id))
    return json_data, found_match


def get_transcript(lex_transcript, participant_id):
    return {'ParticipantId': participant_id,
            'Id': str(uuid.uuid4()),
            'Content': lex_transcript}


def get_participant_id(json_data, participant_type):
    for participant in json_data['Participants']:
        if participant_type == participant['ParticipantRole']:
            return participant['ParticipantId']


def get_cloudwatch_logs(cloudwatch_log_group_name, cloudwatch_client, epoch_time, contact_id):
    next_token = None
    more_results = True
    lex_logs = []
    found_match = False

    while more_results:
        if next_token:
            response = cloudwatch_client.filter_log_events(
                logGroupName=cloudwatch_log_group_name,
                nextToken=next_token,
                startTime=epoch_time - (1 * 60 * 60 * 1000),
                filterPattern='"' + contact_id + '"',
                endTime=epoch_time + (1 * 60 * 60 * 1000))
        else:
            response = cloudwatch_client.filter_log_events(
                logGroupName=cloudwatch_log_group_name,
                startTime=epoch_time - (1 * 60 * 60 * 1000),
                filterPattern='"' + contact_id + '"',
                endTime=epoch_time + (1 * 60 * 60 * 1000))

        # For each matching CloudWatch Log Entry, fetch the message part of the Conversation Logs.
        for event in response.get('events'):
            lex_logs.append(event.get('message'))

        # If there are more results, continue pagination.
        if response.get('nextToken') is None:
            more_results = False
        else:
            next_token = response.get('nextToken')

    if len(lex_logs) > 0:
        found_match = True

    if not found_match:
        print('[IN PROGRESS] Did not find any matching Lex Conversation Logs for contact ID ' + contact_id)

    return lex_logs, found_match


if __name__ == '__main__':
    sys.exit(main())
