from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals
import asyncio
import json
import os

from aio_pika import DeliveryMode, Exchange, Message, connect
from aio_pika.abc import AbstractIncomingMessage

from sumy.parsers.html import HtmlParser
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


async def on_message_url(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        message_json = json.loads(message.body.decode())
        print(f" [x] Received message {message_json}")
        parser = HtmlParser.from_url(
            message_json["url"], Tokenizer(message_json["language"])
        )

        stemmer = Stemmer(message_json["language"])

        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(message_json["language"])

        response = " ".join(
            str(sentence)
            for sentence in summarizer(parser.document, message_json["nb_sentences"])
        ).encode()

        # Send result back to API
        host = os.environ["HOST"]
        connection = await connect(f"amqp://guest:guest@{host}/")

        async with connection:
            # Creating a channel
            channel = await connection.channel()

            # Sending the message
            await channel.default_exchange.publish(
                Message(
                    body=response,
                    correlation_id=message.correlation_id,
                ),
                routing_key=message.reply_to,
            )

        print("Request complete")


async def main() -> None:
    # Perform connection
    host = os.environ["HOST"]
    connection = await connect(f"amqp://guest:guest@{host}/")

    async with connection:
        # Creating a channel
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declaring queue
        queue_url = await channel.declare_queue(
            "task_queue_url",
            durable=True,
        )

        # Start listening the queue with name 'task_queue'
        await queue_url.consume(on_message_url)

        print(" [*] Waiting for messages. To exit press CTRL+C")
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
