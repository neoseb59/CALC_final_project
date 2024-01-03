import asyncio
import json
from typing import MutableMapping
import uuid
import os

from aio_pika import DeliveryMode, Message, connect
from aio_pika.abc import AbstractConnection
from aio_pika.abc import AbstractChannel
from aio_pika.abc import AbstractQueue
from aio_pika.abc import AbstractIncomingMessage


class AsyncSummarizerClient:
    connection: AbstractConnection
    channel: AbstractChannel
    callback_queue: AbstractQueue

    def __init__(self) -> None:
        self.futures: MutableMapping[str, asyncio.Future] = {}

    async def connect(self) -> "AsyncSummarizerClient":
        host = os.environ["HOST"]
        self.connection = await connect(f"amqp://guest:guest@{host}/")
        self.channel = await self.connection.channel()
        self.callback_queue = await self.channel.declare_queue(exclusive=True)
        await self.callback_queue.consume(self.on_response, no_ack=True)

        return self

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        if message.correlation_id is None:
            print(f"Bad message {message!r}")
            return

        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body.decode())

    async def call_url(self, url: str, nb_sentences: int, language: str) -> str:
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        self.futures[correlation_id] = future

        message_body = {
            "url": url,
            "nb_sentences": nb_sentences,
            "language": language,
        }

        message = Message(
            json.dumps(message_body).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            correlation_id=correlation_id,
            reply_to=self.callback_queue.name,
            content_encoding="utf-8",
            content_type="application/json",
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key="task_queue_url",
        )

        return str(await future)

    async def call_text(self, text: str, nb_sentences: int, language: str) -> str:
        correlation_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        self.futures[correlation_id] = future

        message_body = {
            "text": text,
            "nb_sentences": nb_sentences,
            "language": language,
        }

        message = Message(
            json.dumps(message_body).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            correlation_id=correlation_id,
            reply_to=self.callback_queue.name,
            content_encoding="utf-8",
            content_type="application/json",
        )

        await self.channel.default_exchange.publish(
            message,
            routing_key="task_queue_text",
        )

        return str(await future)
