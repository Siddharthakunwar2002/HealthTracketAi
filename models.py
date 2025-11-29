from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, IntField, ReferenceField, ListField, EnumField, DateField, FloatField, DictField
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    GUEST = "guest"

class AppointmentStatus(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class ReportType(enum.Enum):
    LAB_REPORT = "lab_report"
    IMAGING_REPORT = "imaging_report"
    CONSULTATION_REPORT = "consultation_report"
    PATHOLOGY_REPORT = "pathology_report"
    PRESCRIPTION = "prescription"
    OTHER = "other"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    INSURANCE = "insurance"
    ONLINE = "online"

class NotificationType(enum.Enum):
    APPOINTMENT = "appointment"
    MESSAGE = "message"
    PAYMENT = "payment"
    SYSTEM = "system"
    REMINDER = "reminder"

class LogLevel(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"

class CallType(enum.Enum):
    AUDIO = "audio"
    VIDEO = "video"

class CallStatus(enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    CONNECTED = "connected"
    ENDED = "ended"
    MISSED = "missed"
    CANCELLED = "cancelled"

class User(Document, UserMixin):
    username = StringField(max_length=80, unique=True, required=True)
    email = EmailField(unique=True, required=True)
    password_hash = StringField(max_length=255, required=True)
    first_name = StringField(max_length=50, required=True)
    last_name = StringField(max_length=50, required=True)
    role = EnumField(UserRole, required=True, default=UserRole.PATIENT)
    phone = StringField(max_length=20)
    date_of_birth = DateField()
    address = StringField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    # Doctor specific fields
    specialization = StringField(max_length=100)
    license_number = StringField(max_length=50)
    experience_years = IntField()
    consultation_fee = FloatField(default=0.0)
    available_days = ListField(StringField(), default=[])
    available_hours = StringField(max_length=100)
    
    # Patient specific fields
    blood_group = StringField(max_length=5)
    emergency_contact = StringField(max_length=20)
    medical_history = StringField()
    insurance_provider = StringField(max_length=100)
    insurance_number = StringField(max_length=50)
    
    # Profile fields
    profile_picture = StringField(max_length=255)
    bio = StringField()
    
    # Admin specific fields
    department = StringField(max_length=100)
    employee_id = StringField(max_length=50)
    last_login = DateTimeField()
    
    meta = {
        'collection': 'users',
        'indexes': [
            'username',
            'email',
            'role'
        ]
    }
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_doctor(self):
        return self.role == UserRole.DOCTOR
    
    def is_patient(self):
        return self.role == UserRole.PATIENT
    
    def is_guest(self):
        return self.role == UserRole.GUEST
    
    def get_id(self):
        return str(self.id)

class Appointment(Document):
    patient = ReferenceField(User, required=True)
    doctor = ReferenceField(User, required=True)
    appointment_date = DateTimeField(required=True)
    duration = IntField(default=30)  # minutes
    status = EnumField(AppointmentStatus, default=AppointmentStatus.SCHEDULED)
    notes = StringField()
    symptoms = StringField()
    diagnosis = StringField()
    treatment_plan = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'appointments',
        'indexes': [
            'patient',
            'doctor',
            'appointment_date',
            'status'
        ]
    }

class Prescription(Document):
    patient = ReferenceField(User, required=True)
    doctor = ReferenceField(User, required=True)
    appointment = ReferenceField(Appointment)
    medications = ListField(DictField(), required=True)  # List of medication objects
    dosage_instructions = StringField(required=True)
    duration = StringField(max_length=50)  # e.g., "7 days", "2 weeks"
    notes = StringField()
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'prescriptions',
        'indexes': [
            'patient',
            'doctor',
            'is_active'
        ]
    }

class Report(Document):
    user = ReferenceField(User, required=True)
    appointment = ReferenceField(Appointment)
    report_type = EnumField(ReportType, required=True)
    title = StringField(max_length=200, required=True)
    description = StringField()
    file_path = StringField(max_length=255)
    created_by = ReferenceField(User, required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'reports',
        'indexes': [
            'user',
            'created_by',
            'report_type'
        ]
    }

class Message(Document):
    sender = ReferenceField(User, required=True)
    recipient = ReferenceField(User, required=True)
    subject = StringField(max_length=200)
    content = StringField(required=True)
    is_read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'messages',
        'indexes': [
            'sender',
            'recipient',
            'is_read'
        ]
    }
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class ChatMessage(Document):
    user = ReferenceField(User, required=True)
    message = StringField(required=True)
    response = StringField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'chat_messages',
        'indexes': [
            'user',
            'created_at'
        ]
    }

