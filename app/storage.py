from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class MongoDBStorage:
    def __init__(self):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Get MongoDB connection details from environment variables
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = os.getenv('DATABASE_NAME', 'airport_timing')
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client[self.database_name]
            
            # Initialize collections
            self.lga_collection = self.db['lga_data']
            self.jfk_collection = self.db['jfk_data']
            self.ewr_collection = self.db['ewr_data']
            
            # Create indexes for better query performance
            self.lga_collection.create_index("created_at")
            self.jfk_collection.create_index("created_at")
            self.ewr_collection.create_index("created_at")
            
            logging.info(f"Successfully connected to MongoDB database: {self.database_name}")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def _add_metadata(self, data):
        """Add common metadata to documents"""
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        return data

    # LGA Methods
    def create_lga_data(self, lga_data):
        """Create a new LGA data entry"""
        try:
            lga_data = self._add_metadata(lga_data)
            result = self.lga_collection.insert_one(lga_data)
            logging.info(f"Inserted LGA data with ID: {result.inserted_id}")
            return lga_data
        except Exception as e:
            logging.error(f"Error creating LGA data: {str(e)}")
            raise

    def get_lga_data(self, limit=100, skip=0):
        """Get LGA data with pagination"""
        try:
            cursor = self.lga_collection.find({}) \
                        .sort('created_at', -1) \
                        .skip(skip) \
                        .limit(limit)
            return list(cursor)
        except Exception as e:
            logging.error(f"Error retrieving LGA data: {str(e)}")
            raise

    # JFK Methods
    def create_jfk_data(self, jfk_data):
        """Create a new JFK data entry"""
        try:
            jfk_data = self._add_metadata(jfk_data)
            result = self.jfk_collection.insert_one(jfk_data)
            logging.info(f"Inserted JFK data with ID: {result.inserted_id}")
            return jfk_data
        except Exception as e:
            logging.error(f"Error creating JFK data: {str(e)}")
            raise

    def get_jfk_data(self, limit=100, skip=0):
        """Get JFK data with pagination"""
        try:
            cursor = self.jfk_collection.find({}) \
                        .sort('created_at', -1) \
                        .skip(skip) \
                        .limit(limit)
            return list(cursor)
        except Exception as e:
            logging.error(f"Error retrieving JFK data: {str(e)}")
            raise

    # EWR Methods
    def create_ewr_data(self, ewr_data):
        """Create a new EWR data entry"""
        try:
            ewr_data = self._add_metadata(ewr_data)
            result = self.ewr_collection.insert_one(ewr_data)
            logging.info(f"Inserted EWR data with ID: {result.inserted_id}")
            return ewr_data
        except Exception as e:
            logging.error(f"Error creating EWR data: {str(e)}")
            raise

    def get_ewr_data(self, limit=100, skip=0):
        """Get EWR data with pagination"""
        try:
            cursor = self.ewr_collection.find({}) \
                        .sort('created_at', -1) \
                        .skip(skip) \
                        .limit(limit)
            return list(cursor)
        except Exception as e:
            logging.error(f"Error retrieving EWR data: {str(e)}")
            raise

    # Additional utility methods
    def get_latest_data(self, airport):
        """Get the most recent data for a specific airport"""
        try:
            collection = getattr(self, f"{airport.lower()}_collection")
            result = collection.find_one({}, sort=[('created_at', -1)])
            return result
        except Exception as e:
            logging.error(f"Error retrieving latest {airport} data: {str(e)}")
            raise

    def get_data_by_date_range(self, airport, start_date, end_date):
        """Get data for a specific airport within a date range"""
        try:
            collection = getattr(self, f"{airport.lower()}_collection")
            query = {
                'created_at': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            }
            cursor = collection.find(query).sort('created_at', -1)
            return list(cursor)
        except Exception as e:
            logging.error(f"Error retrieving {airport} data by date range: {str(e)}")
            raise

    def __del__(self):
        """Cleanup method to close MongoDB connection"""
        try:
            self.client.close()
            logging.info("MongoDB connection closed")
        except Exception as e:
            logging.error(f"Error closing MongoDB connection: {str(e)}")