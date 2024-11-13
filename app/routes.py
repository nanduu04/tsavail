from flask import Blueprint, jsonify, request, render_template
from app.storage import LGAStorage, JFKStorage, EWRStorage
from bson import json_util, Timestamp
import json
import logging
from datetime import datetime
from dateutil.parser import parse
from flask import Blueprint, jsonify, request, render_template
import humanize
import pytz
from typing import Union

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
ET_TZ = pytz.timezone('America/New_York')

main = Blueprint('main', __name__)

# Initialize storage instances for each airport
lga_storage = LGAStorage()
jfk_storage = JFKStorage()
ewr_storage = EWRStorage()
def init_jinja_filters(app):
    """Initialize custom Jinja filters"""
    
    @app.template_filter('timesince')
    def timesince_filter(value: Union[str, datetime, dict, None]) -> str:
        """
        Convert MongoDB ISODate timestamp to "time ago" format in Eastern Time
        """
        if not value:
            return 'N/A'
            
        try:
            # Debug logging
            logger.debug(f"Timesince input value: {value}")
            logger.debug(f"Timesince input type: {type(value)}")
            
            # Parse the timestamp based on its type
            if isinstance(value, str):
                # Handle ISO format string
                dt = parse(value.replace('Z', '+00:00'))
            elif isinstance(value, dict):
                # Handle MongoDB ISODate format
                if '$date' in value:
                    # If it's in milliseconds
                    if isinstance(value['$date'], int):
                        dt = datetime.fromtimestamp(value['$date'] / 1000, pytz.UTC)
                    else:
                        # If it's an ISO string
                        dt = parse(value['$date'])
            elif isinstance(value, datetime):
                dt = value
            else:
                logger.error(f"Unsupported timestamp format: {type(value)}")
                return 'N/A'
            
            # Ensure timezone awareness
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            
            # Convert to Eastern Time
            et_tz = pytz.timezone('America/New_York')
            et_time = dt.astimezone(et_tz)
            
            # Get current time in ET
            now = datetime.now(et_tz)
            
            # Calculate time difference
            diff = now - et_time
            seconds = diff.total_seconds()
            
            # Format the time difference
            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
                
        except Exception as e:
            logger.error(f"Error in timesince filter: {e}")
            logger.error(f"Problem value: {value}")
            logger.error(f"Value type: {type(value)}")
            import traceback
            logger.error(traceback.format_exc())
            return 'N/A'
    
    @app.template_filter('format_et_time')
    def format_et_time(value: Union[str, datetime, dict, None]) -> str:
        """
        Format MongoDB ISODate timestamp to ET timezone with AM/PM
        """
        if not value:
            return 'N/A'
            
        try:
            # Parse the timestamp based on its type
            if isinstance(value, str):
                dt = parse(value.replace('Z', '+00:00'))
            elif isinstance(value, dict):
                if '$date' in value:
                    if isinstance(value['$date'], int):
                        dt = datetime.fromtimestamp(value['$date'] / 1000, pytz.UTC)
                    else:
                        dt = parse(value['$date'])
            elif isinstance(value, datetime):
                dt = value
            else:
                return 'N/A'
            
            # Ensure timezone awareness
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            
            # Convert to Eastern Time
            et_tz = pytz.timezone('America/New_York')
            et_time = dt.astimezone(et_tz)
            
            # Format the time with AM/PM
            return et_time.strftime("%I:%M %p ET")
            
        except Exception as e:
            logger.error(f"Error in format_et_time filter: {e}")
            return 'N/A'

def parse_mongo_data(data):
    """
    Convert MongoDB data to JSON-serializable format while preserving datetime information
    """
    try:
        # If it's a list, process each item
        if isinstance(data, list):
            return [parse_mongo_data(item) for item in data]
        
        # If it's a dictionary, process each value
        if isinstance(data, dict):
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    # Convert datetime to dict format
                    processed_data[key] = {
                        "$date": value.astimezone(pytz.UTC).isoformat()
                    }
                else:
                    processed_data[key] = parse_mongo_data(value)
            return processed_data
            
        # Return other types as is
        return data
    except Exception as e:
        logger.error(f"Error in parse_mongo_data: {e}")
        return data

