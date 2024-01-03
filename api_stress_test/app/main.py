import asyncio
import aiohttp
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import uvicorn


app = FastAPI(
    title="Stress test",
    version="1.0.0",
)


@app.get(
    "/urls",
    responses={
        status.HTTP_200_OK: {
            "description": "Return the requested summary of the urls content",
        }
    },
)
async def summarize_page_content_stresstest(
    content_url: str,
    nb_sentences: int = 5,
    language: str = "french",
    nb_send_url: int = 10,
):
    async def fetch(url, session):
        async with session.get(
            url,
            ssl=False,
            params={
                "url": content_url,
                "nb_sentences": nb_sentences,
                "language": language,
            },
        ) as response:
            status = response.status
            data = await response.json()
            data_length = len(data)
            return {"url": url, "status": status, "data_length": data_length}

    # async function to make multiple requests
    async def fetch_all(urls):
        async with aiohttp.ClientSession() as session:
            tasks = [fetch(url, session) for url in urls]
            results = await asyncio.gather(*tasks)
            return results

    # run the async functions
    return await fetch_all(["http://fastapi:80/url" for _ in range(nb_send_url)])


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
