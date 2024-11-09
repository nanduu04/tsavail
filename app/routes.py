from flask import Blueprint, jsonify, request
from app.storage import JsonStorage

main = Blueprint('main', __name__)  # Fixed syntax for __name__
storage = JsonStorage()

@main.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@main.route('/flight', methods=['POST'])
def create_flight():
    """Create a new flight schedule"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        required_fields = ['flight_time', 'airport_code', 'start_location']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        saved_flight = storage.create_flight(data)
        return jsonify({
            'message': 'Flight schedule created',
            'data': saved_flight
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@main.route('/flights', methods=['GET'])
def get_flights():
    """Get all flight schedules"""
    try:
        flights = storage.get_flights()
        return jsonify({'flights': flights}), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500



@main.route('/lga', methods=['GET'])
def get_lga():
    """Get all LGA wait times data"""
    try:
        lga_data = storage.get_lga_data()

        if not lga_data:
            return jsonify({'message': 'No LGA wait times data found'}), 404

        return jsonify({
            'message': 'LGA wait times data retrieved successfully',
            'data': lga_data
        }), 200

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500