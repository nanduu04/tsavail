from flask import Blueprint, jsonify, request, render_template
from datetime import datetime, timedelta
from app.storage import MongoDBStorage
from bson import json_util
import json

main = Blueprint('main', __name__)
storage = MongoDBStorage()

def parse_mongo_data(data):
    """Convert MongoDB data to JSON-serializable format"""
    return json.loads(json_util.dumps(data))

@main.route('/')
def index():
    """Main dashboard page"""
    try:
        # Get latest data for each airport
        latest_lga = storage.get_latest_data('lga')
        latest_jfk = storage.get_latest_data('jfk')
        latest_ewr = storage.get_latest_data('ewr')
        
        return render_template('base.html',
                             latest_lga=parse_mongo_data(latest_lga),
                             latest_jfk=parse_mongo_data(latest_jfk),
                             latest_ewr=parse_mongo_data(latest_ewr))
    except Exception as e:
        return render_template('error.html', error=str(e))

@main.route('/wait-times')
def wait_times():
    """Wait times dashboard with pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        skip = (page - 1) * per_page

        # Get paginated data for each airport
        jfk_data = storage.get_jfk_data(limit=per_page, skip=skip)
        lga_data = storage.get_lga_data(limit=per_page, skip=skip)
        ewr_data = storage.get_ewr_data(limit=per_page, skip=skip)

        return render_template('wait_times.html',
                             jfk_data=parse_mongo_data(jfk_data),
                             lga_data=parse_mongo_data(lga_data),
                             ewr_data=parse_mongo_data(ewr_data),
                             page=page,
                             per_page=per_page)
    except Exception as e:
        return render_template('error.html', error=str(e))

@main.route('/jfk-times')
def jfk_times():
    """Partial template for JFK times with filtering"""
    try:
        terminal = request.args.get('terminal')
        date_range = request.args.get('date_range', '24h')  # '24h', '7d', '30d'
        
        end_date = datetime.utcnow()
        if date_range == '24h':
            start_date = end_date - timedelta(days=1)
        elif date_range == '7d':
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        jfk_data = storage.get_data_by_date_range('jfk', start_date, end_date)
        
        if terminal:
            jfk_data = [d for d in jfk_data if d.get('Terminal') == terminal]

        return render_template('partials/jfk_times.html',
                             jfk_data=parse_mongo_data(jfk_data),
                             selected_terminal=terminal,
                             date_range=date_range)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/lga-times')
def lga_times():
    """Partial template for LGA times with filtering"""
    try:
        terminal = request.args.get('terminal')
        date_range = request.args.get('date_range', '24h')
        
        end_date = datetime.utcnow()
        if date_range == '24h':
            start_date = end_date - timedelta(days=1)
        elif date_range == '7d':
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        lga_data = storage.get_data_by_date_range('lga', start_date, end_date)
        
        if terminal:
            lga_data = [d for d in lga_data if d.get('Terminal') == terminal]

        return render_template('partials/lga_times.html',
                             lga_data=parse_mongo_data(lga_data),
                             selected_terminal=terminal,
                             date_range=date_range)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/ewr-times')
def ewr_times():
    """Partial template for EWR times with filtering"""
    try:
        terminal = request.args.get('terminal')
        date_range = request.args.get('date_range', '24h')
        
        end_date = datetime.utcnow()
        if date_range == '24h':
            start_date = end_date - timedelta(days=1)
        elif date_range == '7d':
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        ewr_data = storage.get_data_by_date_range('ewr', start_date, end_date)
        
        if terminal:
            ewr_data = [d for d in ewr_data if d.get('Terminal') == terminal]

        return render_template('partials/ewr_times.html',
                             ewr_data=parse_mongo_data(ewr_data),
                             selected_terminal=terminal,
                             date_range=date_range)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/lga', methods=['GET'])
def get_lga():
    """Get LGA wait times data with filtering and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        terminal = request.args.get('terminal')
        date_range = request.args.get('date_range', '24h')
        
        skip = (page - 1) * per_page
        end_date = datetime.utcnow()
        
        if date_range == '24h':
            start_date = end_date - timedelta(days=1)
        elif date_range == '7d':
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        lga_data = storage.get_data_by_date_range('lga', start_date, end_date)
        
        if terminal:
            lga_data = [d for d in lga_data if d.get('Terminal') == terminal]

        total_count = len(lga_data)
        paginated_data = lga_data[skip:skip + per_page]

        return jsonify({
            'data': parse_mongo_data(paginated_data),
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/jfk', methods=['GET'])
def get_jfk():
    """Get JFK walk times data with formatting"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        terminal = request.args.get('terminal')
        date_range = request.args.get('date_range', '24h')
        
        # Get data from MongoDB
        end_date = datetime.utcnow()
        if date_range == '24h':
            start_date = end_date - timedelta(days=1)
        elif date_range == '7d':
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        # Get data and apply filters
        jfk_data = storage.get_data_by_date_range('jfk', start_date, end_date)
        
        if terminal:
            jfk_data = [d for d in jfk_data if d.get('Terminal') == terminal]

        # Process the data for display
        processed_data = []
        for item in jfk_data:
            processed_item = {
                'Terminal': item['Terminal'],
                'Gate': item['Gate'],
                'Walk_Time': item['Walk Time'],
                'created_at': item['created_at'].strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            processed_data.append(processed_item)

        # Sort data by terminal and gate
        processed_data.sort(key=lambda x: (x['Terminal'], x['Gate']))
        
        # Apply pagination
        total_count = len(processed_data)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_data = processed_data[start_idx:end_idx]

        return jsonify({
            'data': paginated_data,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/ewr', methods=['GET'])
def get_ewr():
    """Get EWR TSA wait times data with filtering and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        terminal = request.args.get('terminal')
        date_range = request.args.get('date_range', '24h')
        
        skip = (page - 1) * per_page
        end_date = datetime.utcnow()
        
        if date_range == '24h':
            start_date = end_date - timedelta(days=1)
        elif date_range == '7d':
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        ewr_data = storage.get_data_by_date_range('ewr', start_date, end_date)
        
        if terminal:
            ewr_data = [d for d in ewr_data if d.get('Terminal') == terminal]

        total_count = len(ewr_data)
        paginated_data = ewr_data[skip:skip + per_page]

        return jsonify({
            'data': parse_mongo_data(paginated_data),
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/api/health', methods=['GET'])
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Check MongoDB connection
        storage.get_latest_data('lga')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

