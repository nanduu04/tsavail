import json
import os
from datetime import datetime

class JsonStorage:
    def __init__(self):
        # Create data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.lga_file = os.path.join(self.data_dir, 'lga.json')
        self._initialize_lga_file()

    def _initialize_lga_file(self):
        """Initialize lga.json if it doesn't exist"""
        if not os.path.exists(self.lga_file):
            self._save_lga_data([])

    def _save_lga_data(self, lga_data):
        """Save LGA data to JSON file"""
        with open(self.lga_file, 'w') as f:
            json.dump(lga_data, f, indent=2)

    def _load_lga_data(self):
        """Load LGA data from JSON file"""
        if os.path.exists(self.lga_file):
            with open(self.lga_file, 'r') as f:
                return json.load(f)
        return []

    def create_lga_data(self, lga_data):
        """Create a new LGA data entry"""
        existing_data = self._load_lga_data()
        
        # Add metadata, if needed
        lga_data['id'] = len(existing_data) + 1
        lga_data['created_at'] = datetime.now().isoformat()

        existing_data.append(lga_data)
        self._save_lga_data(existing_data)
        return lga_data

    def get_lga_data(self):
        """Get all LGA data"""
        return self._load_lga_data()