def get_paginated_data(storage, data_type, terminal=None, page=1, per_page=4):
    """Helper function to get paginated data with terminal filtering"""
    try:
        skip = (page - 1) * per_page
        
        # Create query filter
        query_filter = {}
        if terminal and terminal != 'all':
            terminal_query = f"Terminal {terminal}"
            logger.info(f"Looking for terminal: {terminal_query}")
            query_filter['terminal'] = terminal_query
            
        logger.info(f"Query filter: {query_filter}")
        
        # Get data based on type
        if data_type == 'security':
            cursor = storage.security_collection.find(query_filter)
            total_count = storage.security_collection.count_documents(query_filter)
        else:
            cursor = storage.walk_collection.find(query_filter)
            total_count = storage.walk_collection.count_documents(query_filter)
        
        # Sort and paginate
        data = list(cursor.sort('timestamp', -1).skip(skip).limit(per_page))
        
        # Convert any UTC timestamps to ET
        for doc in data:
            if 'timestamp' in doc:
                timestamp = doc['timestamp']
                if isinstance(timestamp, datetime):
                    if timestamp.tzinfo is None:
                        timestamp = pytz.UTC.localize(timestamp)
                    doc['timestamp'] = timestamp.astimezone(ET_TZ)
        
        logger.info(f"Found {total_count} total documents, returning {len(data)} for page {page}")
        return data, total_count
    except Exception as e:
        logger.error(f"Error in get_paginated_data: {str(e)}", exc_info=True)
        raise

# def parse_mongo_data(data):
#     """Convert MongoDB data to JSON-serializable format"""
#     return json.loads(json_util.dumps(data))
    
@main.route('/')
def index():
    """Main dashboard page showing latest data"""
    return wait_times()

