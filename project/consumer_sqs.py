import boto3
import json

from botocore.exceptions import ClientError

from app.models.settings import get_settings
from lib.logging import get_logger

logger = get_logger(__name__)
config = get_settings()


class ConsumerSQS():
    def __init__(self, conf):
        self.wait_time = 10
        self.max_number = 10
        self.loop_consumer = conf["loop_consumer"] if "loop_consumer" in conf and conf["loop_consumer"] else 5
        self.queue_url = conf["QUEUE_URL"]
        self.region_name = conf["AWS_REGION_FEDERATION"]
        self.aws_access_key_id = conf["AWS_ACCESS_KEY_FEDERATION"]
        self.aws_secret_access_key = conf["AWS_SECRET_FEDERATION"]


    def _sqs(self):
        return boto3.client(
            'sqs',
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )


    def _delete_messages(self, messages, sqs):
        """
            Delete a batch of messages from a queue in a single request.

            :param queue: The queue from which to delete the messages.
            :param messages: The list of messages to delete.
            :return: The response from SQS that contains the list of successful and failed
                    message deletions.
        """
        try:
            eliminated = []
            entries = [{
                'Id': str(ind),
                'ReceiptHandle': msg["ReceiptHandle"]
            } for ind, msg in enumerate(messages)]
            response = sqs.delete_message_batch(
                QueueUrl=self.queue_url, Entries=entries)
            if 'Successful' in response:
                for msg_meta in response['Successful']:
                    eliminated.append(json.loads(messages[int(msg_meta['Id'])]['Body']))
            if 'Failed' in response:
                for msg_meta in response['Failed']:
                    logger.warning("Could not delete %s",
                                   messages[int(msg_meta['Id'])])
            return eliminated
        except ClientError as error:
            logger.error("Couldn't delete messages from queue %s", error)


    def receive_messages(self):
        """
            Receive a batch of messages in a single request from an SQS queue.

            :param queue: The queue from which to receive messages.
            :param max_number: The maximum number of messages to receive. The actual number
                            of messages received might be less.
            :param wait_time: The maximum time to wait (in seconds) before returning. When
                            this number is greater than zero, long polling is used. This
                            can result in reduced costs and fewer false empty responses.
            :return: The list of Message objects received. These each contain the body
                    of the message and metadata and custom attributes.
        """
        try:
            messages = []
            sqs = self._sqs()
            for i in range(self.loop_consumer):
                message = sqs.receive_message(
                    QueueUrl=self.queue_url,
                    MessageAttributeNames=['All'],
                    MaxNumberOfMessages=self.max_number,
                    WaitTimeSeconds=self.wait_time,
                )
                if message:
                    if 'Messages' in message:
                        messages += self._delete_messages(
                            message['Messages'], sqs)
                    else:
                        break
                else:
                    break
        except ClientError as error:
            logger.error(f"Couldn't receive messages from queue: {error}")
        except Exception as err:
            logger.error(f"Error while receiving messages: {err}")
        else:
            return messages


class SendMessageSQS():
    def __init__(self, conf):
        self.queue_url = conf["QUEUE_URL"]
        self.region_name = conf["AWS_REGION_FEDERATION"]
        self.aws_access_key_id = conf["AWS_ACCESS_KEY_FEDERATION"]
        self.aws_secret_access_key = conf["AWS_SECRET_FEDERATION"]


    def _sqs(self):
        return boto3.client(
            'sqs',
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )


    def send_messages(self, messages):
        try:
            sqs = self._sqs()
            for message in messages:
                response = sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(message)
                )
            logger.info(f"Response to send message: {response}")
            return True
        except Exception as err:
            logger.error(f'Error to send message: {err}')
