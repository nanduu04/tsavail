from typing import List
import sys
import logging
from pathlib import Path
import schedule
import time
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Import scrapers from both files
from storage import EWRStorage, LGAStorage, JFKStorage
from ewr_local import SecurityWaitTimeScraper, WalkTimeScraper
from jfk_local import JFKSecurityWaitTimeScraper, JFKWalkTimeScraper

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging with rotation
log_file = Path("logs/combined_airport_scraper.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
    ]
)
logger = logging.getLogger(__name__)

class CombinedAirportScheduler:
    def __init__(self, interval_minutes: int = 6):
        self.interval = interval_minutes
        self.is_running = False
        self.last_run = None
        
        # Initialize storage for all airports
        self.ewr_storage = EWRStorage()
        self.lga_storage = LGAStorage()
        self.jfk_storage = JFKStorage()
    
    def _run_ewr_scraper(self):
        """Run EWR scraping tasks"""
        try:
            logger.info("Starting EWR scraping tasks...")
            
            with SecurityWaitTimeScraper('https://www.newarkairport.com/', headless=True) as security_scraper:
                security_data = security_scraper.scrape()
                if security_data:
                    logger.info("Saving EWR security wait time data...")
                    self.ewr_storage.create_security_times(security_data)
            
            with WalkTimeScraper('https://www.newarkairport.com/', headless=True) as walk_scraper:
                walk_data = walk_scraper.scrape()
                if walk_data:
                    logger.info("Saving EWR walk time data...")
                    self.ewr_storage.create_walk_times(walk_data)
                    
        except Exception as e:
            logger.error(f"Error in EWR scraping task: {str(e)}", exc_info=True)
    
    def _run_lga_scraper(self):
        """Run LGA scraping tasks"""
        try:
            logger.info("Starting LGA scraping tasks...")
            
            with SecurityWaitTimeScraper('https://www.laguardiaairport.com/', headless=True) as security_scraper:
                security_data = security_scraper.scrape()
                if security_data:
                    logger.info("Saving LGA security wait time data...")
                    self.lga_storage.create_security_times(security_data)
            
            with WalkTimeScraper('https://www.laguardiaairport.com/', headless=True) as walk_scraper:
                walk_data = walk_scraper.scrape()
                if walk_data:
                    logger.info("Saving LGA walk time data...")
                    self.lga_storage.create_walk_times(walk_data)
                    
        except Exception as e:
            logger.error(f"Error in LGA scraping task: {str(e)}", exc_info=True)
    
    def _run_jfk_scraper(self):
        """Run JFK scraping tasks"""
        try:
            logger.info("Starting JFK scraping tasks...")
            
            with JFKSecurityWaitTimeScraper(headless=True) as security_scraper:
                security_data = security_scraper.scrape()
                if security_data:
                    logger.info("Saving JFK security wait time data...")
                    self.jfk_storage.create_security_times(security_data)
            
            with JFKWalkTimeScraper(headless=True) as walk_scraper:
                walk_data = walk_scraper.scrape()
                if walk_data:
                    logger.info("Saving JFK walk time data...")
                    self.jfk_storage.create_walk_times(walk_data)
                    
        except Exception as e:
            logger.error(f"Error in JFK scraping task: {str(e)}", exc_info=True)
    
    def _run_task(self):
        """Run all scraping tasks"""
        try:
            logger.info("Starting combined airport scraping tasks...")
            
            # Run all scrapers sequentially
            self._run_ewr_scraper()
            self._run_lga_scraper()
            self._run_jfk_scraper()
            
            self.last_run = datetime.now()
            logger.info("All airport scraping tasks completed successfully")
            
        except Exception as e:
            logger.error(f"Combined task execution failed: {str(e)}", exc_info=True)
    
    def start(self):
        """Start the scheduler"""
        try:
            schedule.every(self.interval).minutes.do(self._run_task)
            self.is_running = True
            
            logger.info(f"Combined scheduler started. Running all airport scrapers every {self.interval} minutes...")
            
            # Run immediately on start
            self._run_task()
            
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the scheduler gracefully"""
        self.is_running = False
        logger.info("Combined scheduler stopping...")

def main():
    """Main entry point for the application"""
    try:
        scheduler = CombinedAirportScheduler(interval_minutes=6)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()