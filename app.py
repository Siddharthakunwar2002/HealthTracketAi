from flask import Flask, request, jsonify, render_template, send_from_directory, flash, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user, login_required
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import nltk
import logging
from mongoengine import connect
from learning_model import HealthChatbotModel
from config import Config
from models import User, ChatMessage, UserRole, Call, CallParticipant, CallLog, CallStatus
from auth import auth
from dashboard import dashboard
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt')
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    nltk.download('averaged_perceptron_tagger')
    logger.info("NLTK data downloaded successfully")
except Exception as e:
    logger.error(f"Error downloading NLTK data: {str(e)}")

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    # Connect to MongoDB
    connect(host=app.config['MONGODB_URI'])

    # Initialize extensions
    CORS(app)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Add custom Jinja2 filters
    @app.template_filter('to_string')
    def to_string_filter(value):
        """Convert ObjectId or any value to string"""
        return str(value)

    @app.template_filter('objectid_slice')
    def objectid_slice_filter(value, start=0, end=8):
        """Slice ObjectId string representation"""
        return str(value)[start:end]

    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(id=user_id).first()

    # Register blueprints
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(dashboard, url_prefix='/dashboard')

    # Initialize chatbot
    chatbot = None

    def initialize_chatbot():
        nonlocal chatbot
        try:
            logger.info("Initializing chatbot...")
            chatbot = HealthChatbotModel()

            # Try to load existing model, if not found, train a new one
            if not chatbot.load_saved_model():
                logger.info("No saved model found. Training new model...")
                chatbot.load_data('data/intents.json')
                chatbot.prepare_training_data()
                chatbot.build_model()
                chatbot.train_model()
                chatbot.save_model()
                logger.info("Model training completed!")
            else:
                logger.info("Loaded existing model successfully")

        except Exception as e:
            logger.error(f"Error initializing chatbot: {str(e)}")
            raise

    # Initialize the chatbot when the app starts
    initialize_chatbot()

    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/features')
    def features():
        return render_template('features.html')

    @app.route('/contact')
    def contact():
        return render_template('contact.html')

    @app.route('/chat')
    # @login_required
    def chat():
        return render_template('gui_chat.html')

    @app.route('/chatbot')
    def chatbot_page():
        return render_template('chatbot.html')

    @app.route('/prediction')
    def prediction_page():
        return render_template('prediction.html')

    @app.route('/login')
    def login():
        return redirect(url_for('auth.login'))

    @app.route('/admin/login')
    def admin_login():
        return redirect(url_for('auth.admin_login'))

    @app.route('/register')
    def register():
        return redirect(url_for('auth.register'))

    @app.route('/api/chat', methods=['POST'])
    def chat_api():
        try:
            data = request.get_json()
            user_message = data.get('message', '')

            if not user_message:
                return jsonify({'status': 'error', 'error': 'No message provided'}), 400

            # Get chatbot response
            response = chatbot.get_response(user_message)

            # Save chat message to database if user is authenticated
            if current_user.is_authenticated:
                chat_message = ChatMessage(
                    user=current_user,
                    message=user_message,
                    response=response
                )
                chat_message.save()

            return jsonify({
                'status': 'success',
                'response': response,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error in chat API: {str(e)}")
            return jsonify({'status': 'error', 'error': 'Internal server error'}), 500

    @app.route('/api/welcome', methods=['GET'])
    def welcome_api():
        """
        Returns a welcome message and logs the request
        """
        logger.info(f"Request received: {request.method} {request.path}")
        return jsonify({'message': 'Welcome to the Flask API Service!'})

    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory('static', filename)

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    # SocketIO event handlers for WebRTC calls
    @socketio.on('join_call')
    def handle_join_call(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')

        if room_id and user_id:
            join_room(room_id)
            emit('user_joined', {'user_id': user_id}, room=room_id, skip_sid=True)

            # Update call participant status
            try:
                call = Call.objects(room_id=room_id).first()
                if call:
                    participant = CallParticipant.objects(call=call, user=user_id).first()
                    if participant:
                        participant.joined_at = datetime.utcnow()
                        participant.save()

                        # Log the action
                        CallLog(call=call, user=user_id, action='joined').save()
            except Exception as e:
                logger.error(f"Error updating participant status: {e}")

    @socketio.on('leave_call')
    def handle_leave_call(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')

        if room_id and user_id:
            leave_room(room_id)
            emit('user_left', {'user_id': user_id}, room=room_id, skip_sid=True)

            # Update call participant status
            try:
                call = Call.objects(room_id=room_id).first()
                if call:
                    participant = CallParticipant.objects(call=call, user=user_id).first()
                    if participant:
                        participant.left_at = datetime.utcnow()
                        participant.save()

                        # Log the action
                        CallLog(call=call, user=user_id, action='left').save()
            except Exception as e:
                logger.error(f"Error updating participant status: {e}")

    @socketio.on('offer')
    def handle_offer(data):
        room_id = data.get('room_id')
        offer = data.get('offer')
        user_id = data.get('user_id')

        if room_id and offer:
            emit('offer', {'offer': offer, 'user_id': user_id}, room=room_id, skip_sid=True)

    @socketio.on('answer')
    def handle_answer(data):
        room_id = data.get('room_id')
        answer = data.get('answer')
        user_id = data.get('user_id')

        if room_id and answer:
            emit('answer', {'answer': answer, 'user_id': user_id}, room=room_id, skip_sid=True)

    @socketio.on('ice_candidate')
    def handle_ice_candidate(data):
        room_id = data.get('room_id')
        candidate = data.get('candidate')
        user_id = data.get('user_id')

        if room_id and candidate:
            emit('ice_candidate', {'candidate': candidate, 'user_id': user_id}, room=room_id, skip_sid=True)

    @socketio.on('mute_audio')
    def handle_mute_audio(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')

        if room_id and user_id:
            emit('user_muted', {'user_id': user_id}, room=room_id, skip_sid=True)

            # Update participant status
            try:
                call = Call.objects(room_id=room_id).first()
                if call:
                    participant = CallParticipant.objects(call=call, user=user_id).first()
                    if participant:
                        participant.is_muted = True
                        participant.save()

                        # Log the action
                        CallLog(call=call, user=user_id, action='muted').save()
            except Exception as e:
                logger.error(f"Error updating mute status: {e}")

    @socketio.on('unmute_audio')
    def handle_unmute_audio(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')

        if room_id and user_id:
            emit('user_unmuted', {'user_id': user_id}, room=room_id, skip_sid=True)

            # Update participant status
            try:
                call = Call.objects(room_id=room_id).first()
                if call:
                    participant = CallParticipant.objects(call=call, user=user_id).first()
                    if participant:
                        participant.is_muted = False
                        participant.save()

                        # Log the action
                        CallLog(call=call, user=user_id, action='unmuted').save()
            except Exception as e:
                logger.error(f"Error updating unmute status: {e}")

    @socketio.on('toggle_video')
    def handle_toggle_video(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        enabled = data.get('enabled', True)

        if room_id and user_id:
            emit('video_toggled', {'user_id': user_id, 'enabled': enabled}, room=room_id, skip_sid=True)

            # Update participant status
            try:
                call = Call.objects(room_id=room_id).first()
                if call:
                    participant = CallParticipant.objects(call=call, user=user_id).first()
                    if participant:
                        participant.is_video_enabled = enabled
                        participant.save()

                        action = 'video_enabled' if enabled else 'video_disabled'
                        CallLog(call=call, user=user_id, action=action).save()
            except Exception as e:
                logger.error(f"Error updating video status: {e}")

    @socketio.on('screen_share')
    def handle_screen_share(data):
        room_id = data.get('room_id')
        user_id = data.get('user_id')
        sharing = data.get('sharing', False)

        if room_id and user_id:
            emit('screen_shared', {'user_id': user_id, 'sharing': sharing}, room=room_id, skip_sid=True)

            # Update participant status
            try:
                call = Call.objects(room_id=room_id).first()
                if call:
                    participant = CallParticipant.objects(call=call, user=user_id).first()
                    if participant:
                        participant.is_screen_sharing = sharing
                        participant.save()

                        action = 'screen_share_started' if sharing else 'screen_share_stopped'
                        CallLog(call=call, user=user_id, action=action).save()
            except Exception as e:
                logger.error(f"Error updating screen share status: {e}")

    return app, socketio

# Create the Flask app instance
app, socketio = create_app()

if __name__ == '__main__':
    # Create upload directories if they don't exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('uploads/reports', exist_ok=True)

    # Create default users for all roles if they don't exist
    try:
        admin_user = User.objects(email='admin@healthcare.com').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@healthcare.com',
                first_name='System',
                last_name='Administrator',
                role=UserRole.ADMIN,
                phone='555-0001',
                is_active=True
            )
            admin_user.set_password('admin123')
            admin_user.save()
            print("✓ Default admin user created")
        else:
            print("✓ Admin user already exists")

        doctor_user = User.objects(email='doctor@healthcare.com').first()
        if not doctor_user:
            doctor_user = User(
                username='doctor',
                email='doctor@healthcare.com',
                first_name='Demo',
                last_name='Doctor',
                role=UserRole.DOCTOR,
                phone='555-1000',
                specialization='General Medicine',
                license_number='MD-DEMO-001',
                experience_years=5,
                is_active=True
            )
            doctor_user.set_password('password123')
            doctor_user.save()
            print("✓ Default doctor user created")
        else:
            print("✓ Doctor user already exists")

        patient_user = User.objects(email='patient@healthcare.com').first()
        if not patient_user:
            patient_user = User(
                username='patient',
                email='patient@healthcare.com',
                first_name='Demo',
                last_name='Patient',
                role=UserRole.PATIENT,
                phone='555-2000',
                blood_group='O+',
                is_active=True
            )
            patient_user.set_password('password123')
            patient_user.save()
            print("✓ Default patient user created")
        else:
            print("✓ Patient user already exists")

        guest_user = User.objects(email='guest@healthcare.com').first()
        if not guest_user:
            guest_user = User(
                username='guest',
                email='guest@healthcare.com',
                first_name='Guest',
                last_name='User',
                role=UserRole.GUEST,
                is_active=True
            )
            guest_user.set_password('password123')
            guest_user.save()
            print("✓ Default guest user created")
        else:
            print("✓ Guest user already exists")
    except Exception as e:
        print(f"Error creating default users: {e}")

    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
