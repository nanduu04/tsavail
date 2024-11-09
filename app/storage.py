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
        self.jfk_file = os.path.join(self.data_dir, 'jfk.json')
        self._initialize_jfk_file()
        self.ewr_file = os.path.join(self.data_dir, 'ewr.json')
        self._initialize_ewr_file()

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
        # lga_data['created_at'] = datetime.now().isoformat()

        existing_data.append(lga_data)
        self._save_lga_data(existing_data)
        return lga_data

    def get_lga_data(self):
        """Get all LGA data"""
        return self._load_lga_data()

    def _initialize_jfk_file(self):
        """Initialize jfk.json if it doesn't exist"""
        if not os.path.exists(self.jfk_file):
            self._save_jfk_data([])

    def _save_jfk_data(self, jfk_data):
        """Save JFK data to JSON file"""
        with open(self.jfk_file, 'w') as f:
            json.dump(jfk_data, f, indent=2)
    
    def _load_jfk_data(self):
        """Load JFK data from JSON file"""
        if os.path.exists(self.jfk_file):
            with open(self.jfk_file, 'r') as f:
                return json.load(f)
        return []
    
    def create_jfk_data(self, jfk_data):
        """Create a new JFK data entry"""
        existing_data = self._load_jfk_data()
        
        # Add metadata, if needed
        jfk_data['id'] = len(existing_data) + 1
        # jfk_data['created_at'] = datetime.now().isoformat()

        existing_data.append(jfk_data)
        self._save_jfk_data(existing_data)
        return jfk_data
    
    def get_jfk_data(self):
        """Get all JFK data"""
        return self._load_jfk_data()
    
    def _initialize_ewr_file(self):
        """Initialize ewr.json if it doesn't exist"""
        if not os.path.exists(self.ewr_file):
            self._save_ewr_data([])

    def _save_ewr_data(self, ewr_data):
        """Save EWR data to JSON file"""
        with open(self.ewr_file, 'w') as f:
            json.dump(ewr_data, f, indent=2)
    
    def _load_ewr_data(self):
        """Load EWR data from JSON file"""
        if os.path.exists(self.ewr_file):
            with open(self.ewr_file, 'r') as f:
                return json.load(f)
        return []
    
    def create_ewr_data(self, ewr_data):
        """Create a new EWR data entry"""
        existing_data = self._load_ewr_data()
        
        # Add metadata, if needed
        ewr_data['id'] = len(existing_data) + 1
        # ewr_data['created_at'] = datetime.now().isoformat()

        existing_data.append(ewr_data)
        self._save_ewr_data(existing_data)
        return ewr_data
    
    def get_ewr_data(self):
        """Get all EWR data"""
        return self._load_ewr_data()

