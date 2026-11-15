import logging

from fastapi import FastAPI

from app.schemas import PostingRequest, PostingResponse
from app.services import posting_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Automated Multi-Platform Posting System",
    description="Publishes one short message with a CTA link to several platforms via their APIs.",
    version="1.0.0",
)


@app.post("/posting", response_model=PostingResponse, summary="Publish a message to all platforms")
async def posting(request: PostingRequest) -> PostingResponse:
    return await posting_service.publish(request.message)
