from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateField, TimeField, IntegerField, FloatField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional, NumberRange
from models import User, UserRole, ReportType, PaymentMethod, PaymentStatus, CallType
from datetime import datetime, date

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    role = SelectField('Role', choices=[
        (UserRole.PATIENT.value, 'Patient'),
        (UserRole.DOCTOR.value, 'Doctor')
    ], validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.objects(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.objects(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
    
    def validate_date_of_birth(self, date_of_birth):
        if date_of_birth.data and date_of_birth.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')

class DoctorRegistrationForm(RegistrationForm):
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=100)])
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=50)])
    experience_years = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0)])
    consultation_fee = FloatField('Consultation Fee ($)', validators=[Optional(), NumberRange(min=0)])
    available_days = SelectField('Available Days', choices=[
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    ], validators=[Optional()])
    available_hours = StringField('Available Hours (e.g., 9:00 AM - 5:00 PM)', validators=[Optional()])
    submit = SubmitField('Register as Doctor')
    
    def validate_experience_years(self, experience_years):
        if experience_years.data < 0:
            raise ValidationError('Experience years cannot be negative.')

class PatientRegistrationForm(RegistrationForm):
    blood_group = SelectField('Blood Group', choices=[
        ('', 'Select Blood Group'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-')
    ], validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=20)])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    allergies = TextAreaField('Allergies', validators=[Optional()])
    insurance_provider = StringField('Insurance Provider', validators=[Optional(), Length(max=100)])
    insurance_number = StringField('Insurance Number', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Register as Patient')

class AppointmentForm(FlaskForm):
    doctor_id = SelectField('Doctor', coerce=str, validators=[DataRequired()])
    appointment_date = DateField('Appointment Date', validators=[DataRequired()])
    appointment_time = TimeField('Appointment Time', validators=[DataRequired()])
    duration = SelectField('Duration (minutes)', coerce=int, choices=[
        (15, '15 minutes'),
        (30, '30 minutes'),
        (45, '45 minutes'),
        (60, '1 hour')
    ], validators=[DataRequired()])
    symptoms = TextAreaField('Symptoms/Reason for Visit', validators=[Optional()])
    submit = SubmitField('Book Appointment')
    
    def validate_appointment_date(self, appointment_date):
        if appointment_date.data < date.today():
            raise ValidationError('Appointment date cannot be in the past.')

class MessageForm(FlaskForm):
    recipient_id = SelectField('Recipient', coerce=str, validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class ReportForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=str, validators=[Optional()])
    report_type = SelectField('Report Type', choices=[
        (ReportType.LAB_REPORT.value, 'Lab Report'),
        (ReportType.IMAGING_REPORT.value, 'Imaging Report'),
        (ReportType.CONSULTATION_REPORT.value, 'Consultation Report'),
        (ReportType.PRESCRIPTION.value, 'Prescription'),
        (ReportType.OTHER.value, 'Other')
    ], validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    file = FileField('Upload File', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 'Only PDF, DOC, DOCX, and image files are allowed!')
    ])
    submit = SubmitField('Create Report')

class PrescriptionForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=str, validators=[DataRequired()])
    medication = StringField('Medication Name', validators=[DataRequired(), Length(max=100)])
    dosage = StringField('Dosage', validators=[DataRequired(), Length(max=50)])
    frequency = StringField('Frequency', validators=[DataRequired(), Length(max=50)])
    duration = StringField('Duration (e.g., 7 days, 2 weeks)', validators=[DataRequired()])
    quantity = StringField('Quantity', validators=[DataRequired(), Length(max=50)])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Create Prescription')

class PaymentForm(FlaskForm):
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField('Payment Method', choices=[
        (PaymentMethod.CASH.value, 'Cash'),
        (PaymentMethod.CREDIT_CARD.value, 'Credit Card'),
        (PaymentMethod.DEBIT_CARD.value, 'Debit Card'),
        (PaymentMethod.INSURANCE.value, 'Insurance'),
        (PaymentMethod.ONLINE.value, 'Online Payment')
    ], validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Process Payment')

class ProfileUpdateForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    bio = TextAreaField('Bio', validators=[Optional()])
    profile_picture = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed!')
    ])
    submit = SubmitField('Update Profile')

class DoctorProfileForm(ProfileUpdateForm):
    specialization = StringField('Specialization', validators=[DataRequired(), Length(max=100)])
    license_number = StringField('License Number', validators=[DataRequired(), Length(max=50)])
    experience_years = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0)])
    consultation_fee = FloatField('Consultation Fee ($)', validators=[Optional(), NumberRange(min=0)])
    available_days = SelectField('Available Days', choices=[
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    ], validators=[Optional()])
    available_hours = StringField('Available Hours', validators=[Optional()])
    
    def validate_experience_years(self, experience_years):
        if experience_years.data < 0:
            raise ValidationError('Experience years cannot be negative.')

