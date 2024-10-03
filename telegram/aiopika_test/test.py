import asyncio
import logging
from types import SimpleNamespace

import aio_pika


config = SimpleNamespace()
config.AMQP_HOST = "localhost"
config.AMQP_PORT = 5672
config.AMQP_USER = "guest"
config.AMQP_PASS = "guest"
config.TASK_QUEUE = "tasks"
config.MAX_MESSAGES = 12
config.MAX_PROCESSING_TIME_SECONDS = 10

async def on_message2(message):
    async with message.process():
        logging.info("New message2: %s", message.body)
        await asyncio.sleep(5)

async def on_message(message: aio_pika.abc.AbstractIncomingMessage):
    async with message.process():
        logging.info("New message: %s", message.body)
        await asyncio.sleep(5)


async def subscriber() -> None:
    logging.info(
        "Establishing connection to AMQP server: %s:%s",
        config.AMQP_HOST, config.AMQP_PORT
    )
    connection = await aio_pika.connect(
        host=config.AMQP_HOST,
        port=config.AMQP_PORT,
        login=config.AMQP_USER,
        password=config.AMQP_PASS,
    )

    async with connection:
        channel = await connection.channel()
        logging.info(
            "Setting channel prefetch count to %d with max processing time %d",
            config.MAX_MESSAGES, config.MAX_PROCESSING_TIME_SECONDS
        )

        # MAX_MESSAGES is 12
        await channel.set_qos(prefetch_count=config.MAX_MESSAGES)

        logging.info("Subscribing to the queue: %s", config.TASK_QUEUE)

        # The reason for your problem is that you are using the get_queue
        # method, the behavior of which you don't understand.
        # It is worth noting that it is not very well described in the
        # documentation, so there is nothing to blame you.
        # In short, my advice is to avoid using this method unless you 
        # **really need it**.
        queue = await channel.declare_queue(config.TASK_QUEUE)
        queue2 = await channel.declare_queue('fakingshit')
        logging.critical("Consume done")

        await queue.consume(
            callback=on_message,
            timeout=config.MAX_PROCESSING_TIME_SECONDS,
            no_ack=True
        )
        await queue2.consume(callback=on_message2, no_ack=True)

        logging.critical("Stopped listening for messages")
        await asyncio.Future()


async def publisher() -> None:
    connection = await aio_pika.connect(
        host=config.AMQP_HOST,
        port=config.AMQP_PORT,
        login=config.AMQP_USER,
        password=config.AMQP_PASS,
    )

    logging.info("Start publishing")

    async with connection:
        channel = await connection.channel()
        for i in range(24):
            await channel.default_exchange.publish(
                aio_pika.Message(str(i).encode()),
                routing_key='fakingshit'
            )
        logging.info("Publish done")


async def main():
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(subscriber(), publisher())


if __name__ == "__main__":
    asyncio.run(main())