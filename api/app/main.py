from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import uvicorn

from AsyncSummarizerClient import AsyncSummarizerClient


app = FastAPI(
    title="Asynchronous tasks processing with Celery and RabbitMQ, and non asunc one using rabbitmq",
    description="Sample FastAPI Application to demonstrate Event "
    "driven architecture with Celery and RabbitMQ"
    " and non async one using rabbitmq",
    version="1.0.0",
)


@app.get(
    "/url",
    responses={
        status.HTTP_200_OK: {
            "description": "Return the requested summary of the url content",
        }
    },
)
async def summarize_page_content(
    url: str, nb_sentences: int = 5, language: str = "french"
):
    summarizer = await AsyncSummarizerClient().connect()
    print(" [x] Requesting summarizer")
    return await summarizer.call_url(url, nb_sentences, language)


@app.get(
    "/text",
    responses={
        status.HTTP_200_OK: {
            "description": "Return the requested summary of the text",
        }
    },
)
async def summarize_page_content(
    text: str, nb_sentences: int = 5, language: str = "french"
):
    summarizer = await AsyncSummarizerClient().connect()
    print(" [x] Requesting summarizer")
    return await summarizer.call_text(text, nb_sentences, language)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
