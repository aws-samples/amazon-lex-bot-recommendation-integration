## Amazon Lex bot recommendation integration

### Stitch Amazon Lex conversation logs with Amazon Connect Contact Lens transcripts

Amazon Connect Contact Flows that interact with Amazon Lex bots do not have the Amazon Lex part of the interactions included as part of the transcripts written to Aamzon S3 by Contact Lens. This script helps stich together Amazon Lex Conversation Logs with the Amazon Connect Contact Lens Transcripts so bot developers can submit holistic conversations as input for bot recommendations to be generated by Amazon Lex. The transcripts stitched together are uploaded back into Amazon S3.

#### Usage

```
python3 stitch_conversation_logs_and_contact_lens_transcripts.py --source my-contact-lens-bucket --access_key MYACCESSKEY --secret_key MYSECRETKEY --region us-west-2 --cloudwatch_log_group_name MyLexCloudWatchLogGroupName
```

1. **source**: This refers to the Amazon S3 bucket containing the original Contact Lens transcripts.
2. **access_key**: Access key of the AWS IAM credentials to be used by this script. The credentials require access to Amazon S3 (read/write) and Amazon CloudWatch (read).
3. **secret_key**: Secret key of the AWS IAM credentials to be used by this script. The credentials require access to Amazon S3 (read/write) and Amazon CloudWatch (read).
4. **region**: The region in which the Amazon S3 Bucket and Amazon CloudWatch Log Group are present.
5. **cloudwatch_log_group_name**: The Amazon CloudWatch Log Group containing the Amazon Lex Conversation Logs.

### Convert Amazon Transcribe Call Analytics transcripts to Amazon Lex bot recommendation input format

This script helps convert output transcripts from Amazon Transcribe Call Analytics into the required input format for the Amazon Lex Bot Recommendation APIs.

#### Usage

```
python3 transcribe_call_analytics_to_lex_transcripts.py --source my-transcribe-call-analytics-bucket --access_key MYACCESSKEY --secret_key MYSECRETKEY --region us-west-2 --target my-lex-transcripts-bucket
```

1. **source**: The Amazon S3 bucket that contains the original Amazon Transcribe Call Analytics transcripts.
2. **access_key**: Access key of the AWS IAM credentials used by this script. The credentials require read/write access to Amazon S3.
3. **secret_key**: Secret key of the AWS IAM credentials used by this script. The credentials require read/write access to Amazon S3.
4. **region**: The Region where the Amazon S3 buckets are located.
5. **target**: The Amazon S3 bucket where output transcripts in Amazon Lex input format are stored.

### Convert Amazon Connect Chat transcripts to Amazon Lex bot recommendation input format

This script helps convert output transcripts from Amazon Connect Chat into the required input format for the Amazon Lex Bot Recommendation APIs.

#### Usage

```
python3 connect_chat_to_lex_transcripts.py --source my-connect-chat-bucket --access_key MYACCESSKEY --secret_key MYSECRETKEY --region us-west-2 --target my-lex-transcripts-bucket
```

1. **source**: The Amazon S3 bucket that contains the original Amazon Connect Chat transcripts.
2. **access_key**: Access key of the AWS IAM credentials used by this script. The credentials require read/write access to Amazon S3.
3. **secret_key**: Secret key of the AWS IAM credentials used by this script. The credentials require read/write access to Amazon S3.
4. **region**: The Region where the Amazon S3 buckets are located.
5. **target**: The Amazon S3 bucket where output transcripts in Amazon Lex input format are stored.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

