## Amazon Lex Bot Recommendation Integration

### Stitch Amazon Lex Conversation Logs with Amazon Connect Contact Lens Transcripts

Amazon Connect Contact Flows that interact with Amazon Lex bots do not have the Lex part of the interactions included as part of the transcripts written to S3 by Contact Lens. This script helps workaround that issue by stitching together Lex Conversation Logs with the Connect Contact Lens Transcripts so bot developers can submit holistic conversations as input for bot recommendations to be generated by Amazon Lex. The transcripts stitched together are uploaded back into S3.

#### Usage

```
python3 stitch_conversation_logs_and_contact_lens_transcripts.py --source my-contact-lens-bucket --access_key MYACCESSKEY --secret_key MYSECRETKEY --region us-west-2 --cloudwatch_log_group_name MyLexCloudWatchLogGroupName
```

1. **source**: This refers to the S3 bucket containing the original Contact Lens transcripts.
2. **access_key**: Access key of the IAM credentials to be used by this script. The credentials requires access to S3 (read/write) and CloudWatch (read).
3. **secret_key**: Secret key of the IAM credentials to be used by this script. The credentials requires access to S3 (read/write) and CloudWatch (read).
4. **region**: The region in which the S3 Bucket and CloudWatch Log Group are present.
5. **cloudwatch_log_group_name**: The CloudWatch Log Group containing the Amazon Lex Conversation Logs.

### Convert Transcribe Call Analytics Transcripts to Amazon Lex Bot Recommendation Input Format

This script helps convert output transcripts from Transcribe Call Analytics into the required input format for the Amazon Lex Bot Recommendation APIs.

#### Usage

```
python3 transcribe_call_analytics_to_lex_transcripts.py --source my-transcribe-call-analytics-bucket --access_key MYACCESSKEY --secret_key MYSECRETKEY --region us-west-2 --target my-lex-transcripts-bucket
```

1. **source**: This refers to the S3 bucket containing the original Transcribe Call Analytics transcripts.
2. **access_key**: Access key of the IAM credentials to be used by this script. The credentials requires access to S3 (read/write).
3. **secret_key**: Secret key of the IAM credentials to be used by this script. The credentials requires access to S3 (read/write).
4. **region**: The region in which the S3 Bucket and CloudWatch Log Group are present.
5. **target**: This refers to the S3 bucket that should contain the output transcripts in the Amazon Lex Input Format.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

