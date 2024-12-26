from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conference_rooms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Room model
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=True)

# Define the Booking model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    employee_name = db.Column(db.String(50), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

# Initialize the database and add sample data
def initialize_database():
    with app.app_context():
        db.create_all()
        if not Room.query.first():  # Add sample rooms if none exist
            sample_rooms = [
                Room(name="Conference Room A", capacity=10, location="New Sales Office"),
                Room(name="Conference Room B", capacity=10, location="NP HQ"),
                Room(name="Conference Room C", capacity=10, location="NP HQ"),
            ]
            db.session.add_all(sample_rooms)
            db.session.commit()
            print("Database initialized with sample data.")

#sends room data with booking details to the frontend.
@app.route('/')
def home():
    rooms = Room.query.all()
    # Replace this with the actual logic to get the logged-in user's name
    user_name = "hari"  # Example hardcoded user name for testing
    room_data = [
        {
            'id': room.id,
            'name': room.name,
            'location': room.location,
            'bookings': [
                {
                    'id': booking.id,  # Include booking ID for cancellation
                    'employee_name': booking.employee_name,
                    'start_time': booking.start_time.strftime('%Y-%m-%d %H:%M'),
                    'end_time': booking.end_time.strftime('%Y-%m-%d %H:%M')
                }
                for booking in Booking.query.filter_by(room_id=room.id).order_by(Booking.start_time).all()
            ]
        }
        for room in rooms
    ]
    return render_template('index.html', rooms=room_data, user_name=user_name)


# API to get room details
@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    rooms = Room.query.all()
    room_data = [
        {
            'id': room.id,
            'name': room.name,
            'location': room.location,
            'bookings': [
                {
                    'employee_name': booking.employee_name,
                    'start_time': booking.start_time.strftime('%Y-%m-%d %H:%M'),
                    'end_time': booking.end_time.strftime('%Y-%m-%d %H:%M')
                }
                for booking in Booking.query.filter_by(room_id=room.id).order_by(Booking.start_time).all()
            ]
        }
        for room in rooms
    ]
    return jsonify(room_data)

# Route for booking a room
@app.route('/book', methods=['POST'])
def book_room():
    try:
        room_id = request.form['room_id']
        employee_name = request.form['employee_name']
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')

        if not employee_name:
            return jsonify({'error': 'Employee name is required!'}), 400

        overlapping_bookings = Booking.query.filter(
            Booking.room_id == room_id,
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).all()

        if overlapping_bookings:
            return jsonify({'error': 'The room is already booked for this time slot.'}), 400

        new_booking = Booking(
            room_id=room_id,
            employee_name=employee_name,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(new_booking)
        db.session.commit()
        return jsonify({'message': 'Room booked successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# Default route for serving the HTML


if __name__ == '__main__':
    initialize_database()  # Ensure database is initialized
    app.run(host='0.0.0.0', port=8080)
