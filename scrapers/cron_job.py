import schedule
import time
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from tsa_scraper import TSAWaitTimesManager

# Set up logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"tsa_scraper_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_scraper():
    try:
        logger.info("Starting TSA wait times scrape")
        start_time = time.time()
        
        manager = TSAWaitTimesManager()
        await manager.run()
        
        duration = time.time() - start_time
        logger.info(f"✅ Scrape completed in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"❌ Scrape failed: {str(e)}")

def schedule_scraper():
    """Helper function to run the async scraper in the event loop"""
    asyncio.run(run_scraper())

async def main():
    # Run immediately on startup
    await run_scraper()
    
    # Schedule to run every 30 minutes
    schedule.every(30).minutes.do(schedule_scraper)
    
    logger.info("🕒 Scheduler started - running every 30 minutes")
    
    while True:
        try:
            schedule.run_pending()
            await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            await asyncio.sleep(60)  # Wait a minute before retrying

if __name__ == "__main__":
    asyncio.run(main())