class Notification(Document):
    user = ReferenceField(User, required=True)
    title = StringField(max_length=200, required=True)
    message = StringField(required=True)
    notification_type = EnumField(NotificationType, default=NotificationType.SYSTEM)
    is_read = BooleanField(default=False)
    related_id = StringField(max_length=50)  # ID of related object (appointment, message, etc.)
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'notifications',
        'indexes': [
            'user',
            'is_read',
            'notification_type'
        ]
    }
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class Payment(Document):
    patient = ReferenceField(User, required=True)
    doctor = ReferenceField(User, required=True)
    appointment = ReferenceField(Appointment)
    amount = FloatField(required=True)
    currency = StringField(max_length=3, default='USD')
    payment_method = EnumField(PaymentMethod, required=True)
    status = EnumField(PaymentStatus, default=PaymentStatus.PENDING)
    transaction_id = StringField(max_length=100)
    payment_date = DateTimeField()
    notes = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'payments',
        'indexes': [
            'patient',
            'doctor',
            'status',
            'transaction_id'
        ]
    }

class SystemLog(Document):
    user = ReferenceField(User)
    action = StringField(max_length=200, required=True)
    details = StringField()
    ip_address = StringField(max_length=45)
    user_agent = StringField(max_length=500)
    log_level = EnumField(LogLevel, default=LogLevel.INFO)
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'system_logs',
        'indexes': [
            'user',
            'action',
            'log_level',
            'created_at'
        ]
    }

class Analytics(Document):
    metric_name = StringField(max_length=100, required=True)
    metric_value = FloatField(required=True)
    metric_date = DateField(required=True)
    category = StringField(max_length=50)
    metadata = DictField()
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'analytics',
        'indexes': [
            'metric_name',
            'metric_date',
            'category'
        ]
    }

class Call(Document):
    initiator = ReferenceField(User, required=True)
    participants = ListField(ReferenceField(User), required=True)
    call_type = EnumField(CallType, default=CallType.VIDEO)
    status = EnumField(CallStatus, default=CallStatus.INITIATED)
    room_id = StringField(max_length=100, unique=True, required=True)
    start_time = DateTimeField()
    end_time = DateTimeField()
    duration = IntField()  # in seconds
    is_group_call = BooleanField(default=False)
    call_title = StringField(max_length=200)
    notes = StringField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'calls',
        'indexes': [
            'initiator',
            'participants',
            'status',
            'room_id',
            'start_time'
        ]
    }

class CallParticipant(Document):
    call = ReferenceField(Call, required=True)
    user = ReferenceField(User, required=True)
    joined_at = DateTimeField()
    left_at = DateTimeField()
    is_muted = BooleanField(default=False)
    is_video_enabled = BooleanField(default=True)
    is_screen_sharing = BooleanField(default=False)
    connection_quality = StringField(max_length=20, default='good')  # good, fair, poor
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'call_participants',
        'indexes': [
            'call',
            'user'
        ]
    }

class CallLog(Document):
    call = ReferenceField(Call, required=True)
    user = ReferenceField(User, required=True)
    action = StringField(max_length=100, required=True)  # joined, left, muted, unmuted, etc.
    details = StringField()
    timestamp = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'call_logs',
        'indexes': [
            'call',
            'user',
            'action'
        ]
    }