@main.route('/wait-times')
def wait_times():
    """Security wait times dashboard"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 4))  # Changed default to 4
        terminal = request.args.get('terminal', 'all')  # Default to 'all'

        # Get security data for each airport
        jfk_data, jfk_count = get_paginated_data(jfk_storage, 'security', terminal, page, per_page)
        lga_data, lga_count = get_paginated_data(lga_storage, 'security', terminal, page, per_page)
        ewr_data, ewr_count = get_paginated_data(ewr_storage, 'security', terminal, page, per_page)

        return render_template('wait_times.html',
                             jfk_data=parse_mongo_data(jfk_data),
                             lga_data=parse_mongo_data(lga_data),
                             ewr_data=parse_mongo_data(ewr_data),
                             page=page,
                             per_page=per_page,
                             total_pages=max(1, (max(jfk_count, lga_count, ewr_count) + per_page - 1) // per_page),
                             selected_terminal=terminal)
    except Exception as e:
        logger.error(f"Error in wait_times: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@main.route('/walk-times')
def walk_times():
    """Walk times dashboard"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 4))  # Changed to 4
        terminal = request.args.get('terminal', 'all')  # Default to 'all'

        logger.info(f"Walk Times Request - Page: {page}, Per Page: {per_page}, Terminal: {terminal}")

        # Get walk data for each airport
        jfk_data, jfk_count = get_paginated_data(jfk_storage, 'walk', terminal, page, per_page)
        lga_data, lga_count = get_paginated_data(lga_storage, 'walk', terminal, page, per_page)
        ewr_data, ewr_count = get_paginated_data(ewr_storage, 'walk', terminal, page, per_page)

        logger.info(f"JFK Walk Data Count: {jfk_count}")
        logger.info(f"LGA Walk Data Count: {lga_count}")
        logger.info(f"EWR Walk Data Count: {ewr_count}")

        # Calculate total pages based on the highest count
        total_count = max(jfk_count, lga_count, ewr_count)
        total_pages = max(1, (total_count + per_page - 1) // per_page)  # Ensure at least 1 page

        parsed_jfk = parse_mongo_data(jfk_data)
        parsed_lga = parse_mongo_data(lga_data)
        parsed_ewr = parse_mongo_data(ewr_data)

        logger.debug(f"Parsed JFK Walk Data: {parsed_jfk}")
        logger.debug(f"Parsed LGA Walk Data: {parsed_lga}")
        logger.debug(f"Parsed EWR Walk Data: {parsed_ewr}")

        return render_template('walk_times.html',
                             jfk_data=parsed_jfk,
                             lga_data=parsed_lga,
                             ewr_data=parsed_ewr,
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             selected_terminal=terminal,
                             data_type='walk')  # Added data_type
    except Exception as e:
        logger.error(f"Error in walk_times: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

@main.route('/jfk-times')
def jfk_times():
    """Partial template for JFK times"""
    try:
        data_type = request.args.get('type', 'security')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 4))
        terminal = request.args.get('terminal', 'all')
        
        logger.info(f"JFK request - Type: {data_type}, Terminal: {terminal}")
        
        data, total_count = get_paginated_data(
            jfk_storage, data_type, terminal, page, per_page
        )
        
        return render_template('partials/jfk_times.html',
                             data=parse_mongo_data(data),
                             data_type=data_type,
                             page=page,
                             per_page=per_page,
                             total_pages=max(1, (total_count + per_page - 1) // per_page),
                             selected_terminal=terminal)
    except Exception as e:
        logger.error(f"Error in JFK times: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main.route('/lga-times')
def lga_times():
    """Partial template for LGA times"""
    try:
        data_type = request.args.get('type', 'security')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 4))
        terminal = request.args.get('terminal', 'all')
        
        logger.info(f"LGA request - Type: {data_type}, Terminal: {terminal}")
        
        data, total_count = get_paginated_data(
            lga_storage, data_type, terminal, page, per_page
        )
        
        logger.info(f"LGA data count: {len(data)}")
        
        return render_template('partials/lga_times.html',
                             data=parse_mongo_data(data),
                             data_type=data_type,
                             page=page,
                             per_page=per_page,
                             total_pages=max(1, (total_count + per_page - 1) // per_page),
                             selected_terminal=terminal)
    except Exception as e:
        logger.error(f"Error in LGA times: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main.route('/ewr-times')
def ewr_times():
    """Partial template for EWR times"""
    try:
        data_type = request.args.get('type', 'security')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 4))
        terminal = request.args.get('terminal', 'all')
        
        logger.info(f"EWR request - Type: {data_type}, Terminal: {terminal}")
        
        data, total_count = get_paginated_data(
            ewr_storage, data_type, terminal, page, per_page
        )
        
        logger.info(f"EWR data count: {len(data)}")
        
        return render_template('partials/ewr_times.html',
                             data=parse_mongo_data(data),
                             data_type=data_type,
                             page=page,
                             per_page=per_page,
                             total_pages=max(1, (total_count + per_page - 1) // per_page),
                             selected_terminal=terminal)
    except Exception as e:
        logger.error(f"Error in EWR times: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    

def debug_terminal_values(storage, collection_name):
    """Debug helper to check terminal values in MongoDB"""
    collection = storage.security_collection if collection_name == 'security' else storage.walk_collection
    pipeline = [
        {"$group": {"_id": "$terminal"}},
        {"$project": {"terminal": "$_id", "_id": 0}}
    ]
    terminals = list(collection.aggregate(pipeline))
    logger.info(f"Terminals in {collection_name}: {terminals}")
    return terminals

@main.route('/debug-terminals')
def debug_terminals():
    """Debug endpoint to check terminal values"""
    for storage, name in [(jfk_storage, 'JFK'), (lga_storage, 'LGA'), (ewr_storage, 'EWR')]:
        logger.info(f"\n{name} Terminals:")
        security_terminals = debug_terminal_values(storage, 'security')
        walk_terminals = debug_terminal_values(storage, 'walk')
        logger.info(f"Security terminals: {security_terminals}")
        logger.info(f"Walk terminals: {walk_terminals}")
    return jsonify({"message": "Check logs for terminal values"})