class PatientProfileForm(ProfileUpdateForm):
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    blood_group = SelectField('Blood Group', choices=[
        ('', 'Select Blood Group'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-')
    ], validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=20)])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    allergies = TextAreaField('Allergies', validators=[Optional()])
    insurance_provider = StringField('Insurance Provider', validators=[Optional(), Length(max=100)])
    insurance_number = StringField('Insurance Number', validators=[Optional(), Length(max=50)])

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    category = SelectField('Category', choices=[
        ('all', 'All'),
        ('doctors', 'Doctors'),
        ('appointments', 'Appointments'),
        ('reports', 'Reports'),
        ('messages', 'Messages')
    ], validators=[Optional()])
    submit = SubmitField('Search')

class FilterForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('all', 'All'),
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], validators=[Optional()])
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    submit = SubmitField('Apply Filter')

class SettingsForm(FlaskForm):
    site_name = StringField('Site Name', validators=[DataRequired()])
    site_email = StringField('Site Email', validators=[DataRequired(), Email()])
    max_file_size = IntegerField('Max File Size (MB)', validators=[DataRequired(), NumberRange(min=1, max=100)])
    session_timeout = IntegerField('Session Timeout (minutes)', validators=[DataRequired(), NumberRange(min=5, max=480)])
    maintenance_mode = BooleanField('Maintenance Mode')
    email_notifications = BooleanField('Email Notifications')
    sms_notifications = BooleanField('SMS Notifications')
    submit = SubmitField('Save Settings')

class AdminRegistrationForm(RegistrationForm):
    admin_code = StringField('Admin Code', validators=[DataRequired(), Length(min=6, max=20)])
    department = StringField('Department', validators=[DataRequired(), Length(max=100)])
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Register as Admin')
    
    def validate_admin_code(self, admin_code):
        # In a real application, you would validate against a secure admin code
        if admin_code.data != 'ADMIN2024':
            raise ValidationError('Invalid admin code.')

class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class PasswordResetConfirmForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')

class EmailVerificationForm(FlaskForm):
    verification_code = StringField('Verification Code', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify Email')

class ResendVerificationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend Verification Code')

class AdminUserCreationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    role = SelectField('Role', choices=[
        (UserRole.ADMIN.value, 'Admin'),
        (UserRole.DOCTOR.value, 'Doctor'),
        (UserRole.PATIENT.value, 'Patient'),
        (UserRole.GUEST.value, 'Guest')
    ], validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional()])
    is_active = BooleanField('Active Account', default=True)
    
    # Doctor specific fields
    specialization = StringField('Specialization', validators=[Optional(), Length(max=100)])
    license_number = StringField('License Number', validators=[Optional(), Length(max=50)])
    experience_years = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0)])
    consultation_fee = FloatField('Consultation Fee ($)', validators=[Optional(), NumberRange(min=0)])
    
    # Patient specific fields
    blood_group = SelectField('Blood Group', choices=[
        ('', 'Select Blood Group'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-')
    ], validators=[Optional()])
    emergency_contact = StringField('Emergency Contact', validators=[Optional(), Length(max=20)])
    medical_history = TextAreaField('Medical History', validators=[Optional()])
    insurance_provider = StringField('Insurance Provider', validators=[Optional(), Length(max=100)])
    insurance_number = StringField('Insurance Number', validators=[Optional(), Length(max=50)])
    
    # Admin specific fields
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    employee_id = StringField('Employee ID', validators=[Optional(), Length(max=50)])
    
    submit = SubmitField('Create User')
    
    def validate_username(self, username):
        user = User.objects(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.objects(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
    
    def validate_date_of_birth(self, date_of_birth):
        if date_of_birth.data and date_of_birth.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')

class CallForm(FlaskForm):
    call_type = SelectField('Call Type', choices=[
        (CallType.AUDIO.value, 'Audio Call'),
        (CallType.VIDEO.value, 'Video Call')
    ], validators=[DataRequired()])
    participants = SelectField('Participants', coerce=str, validators=[DataRequired()], multiple=True)
    call_title = StringField('Call Title', validators=[Optional(), Length(max=200)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Start Call')

class GroupCallForm(FlaskForm):
    call_type = SelectField('Call Type', choices=[
        (CallType.AUDIO.value, 'Audio Call'),
        (CallType.VIDEO.value, 'Video Call')
    ], validators=[DataRequired()])
    participants = SelectField('Participants', coerce=str, validators=[DataRequired()], multiple=True)
    call_title = StringField('Call Title', validators=[DataRequired(), Length(max=200)])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Start Group Call')
