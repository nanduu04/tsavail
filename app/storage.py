from pymongo import MongoClient
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv
import logging
from abc import ABC, abstractmethod

# Load environment variables
load_dotenv()

class BaseAirportStorage(ABC):
    """Base class for airport-specific MongoDB storage"""
    
    def __init__(self, airport_code):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        self.airport_code = airport_code.lower()
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = f"{self.airport_code}_airport"
        
        # Initialize timezone
        self.timezone = pytz.timezone('America/New_York')
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self.security_collection = self.db['security_wait_times']
            self.walk_collection = self.db['walk_times']
            
            # Create indexes for better query performance
            self._create_indexes()
            
            logging.info(f"Successfully connected to MongoDB database: {self.database_name}")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def _create_indexes(self):
        """Create indexes for collections"""
        self.security_collection.create_index("timestamp")
        self.security_collection.create_index("terminal")
        self.walk_collection.create_index("timestamp")
        self.walk_collection.create_index("terminal")
        self.walk_collection.create_index("gate")

    def _get_current_et_time(self) -> datetime:
        """Get current time in Eastern timezone"""
        return datetime.now(self.timezone)

    def _add_metadata(self, data):
        """Add common metadata to documents with Eastern timezone"""
        current_time = self._get_current_et_time()
        
        if 'timestamp' not in data:
            data['timestamp'] = current_time
        elif isinstance(data['timestamp'], str):
            # If timestamp is provided as string, parse and localize it
            try:
                naive_dt = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                if naive_dt.tzinfo is None:
                    data['timestamp'] = self.timezone.localize(naive_dt)
                else:
                    # If timestamp has timezone info, convert to ET
                    data['timestamp'] = naive_dt.astimezone(self.timezone)
            except ValueError:
                data['timestamp'] = current_time
        
        # Set created_at and updated_at in ET
        data['created_at'] = current_time
        data['updated_at'] = current_time
        data['airport'] = self.airport_code
        
        return data

    def create_security_times(self, security_data):
        """Create new security wait time entries"""
        try:
            if isinstance(security_data, list):
                documents = [self._add_metadata(data.copy()) for data in security_data]
                result = self.security_collection.insert_many(documents)
                logging.info(f"Inserted {len(result.inserted_ids)} {self.airport_code} security wait time records")
                return documents
            else:
                document = self._add_metadata(security_data.copy())
                result = self.security_collection.insert_one(document)
                logging.info(f"Inserted {self.airport_code} security wait time with ID: {result.inserted_id}")
                return document
        except Exception as e:
            logging.error(f"Error creating {self.airport_code} security wait time data: {str(e)}")
            raise

    def create_walk_times(self, walk_data):
        """Create new walk time entries"""
        try:
            if isinstance(walk_data, list):
                documents = [self._add_metadata(data.copy()) for data in walk_data]
                result = self.walk_collection.insert_many(documents)
                logging.info(f"Inserted {len(result.inserted_ids)} {self.airport_code} walk time records")
                return documents
            else:
                document = self._add_metadata(walk_data.copy())
                result = self.walk_collection.insert_one(document)
                logging.info(f"Inserted {self.airport_code} walk time with ID: {result.inserted_id}")
                return document
        except Exception as e:
            logging.error(f"Error creating {self.airport_code} walk time data: {str(e)}")
            raise

    def get_security_times(self, limit=100, skip=0):
        """Get security wait times with pagination"""
        try:
            logging.info(f"Fetching security times for {self.airport_code}")
            logging.info(f"Parameters: limit={limit}, skip={skip}")
            
            cursor = self.security_collection.find({}) \
                        .sort('timestamp', -1) \
                        .skip(skip) \
                        .limit(limit)
            
            result = list(cursor)
            logging.info(f"Found {len(result)} security time records")
            return result
        except Exception as e:
            logging.error(f"Error retrieving {self.airport_code} security wait times: {str(e)}")
            raise

    def get_walk_times(self, limit=100, skip=0):
        """Get walk times with pagination"""
        try:
            logging.info(f"Fetching walk times for {self.airport_code}")
            logging.info(f"Parameters: limit={limit}, skip={skip}")
            
            cursor = self.walk_collection.find({}) \
                        .sort('timestamp', -1) \
                        .skip(skip) \
                        .limit(limit)
            
            result = list(cursor)
            logging.info(f"Found {len(result)} walk time records")
            return result
        except Exception as e:
            logging.error(f"Error retrieving {self.airport_code} walk times: {str(e)}")
            raise

    def get_latest_data(self, data_type='all'):
        """Get the most recent data for security times, walk times, or both"""
        try:
            result = {}
            if data_type in ['all', 'security']:
                result['security'] = self.security_collection.find_one(
                    {}, sort=[('timestamp', -1)]
                )
            if data_type in ['all', 'walk']:
                result['walk'] = self.walk_collection.find_one(
                    {}, sort=[('timestamp', -1)]
                )
            return result if data_type == 'all' else result.get(data_type)
        except Exception as e:
            logging.error(f"Error retrieving {self.airport_code} latest data: {str(e)}")
            raise

    def get_data_by_date_range(self, data_type, start_date, end_date):
        """Get data within a date range using Eastern timezone"""
        try:
            # Convert dates to Eastern timezone if they're not already
            if start_date.tzinfo is None:
                start_date = self.timezone.localize(start_date)
            else:
                start_date = start_date.astimezone(self.timezone)
                
            if end_date.tzinfo is None:
                end_date = self.timezone.localize(end_date)
            else:
                end_date = end_date.astimezone(self.timezone)
            
            collection = self.security_collection if data_type == 'security' else self.walk_collection
            query = {
                'timestamp': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }
            cursor = collection.find(query).sort('timestamp', -1)
            return list(cursor)
        except Exception as e:
            logging.error(f"Error retrieving {self.airport_code} data by date range: {str(e)}")
            raise

    def __del__(self):
        """Cleanup method to close MongoDB connection"""
        try:
            self.client.close()
            logging.info(f"Closed {self.airport_code} MongoDB connection")
        except Exception as e:
            logging.error(f"Error closing {self.airport_code} MongoDB connection: {str(e)}")

# Airport-specific storage classes
class LGAStorage(BaseAirportStorage):
    def __init__(self):
        super().__init__('lga')

class JFKStorage(BaseAirportStorage):
    def __init__(self):
        super().__init__('jfk')

class EWRStorage(BaseAirportStorage):
    def __init__(self):
        super().__init__('ewr')