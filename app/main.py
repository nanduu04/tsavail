from fastapi import FastAPI, HTTPException
from .scrapers.jfk import JFKScraper
from .models.wait_times import SecurityWaitTime, ErrorResponse
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="JFK Wait Times API",
    description="API for retrieving JFK Airport TSA wait times",
    version="1.0.0"
)

@app.get(
    "/api/v1/jfk/wait-times",
    response_model=List[SecurityWaitTime],
    responses={500: {"model": ErrorResponse}}
)
async def get_jfk_wait_times():
    """Get current JFK TSA wait times for all terminals"""
    try:
        with JFKScraper(headless=True) as scraper:
            data = scraper.scrape()
            if not data:
                raise HTTPException(status_code=500, detail="Failed to fetch wait times")
            return data
    except Exception as e:
        logger.error(f"Error fetching JFK wait times: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}