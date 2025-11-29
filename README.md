<<<<<<< HEAD
# Healthcare AI System

A comprehensive healthcare management system with AI-powered chatbot, appointment scheduling, and health prediction features.

## Features

### 🤖 AI Health Assistant
- Intelligent chatbot for health-related queries
- Natural language processing for better user interaction
- Contextual health recommendations
- Integration with medical knowledge base

### 📅 Appointment Management
- Doctor and patient appointment scheduling
- Real-time availability checking
- Automated reminders and notifications
- Multi-role dashboard system

### 📊 Health Analytics & Predictions
- AI-powered health risk assessment
- Predictive analytics for health trends
- Personalized health reports
- Medical data visualization

### 👥 Multi-Role System
- **Admin Dashboard**: System management and analytics
- **Doctor Dashboard**: Patient management and medical tools
- **Patient Dashboard**: Personal health tracking and appointments
- **Guest Access**: Public information and basic features

### 🔐 Security & Authentication
- Secure user authentication
- Role-based access control
- Password encryption and validation
- Session management

## Technology Stack

- **Backend**: Python Flask
- **Database**: MongoDB with MongoEngine
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI/ML**: NLTK, Scikit-learn, TensorFlow
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Email**: Flask-Mail

## Installation

### Prerequisites
- Python 3.8 or higher
- MongoDB (local or cloud)
- pip package manager

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Ai_health_chat
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   MONGODB_URI=mongodb://localhost:27017/healthcare_ai
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

5. **Initialize the database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

   Or use the main app directly:
   ```bash
   python app.py
   ```

## Usage

### Starting the Application

1. **Run the application**:
   ```bash
   python run.py
   ```

2. **Access the application**:
   - Open your browser and go to `http://127.0.0.1:5000`
   - The application will be running on the specified host and port

### User Roles

#### Admin
- Access: `/admin/dashboard`
- Features: User management, system analytics, appointment oversight

#### Doctor
- Access: `/doctor/dashboard`
- Features: Patient management, appointment scheduling, medical reports

#### Patient
- Access: `/patient/dashboard`
- Features: Book appointments, view medical reports, health tracking

#### Guest
- Access: Public pages
- Features: View information, use AI chatbot, contact forms

### Key Features

#### AI Health Assistant
- Access the chatbot at `/chat` or `/chatbot`
- Ask health-related questions
- Get personalized recommendations
- View health tips and suggestions

#### Appointment Booking
- Patients can book appointments with doctors
- Real-time availability checking
- Email notifications for confirmations

#### Health Predictions
- Access at `/prediction`
- Input health data for risk assessment
- Get personalized health insights
- View health trend analysis

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/logout` - User logout

### Chat API
- `POST /api/chat` - Send message to AI chatbot
- `GET /api/chat/history` - Get chat history

### Appointments
- `GET /dashboard/appointments` - View appointments
- `POST /dashboard/appointments` - Create appointment
- `PUT /dashboard/appointments/<id>` - Update appointment
- `DELETE /dashboard/appointments/<id>` - Cancel appointment

## Configuration

### Database Configuration
The application uses MongoDB for data storage. Configure the connection in `config.py`:

```python
MONGODB_SETTINGS = {
    'db': 'healthcare_ai',
    'host': 'mongodb://localhost:27017/healthcare_ai'
}
```

### Email Configuration
Configure email settings for notifications:

```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
```

## Testing

Run the test suite to verify everything is working:

```bash
python test_app.py
```

This will test:
- Module imports
- Flask app creation
- Database models
- Route accessibility

## Project Structure

```
Ai_health_chat/
├── app.py                 # Main Flask application
├── auth.py               # Authentication routes
├── dashboard.py          # Dashboard routes
├── chatbot.py            # Chatbot functionality
├── learning_model.py     # AI model implementation
├── models.py             # Database models
├── forms.py              # WTForms definitions
├── config.py             # Configuration settings
├── init_db.py            # Database initialization
├── run.py                # Application runner
├── test_app.py           # Test suite
├── requirements.txt      # Python dependencies
├── static/               # Static files
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── templates/            # HTML templates
│   ├── auth/            # Authentication templates
│   ├── dashboard/       # Dashboard templates
│   ├── doctor/          # Doctor-specific templates
│   ├── patient/         # Patient-specific templates
│   └── admin/           # Admin templates
└── data/                # Data files
    └── intents.json     # Chatbot training data
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Changelog

### Version 1.0.0
- Initial release
- AI health assistant
- Multi-role dashboard system
- Appointment management
- Health prediction features
- Responsive design
- Security implementation

---

**Note**: This is a healthcare application. Always consult with medical professionals for serious health concerns. The AI assistant provides general information and should not replace professional medical advice.
=======
# HealthTracketAi
>>>>>>> 82428c59f206a4a98eaea621922865ff80951d94
