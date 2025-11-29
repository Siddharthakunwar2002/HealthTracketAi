from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import (
    User, Appointment, Report, Message, Notification, UserRole, AppointmentStatus,
    Prescription, Payment, PaymentStatus, PaymentMethod, SystemLog, Analytics,
    NotificationType, LogLevel, ChatMessage, Call, CallParticipant, CallType, CallStatus
)
from forms import (
    AppointmentForm, MessageForm, ReportForm, PrescriptionForm, PaymentForm,
    ProfileUpdateForm, DoctorProfileForm, PatientProfileForm, SearchForm,
    FilterForm, SettingsForm, ContactForm, AdminUserCreationForm
)
from datetime import datetime, timedelta
import os
import json
from werkzeug.utils import secure_filename
from mongoengine.queryset.visitor import Q

dashboard = Blueprint('dashboard', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.dashboard_home'))
        return f(*args, **kwargs)
    return decorated_function

def doctor_required(f):
    """Decorator to require doctor role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_doctor():
            flash('Access denied. Doctor privileges required.', 'error')
            return redirect(url_for('dashboard.dashboard_home'))
        return f(*args, **kwargs)
    return decorated_function

def patient_required(f):
    """Decorator to require patient role"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_patient():
            flash('Access denied. Patient privileges required.', 'error')
            return redirect(url_for('dashboard.dashboard_home'))
        return f(*args, **kwargs)
    return decorated_function

def log_action(action, details=None, log_level=LogLevel.INFO):
    """Log system actions"""
    try:
        log = SystemLog(
            user=current_user if current_user.is_authenticated else None,
            action=action,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            log_level=log_level
        )
        log.save()
    except Exception as e:
        current_app.logger.error(f"Failed to log action: {e}")

# Main dashboard route
@dashboard.route('/')
@login_required
def dashboard_home():
    if current_user.is_admin():
        return redirect(url_for('dashboard.admin_dashboard'))
    elif current_user.is_doctor():
        return redirect(url_for('dashboard.doctor_dashboard'))
    elif current_user.is_patient():
        return redirect(url_for('dashboard.patient_dashboard'))
    else:
        return redirect(url_for('home'))

# ============================================================================
# ADMIN DASHBOARD ROUTES
# ============================================================================

@dashboard.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin main dashboard"""
    try:
        # Get statistics
        total_users = User.objects.count()
        total_doctors = User.objects(role=UserRole.DOCTOR).count()
        total_patients = User.objects(role=UserRole.PATIENT).count()
        total_appointments = Appointment.objects.count()
        pending_appointments = Appointment.objects(status=AppointmentStatus.SCHEDULED).count()
        total_payments = Payment.objects.count()
        total_revenue = sum([p.amount for p in Payment.objects(status=PaymentStatus.PAID)])
        
        # Recent activities
        recent_appointments = Appointment.objects.order_by('-created_at').limit(5)
        recent_users = User.objects.order_by('-created_at').limit(5)
        recent_payments = Payment.objects.order_by('-created_at').limit(5)
        
        # System health
        system_logs = SystemLog.objects.order_by('-created_at').limit(10)
        
        log_action("Admin dashboard accessed")
        
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             total_doctors=total_doctors,
                             total_patients=total_patients,
                             total_appointments=total_appointments,
                             pending_appointments=pending_appointments,
                             total_payments=total_payments,
                             total_revenue=total_revenue,
                             recent_appointments=recent_appointments,
                             recent_users=recent_users,
                             recent_payments=recent_payments,
                             system_logs=system_logs)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        log_action("Dashboard error", str(e), LogLevel.ERROR)
        return redirect(url_for('home'))

@dashboard.route('/admin/users')
@login_required
@admin_required
def admin_manage_users():
    """Admin user management"""
    try:
        search_query = request.args.get('search', '').strip()
        users = User.objects.order_by('-created_at')

        if search_query:
            # Filter in Python for case-insensitive search
            all_users = list(users)
            filtered_users = []
            search_lower = search_query.lower()

            for user in all_users:
                if (search_lower in user.first_name.lower() or
                    search_lower in user.last_name.lower() or
                    search_lower in user.email.lower() or
                    search_lower in user.username.lower()):
                    filtered_users.append(user)

            users = filtered_users

        return render_template('admin/manage_users.html', users=users, search_query=search_query)
    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    """Admin create new user"""
    try:
        form = AdminUserCreationForm()
        
        if form.validate_on_submit():
            # Check if username already exists
            if User.objects(username=form.username.data).first():
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('admin/create_user.html', form=form)
            
            # Check if email already exists
            if User.objects(email=form.email.data).first():
                flash('Email already exists. Please use a different email.', 'error')
                return render_template('admin/create_user.html', form=form)
            
            # Create user based on role
            user_data = {
                'username': form.username.data,
                'email': form.email.data,
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'role': form.role.data,
                'phone': form.phone.data,
                'date_of_birth': form.date_of_birth.data,
                'address': form.address.data,
                'is_active': form.is_active.data
            }
            
            # Add role-specific fields
            if form.role.data == UserRole.DOCTOR:
                user_data.update({
                    'specialization': form.specialization.data,
                    'license_number': form.license_number.data,
                    'experience_years': form.experience_years.data,
                    'consultation_fee': form.consultation_fee.data
                })
            elif form.role.data == UserRole.PATIENT:
                user_data.update({
                    'blood_group': form.blood_group.data,
                    'emergency_contact': form.emergency_contact.data,
                    'medical_history': form.medical_history.data,
                    'insurance_provider': form.insurance_provider.data,
                    'insurance_number': form.insurance_number.data
                })
            elif form.role.data == UserRole.ADMIN:
                user_data.update({
                    'department': form.department.data,
                    'employee_id': form.employee_id.data
                })
            
            user = User(**user_data)
            user.set_password(form.password.data)
            user.save()
            
            # Create notification for the new user
            notification = Notification(
                user=user,
                title="Account Created",
                message=f"Your account has been created by an administrator. Welcome to the healthcare system!",
                notification_type=NotificationType.SYSTEM
            )
            notification.save()
            
            log_action("User created by admin", f"Created user: {user.get_full_name()}")
            flash(f'User {user.get_full_name()} created successfully!', 'success')
            return redirect(url_for('dashboard.admin_manage_users'))
        
        return render_template('admin/create_user.html', form=form)
    except Exception as e:
        flash(f'Error creating user: {str(e)}', 'error')
        log_action("User creation error", str(e), LogLevel.ERROR)
        return redirect(url_for('dashboard.admin_manage_users'))

@dashboard.route('/admin/doctors')
@login_required
@admin_required
def admin_manage_doctors():
    """Admin doctor management"""
    try:
        doctors = User.objects(role=UserRole.DOCTOR).order_by('-created_at')
        return render_template('admin/manage_doctors.html', doctors=doctors)
    except Exception as e:
        flash(f'Error loading doctors: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/doctors/<doctor_id>/profile')
@login_required
@admin_required
def admin_view_doctor_profile(doctor_id):
    """Admin view doctor profile"""
    try:
        doctor = User.objects(id=doctor_id, role=UserRole.DOCTOR).first()
        if not doctor:
            flash('Doctor not found.', 'error')
            return redirect(url_for('dashboard.admin_manage_doctors'))

        # Get doctor's statistics
        total_appointments = Appointment.objects(doctor=doctor).count()
        completed_appointments = Appointment.objects(doctor=doctor, status=AppointmentStatus.COMPLETED).count()
        total_patients = len(set([appt.patient.id for appt in Appointment.objects(doctor=doctor)]))
        total_prescriptions = Prescription.objects(doctor=doctor).count()

        # Get recent appointments (last 5)
        recent_appointments = Appointment.objects(doctor=doctor).order_by('-appointment_date').limit(5)

        # Get recent prescriptions (last 5)
        recent_prescriptions = Prescription.objects(doctor=doctor).order_by('-created_at').limit(5)

        return render_template('admin/view_doctor_profile.html',
                             doctor=doctor,
                             total_appointments=total_appointments,
                             completed_appointments=completed_appointments,
                             total_patients=total_patients,
                             total_prescriptions=total_prescriptions,
                             recent_appointments=recent_appointments,
                             recent_prescriptions=recent_prescriptions)
    except Exception as e:
        flash(f'Error loading doctor profile: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_manage_doctors'))

@dashboard.route('/admin/doctors/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_doctor():
    """Admin add new doctor"""
    try:
        form = AdminUserCreationForm()
        # Set role to doctor by default
        form.role.data = UserRole.DOCTOR.value

        if form.validate_on_submit():
            # Check if username already exists
            if User.objects(username=form.username.data).first():
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('admin/add_doctor.html', form=form)

            # Check if email already exists
            if User.objects(email=form.email.data).first():
                flash('Email already exists. Please use a different email.', 'error')
                return render_template('admin/add_doctor.html', form=form)

            # Check if license number already exists (if provided)
            if form.license_number.data and User.objects(license_number=form.license_number.data).first():
                flash('License number already exists. Please use a different license number.', 'error')
                return render_template('admin/add_doctor.html', form=form)

            # Create doctor user
            user_data = {
                'username': form.username.data,
                'email': form.email.data,
                'first_name': form.first_name.data,
                'last_name': form.last_name.data,
                'role': UserRole.DOCTOR,
                'phone': form.phone.data,
                'date_of_birth': form.date_of_birth.data,
                'address': form.address.data,
                'is_active': form.is_active.data,
                'specialization': form.specialization.data,
                'license_number': form.license_number.data,
                'experience_years': form.experience_years.data,
                'consultation_fee': form.consultation_fee.data
            }

            user = User(**user_data)
            user.set_password(form.password.data)
            user.save()

            # Create notification for the new doctor
            notification = Notification(
                user=user,
                title="Account Created",
                message=f"Your doctor account has been created by an administrator. Welcome to the healthcare system!",
                notification_type=NotificationType.SYSTEM
            )
            notification.save()

            log_action("Doctor created by admin", f"Created doctor: {user.get_full_name()}")
            flash(f'Doctor {user.get_full_name()} created successfully!', 'success')
            return redirect(url_for('dashboard.admin_manage_doctors'))

        return render_template('admin/add_doctor.html', form=form)
    except Exception as e:
        flash(f'Error creating doctor: {str(e)}', 'error')
        log_action("Doctor creation error", str(e), LogLevel.ERROR)
        return redirect(url_for('dashboard.admin_manage_doctors'))

@dashboard.route('/admin/patients')
@login_required
@admin_required
def admin_manage_patients():
    """Admin patient management"""
    try:
        patients = User.objects(role=UserRole.PATIENT).order_by('-created_at')
        return render_template('admin/manage_patients.html', patients=patients)
    except Exception as e:
        flash(f'Error loading patients: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/appointments')
@login_required
@admin_required
def admin_manage_appointments():
    """Admin appointment management"""
    try:
        search_query = request.args.get('search', '').strip()
        appointments = Appointment.objects.order_by('-appointment_date')

        if search_query:
            # Filter in Python to handle referenced fields properly
            all_appointments = list(appointments)
            filtered_appointments = []
            search_lower = search_query.lower()

            for appt in all_appointments:
                # Load referenced objects if not already loaded
                if not hasattr(appt.patient, 'first_name'):
                    appt.patient.reload()
                if not hasattr(appt.doctor, 'first_name'):
                    appt.doctor.reload()

                # Check if search query matches any field
                if (search_lower in appt.patient.first_name.lower() or
                    search_lower in appt.patient.last_name.lower() or
                    search_lower in appt.doctor.first_name.lower() or
                    search_lower in appt.doctor.last_name.lower() or
                    (appt.symptoms and search_lower in appt.symptoms.lower())):
                    filtered_appointments.append(appt)

            appointments = filtered_appointments

        return render_template('admin/manage_appointments.html', appointments=appointments, search_query=search_query)
    except Exception as e:
        flash(f'Error loading appointments: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/prescriptions')
@login_required
@admin_required
def admin_manage_prescriptions():
    """Admin prescription management"""
    try:
        search_query = request.args.get('search', '').strip()
        prescriptions = Prescription.objects.order_by('-created_at')

        if search_query:
            # Filter in Python for case-insensitive search
            all_prescriptions = list(prescriptions)
            filtered_prescriptions = []
            search_lower = search_query.lower()

            for prescription in all_prescriptions:
                # Load referenced objects if not already loaded
                if not hasattr(prescription.patient, 'first_name'):
                    prescription.patient.reload()
                if not hasattr(prescription.doctor, 'first_name'):
                    prescription.doctor.reload()

                # Check if search query matches any field
                if (search_lower in prescription.patient.first_name.lower() or
                    search_lower in prescription.patient.last_name.lower() or
                    search_lower in prescription.doctor.first_name.lower() or
                    search_lower in prescription.doctor.last_name.lower() or
                    (prescription.dosage_instructions and search_lower in prescription.dosage_instructions.lower()) or
                    any(search_lower in med.get('name', '').lower() for med in prescription.medications)):
                    filtered_prescriptions.append(prescription)

            prescriptions = filtered_prescriptions

        return render_template('admin/manage_prescriptions.html', prescriptions=prescriptions, search_query=search_query)
    except Exception as e:
        flash(f'Error loading prescriptions: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/reports')
@login_required
@admin_required
def admin_manage_reports():
    """Admin report management"""
    try:
        search_query = request.args.get('search', '').strip()
        reports = Report.objects.order_by('-created_at')

        if search_query:
            # Filter in Python for case-insensitive search
            all_reports = list(reports)
            filtered_reports = []
            search_lower = search_query.lower()

            for report in all_reports:
                # Load referenced objects if not already loaded
                if not hasattr(report.user, 'first_name'):
                    report.user.reload()
                if not hasattr(report.created_by, 'first_name'):
                    report.created_by.reload()

                # Check if search query matches any field
                if (search_lower in report.user.first_name.lower() or
                    search_lower in report.user.last_name.lower() or
                    search_lower in report.created_by.first_name.lower() or
                    search_lower in report.created_by.last_name.lower() or
                    search_lower in report.title.lower() or
                    (report.description and search_lower in report.description.lower())):
                    filtered_reports.append(report)

            reports = filtered_reports

        return render_template('admin/manage_reports.html', reports=reports, search_query=search_query)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/payments')
@login_required
@admin_required
def admin_manage_payments():
    """Admin payment management"""
    try:
        payments = Payment.objects.order_by('-created_at')
        return render_template('admin/manage_payments.html', payments=payments)
    except Exception as e:
        flash(f'Error loading payments: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    """Admin analytics dashboard"""
    try:
        # Get comprehensive analytics data
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Basic statistics
        total_users = User.objects.count()
        total_doctors = User.objects(role=UserRole.DOCTOR).count()
        total_patients = User.objects(role=UserRole.PATIENT).count()
        total_appointments = Appointment.objects.count()
        total_revenue = sum([p.amount for p in Payment.objects(status=PaymentStatus.PAID)])
        active_chats = ChatMessage.objects.count()
        
        # User growth data (last 6 months)
        user_growth_data = []
        user_growth_labels = []
        for i in range(6):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            if i == 0:
                month_end = today
            users_this_month = User.objects(created_at__gte=month_start, created_at__lt=month_end).count()
            user_growth_data.append(users_this_month)
            user_growth_labels.append(month_start.strftime('%b'))
        
        user_growth_data.reverse()
        user_growth_labels.reverse()
        
        # Appointment trends (last 7 days)
        appointment_trends_data = []
        appointment_trends_labels = []
        for i in range(7):
            day = today - timedelta(days=6-i)
            appointments_today = Appointment.objects(
                appointment_date__gte=day,
                appointment_date__lt=day + timedelta(days=1)
            ).count()
            appointment_trends_data.append(appointments_today)
            appointment_trends_labels.append(day.strftime('%a'))
        
        # User distribution
        user_distribution = {
            'patients': total_patients,
            'doctors': total_doctors,
            'admins': User.objects(role=UserRole.ADMIN).count()
        }
        
        # Recent activity
        recent_activities = []
        
        # Recent user registrations
        recent_users = User.objects.order_by('-created_at').limit(5)
        for user in recent_users:
            recent_activities.append({
                'type': 'user_registration',
                'title': 'New User Registration',
                'description': f'{user.get_full_name()} registered as a {user.role.value}',
                'timestamp': user.created_at,
                'icon': 'fas fa-user-plus'
            })
        
        # Recent appointments
        recent_appointments = Appointment.objects.order_by('-created_at').limit(5)
        for appointment in recent_appointments:
            recent_activities.append({
                'type': 'appointment',
                'title': f'Appointment {appointment.status.value.title()}',
                'description': f'{appointment.patient.get_full_name()} with Dr. {appointment.doctor.get_full_name()}',
                'timestamp': appointment.created_at,
                'icon': 'fas fa-calendar'
            })
        
        # Recent payments
        recent_payments = Payment.objects.order_by('-created_at').limit(5)
        for payment in recent_payments:
            recent_activities.append({
                'type': 'payment',
                'title': 'Payment Received',
                'description': f'${payment.amount} from {payment.patient.get_full_name()}',
                'timestamp': payment.created_at,
                'icon': 'fas fa-dollar-sign'
            })
        
        # Sort activities by timestamp
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activities = recent_activities[:10]
        
        # System health metrics
        system_health = {
            'database_status': 'Online',
            'ai_chatbot_status': 'Active',
            'email_service_status': 'Ready',
            'security_status': 'Protected'
        }
        
        # Performance metrics
        performance_metrics = {
            'avg_response_time': '120ms',
            'uptime': '99.9%',
            'error_rate': '0.1%',
            'active_sessions': User.objects.count()  # Simplified
        }
        
        log_action("Admin analytics accessed")
        
        return render_template('admin/analytics.html',
                             total_users=total_users,
                             total_doctors=total_doctors,
                             total_patients=total_patients,
                             total_appointments=total_appointments,
                             total_revenue=total_revenue,
                             active_chats=active_chats,
                             user_growth_data=user_growth_data,
                             user_growth_labels=user_growth_labels,
                             appointment_trends_data=appointment_trends_data,
                             appointment_trends_labels=appointment_trends_labels,
                             user_distribution=user_distribution,
                             recent_activities=recent_activities,
                             system_health=system_health,
                             performance_metrics=performance_metrics)
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        log_action("Analytics error", str(e), LogLevel.ERROR)
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/notifications')
@login_required
@admin_required
def admin_notifications():
    """Admin notifications"""
    try:
        notifications = Notification.objects.order_by('-created_at')
        return render_template('admin/notifications.html', notifications=notifications)
    except Exception as e:
        flash(f'Error loading notifications: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/messages')
@login_required
@admin_required
def admin_messages():
    """Admin messages - see all messages"""
    try:
        search_query = request.args.get('search', '').strip()
        messages = Message.objects.order_by('-created_at')

        if search_query:
            # Filter in Python for case-insensitive search
            all_messages = list(messages)
            filtered_messages = []
            search_lower = search_query.lower()

            for message in all_messages:
                # Load referenced objects if not already loaded
                if not hasattr(message.sender, 'first_name'):
                    message.sender.reload()
                if not hasattr(message.recipient, 'first_name'):
                    message.recipient.reload()

                # Check if search query matches any field
                sender_name = message.sender.get_full_name() if message.sender else 'System'
                recipient_name = message.recipient.get_full_name() if message.recipient else 'All Users'

                if (search_lower in sender_name.lower() or
                    search_lower in recipient_name.lower() or
                    search_lower in message.subject.lower() or
                    search_lower in message.content.lower()):
                    filtered_messages.append(message)

            messages = filtered_messages

        return render_template('admin/messages.html', messages=messages, search_query=search_query)
    except Exception as e:
        flash(f'Error loading messages: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/chats')
@login_required
@admin_required
def admin_chats():
    """Admin chat management"""
    try:
        # Get search and filter parameters
        search_query = request.args.get('search', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()

        # Start with base query
        query = ChatMessage.objects

        # Apply date filters
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(created_at__gte=from_date)
            except ValueError:
                pass  # Invalid date format, ignore

        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                # Set to end of day
                to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                query = query.filter(created_at__lte=to_date)
            except ValueError:
                pass  # Invalid date format, ignore

        # Apply search filter
        if search_query:
            # Filter in Python for case-insensitive search across user fields and message content
            all_chats = list(query.order_by('-created_at'))
            filtered_chats = []
            search_lower = search_query.lower()

            for chat in all_chats:
                # Check user name and email
                user_match = False
                if chat.user:
                    if (search_lower in chat.user.first_name.lower() or
                        search_lower in chat.user.last_name.lower() or
                        search_lower in chat.user.email.lower()):
                        user_match = True

                # Check message content
                message_match = (search_lower in chat.message.lower() or
                               search_lower in chat.response.lower())

                if user_match or message_match:
                    filtered_chats.append(chat)

            chat_messages = filtered_chats
        else:
            chat_messages = list(query.order_by('-created_at'))

        # Compute statistics to avoid generator issues in template
        total_chats = len(chat_messages)
        unique_users_count = len(set(chat.user.id for chat in chat_messages if chat.user))
        today = datetime.now().date()
        today_count = sum(1 for chat in chat_messages if chat.created_at.date() == today)

        return render_template('admin/chats.html',
                             chat_messages=chat_messages,
                             total_chats=total_chats,
                             unique_users_count=unique_users_count,
                             today_count=today_count,
                             search_query=search_query,
                             date_from=date_from,
                             date_to=date_to)
    except Exception as e:
        flash(f'Error loading chats: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/predictions')
@login_required
@admin_required
def admin_predictions():
    """Admin predictions"""
    try:
        return render_template('admin/predictions.html')
    except Exception as e:
        flash(f'Error loading predictions: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/logs')
@login_required
@admin_required
def admin_system_logs():
    """Admin system logs"""
    try:
        logs = SystemLog.objects.order_by('-created_at')
        return render_template('admin/system_logs.html', logs=logs)
    except Exception as e:
        flash(f'Error loading logs: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    """Admin settings view/save"""
    try:
        form = SettingsForm()
        if form.validate_on_submit():
            log_action(
                "Admin settings updated",
                details=f"email={form.email_notifications.data}, sms={form.sms_notifications.data}, appt={form.appointment_reminders.data}, msg={form.message_notifications.data}"
            )
            flash('Settings saved successfully!', 'success')
            return redirect(url_for('dashboard.admin_settings'))
        return render_template('admin/settings.html', form=form)
    except Exception as e:
        flash(f'Error loading settings: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/admin/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_profile():
    """Admin profile view/update"""
    try:
        form = ProfileUpdateForm(obj=current_user)
        if form.validate_on_submit():
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone = form.phone.data
            current_user.address = form.address.data
            current_user.bio = form.bio.data

            if form.profile_picture.data:
                filename = secure_filename(form.profile_picture.data.filename)
                upload_dir = os.path.join('uploads', 'profile_pictures')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                form.profile_picture.data.save(filepath)
                current_user.profile_picture = filepath

            current_user.save()
            log_action("Admin profile updated")
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard.admin_profile'))

        return render_template('admin/profile.html', form=form)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

# ============================================================================
# DOCTOR DASHBOARD ROUTES
# ============================================================================

@dashboard.route('/doctor')
@login_required
@doctor_required
def doctor_dashboard():
    """Doctor main dashboard"""
    try:
        # Get doctor's statistics
        today = datetime.now().date()
        
        # Get upcoming appointments (handle empty results gracefully)
        try:
            upcoming_appointments = Appointment.objects(
                doctor=current_user,
                appointment_date__gte=today,
                status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
            ).order_by('appointment_date').limit(10)
        except:
            upcoming_appointments = []
        
        # Get recent patients (handle empty results gracefully)
        try:
            patient_ids = Appointment.objects(doctor=current_user).distinct('patient')
            if patient_ids:
                normalized_ids = [p.id if hasattr(p, 'id') else p for p in patient_ids]
                recent_patients = User.objects(id__in=normalized_ids).limit(5)
            else:
                recent_patients = []
        except:
            recent_patients = []
        
        # Get unread messages count
        try:
            unread_messages = Message.objects(
                recipient=current_user,
                is_read=False
            ).count()
        except:
            unread_messages = 0
        
        # Get today's appointments count
        try:
            total_appointments_today = Appointment.objects(
                doctor=current_user,
                appointment_date__gte=today,
                appointment_date__lt=today + timedelta(days=1)
            ).count()
        except:
            total_appointments_today = 0
        
        log_action("Doctor dashboard accessed")
        
        return render_template('doctor/dashboard.html',
                             upcoming_appointments=upcoming_appointments,
                             recent_patients=recent_patients,
                             unread_messages=unread_messages,
                             total_appointments_today=total_appointments_today,
                             today=today)
    except Exception as e:
        current_app.logger.error(f"Doctor dashboard error: {str(e)}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('home'))

@dashboard.route('/doctor/appointments')
@login_required
@doctor_required
def doctor_appointments():
    """Doctor appointments"""
    try:
        appointments = Appointment.objects(doctor=current_user).order_by('-appointment_date')
        return render_template('doctor/appointments.html', appointments=appointments)
    except Exception as e:
        current_app.logger.error(f"Doctor appointments error: {str(e)}")
        flash(f'Error loading appointments: {str(e)}', 'error')
        return render_template('doctor/appointments.html', appointments=[])

@dashboard.route('/doctor/patients')
@login_required
@doctor_required
def doctor_patients():
    """Doctor patients"""
    try:
        today = datetime.now().date()
        patient_ids = Appointment.objects(doctor=current_user).distinct('patient')
        if patient_ids:
            normalized_ids = [p.id if hasattr(p, 'id') else p for p in patient_ids]
            patients = User.objects(id__in=normalized_ids)
        else:
            patients = []
        return render_template('doctor/patients.html', patients=patients, today=today)
    except Exception as e:
        current_app.logger.error(f"Doctor patients error: {str(e)}")
        flash(f'Error loading patients: {str(e)}', 'error')
        return render_template('doctor/patients.html', patients=[], today=datetime.now().date())

@dashboard.route('/doctor/prescriptions')
@login_required
@doctor_required
def doctor_prescriptions():
    """Doctor prescriptions"""
    try:
        prescriptions = Prescription.objects(doctor=current_user).order_by('-created_at')
        return render_template('doctor/prescriptions.html', prescriptions=prescriptions)
    except Exception as e:
        current_app.logger.error(f"Doctor prescriptions error: {str(e)}")
        flash(f'Error loading prescriptions: {str(e)}', 'error')
        return render_template('doctor/prescriptions.html', prescriptions=[])

@dashboard.route('/doctor/prescriptions/new', methods=['GET', 'POST'])
@login_required
@doctor_required
def doctor_new_prescription():
    """Create new prescription"""
    try:
        form = PrescriptionForm()
        patients = User.objects(role=UserRole.PATIENT)
        form.patient_id.choices = [(str(p.id), p.get_full_name()) for p in patients]
        
        if form.validate_on_submit():
            patient = User.objects(id=form.patient_id.data).first()
            if not patient:
                flash('Selected patient not found.', 'error')
                return redirect(url_for('dashboard.doctor_new_prescription'))
            
            # Create medication object
            medication_data = {
                'name': form.medication.data,
                'dosage': form.dosage.data,
                'frequency': form.frequency.data,
                'quantity': form.quantity.data
            }
            
            prescription = Prescription(
                patient=patient,
                doctor=current_user,
                medications=[medication_data],
                dosage_instructions=form.instructions.data,
                duration=form.duration.data,
                notes=form.notes.data
            )
            prescription.save()
            
            # Create notification for patient
            notification = Notification(
                user=patient,
                title="New Prescription",
                message=f"Dr. {current_user.get_full_name()} has prescribed new medication for you. Please check your prescriptions.",
                notification_type=NotificationType.SYSTEM,
                related_id=str(prescription.id)
            )
            notification.save()
            
            log_action("Prescription created", f"Prescription for {patient.get_full_name()}")
            flash('Prescription created successfully!', 'success')
            return redirect(url_for('dashboard.doctor_prescriptions'))
        
        return render_template('doctor/new_prescription.html', form=form)
    except Exception as e:
        current_app.logger.error(f"Doctor prescription error: {str(e)}")
        flash(f'Error creating prescription: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_prescriptions'))

@dashboard.route('/doctor/profile', methods=['GET', 'POST'])
@login_required
@doctor_required
def doctor_profile():
    """Doctor profile view/update"""
    try:
        form = DoctorProfileForm(obj=current_user)
        if form.validate_on_submit():
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone = form.phone.data
            current_user.address = form.address.data
            current_user.bio = form.bio.data
            current_user.specialization = form.specialization.data
            current_user.license_number = form.license_number.data
            current_user.experience_years = form.experience_years.data
            current_user.consultation_fee = form.consultation_fee.data
            current_user.available_days = [form.available_days.data] if form.available_days.data else []
            current_user.available_hours = form.available_hours.data

            if form.profile_picture.data:
                filename = secure_filename(form.profile_picture.data.filename)
                upload_dir = os.path.join('uploads', 'profile_pictures')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                form.profile_picture.data.save(filepath)
                current_user.profile_picture = filepath

            current_user.save()
            log_action("Doctor profile updated")
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard.doctor_profile'))

        return render_template('doctor/profile.html', form=form)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

@dashboard.route('/doctor/schedule')
@login_required
@doctor_required
def doctor_schedule():
    """Doctor schedule"""
    try:
        appointments = Appointment.objects(doctor=current_user).order_by('appointment_date')
        return render_template('doctor/schedule.html', appointments=appointments)
    except Exception as e:
        flash(f'Error loading schedule: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

@dashboard.route('/doctor/reports', methods=['GET', 'POST'])
@login_required
@doctor_required
def doctor_reports():
    """Doctor reports - view and create medical reports"""
    try:
        form = ReportForm()

        # Populate patient choices for doctors
        patients = User.objects(role=UserRole.PATIENT, is_active=True)
        form.patient_id.choices = [('', 'Select Patient')] + [(str(p.id), p.get_full_name()) for p in patients]

        if form.validate_on_submit():
            # Determine the user for the report
            if form.patient_id.data:
                patient = User.objects(id=form.patient_id.data).first()
                if not patient:
                    flash('Selected patient not found.', 'error')
                    return redirect(url_for('dashboard.doctor_reports'))
                report_user = patient
            else:
                # If no patient selected, create report for the doctor themselves
                report_user = current_user

            report = Report(
                user=report_user,
                report_type=form.report_type.data,
                title=form.title.data,
                description=form.description.data,
                created_by=current_user
            )

            if form.file.data:
                filename = secure_filename(form.file.data.filename)
                filepath = os.path.join('uploads', 'reports', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                form.file.data.save(filepath)
                report.file_path = filepath.replace('\\', '/')  # Normalize to forward slashes

            report.save()

            # Create notification for the patient if report is for a patient
            if report_user != current_user:
                notification = Notification(
                    user=report_user,
                    title="New Report Created",
                    message=f"Dr. {current_user.get_full_name()} has created a new report: {form.title.data}",
                    notification_type=NotificationType.SYSTEM,
                    related_id=str(report.id)
                )
                notification.save()

            log_action("Report created", f"Report: {form.title.data} for {report_user.get_full_name()}")
            flash('Report created successfully!', 'success')
            return redirect(url_for('dashboard.doctor_reports'))

        # Get existing reports created by the doctor
        reports = Report.objects(created_by=current_user).order_by('-created_at')

        return render_template('doctor/reports.html', reports=reports, form=form)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

@dashboard.route('/doctor/messages')
@login_required
@doctor_required
def doctor_messages():
    """Doctor messages"""
    try:
        received_messages = Message.objects(recipient=current_user).order_by('-created_at')
        sent_messages = Message.objects(sender=current_user).order_by('-created_at')
        return render_template('doctor/messages.html', 
                             received_messages=received_messages,
                             sent_messages=sent_messages)
    except Exception as e:
        flash(f'Error loading messages: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

@dashboard.route('/doctor/message/patient/<patient_id>', methods=['GET', 'POST'])
@login_required
@doctor_required
def doctor_message_patient(patient_id):
    """Doctor send message to specific patient"""
    try:
        patient = User.objects(id=patient_id, role=UserRole.PATIENT).first()
        if not patient:
            flash('Patient not found.', 'error')
            return redirect(url_for('dashboard.doctor_messages'))

        form = MessageForm()
        form.recipient_id.data = patient_id

        if form.validate_on_submit():
            message = Message(
                sender=current_user,
                recipient=patient,
                subject=form.subject.data,
                content=form.content.data
            )
            message.save()

            log_action("Message sent", f"Message to {patient.get_full_name()}")
            flash('Message sent successfully!', 'success')
            return redirect(url_for('dashboard.doctor_messages'))

        return render_template('doctor/message_patient.html', form=form, patient=patient)
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_messages'))

@dashboard.route('/doctor/patient/<patient_id>/history')
@login_required
@doctor_required
def doctor_view_patient_history(patient_id):
    """Doctor view patient medical history"""
    try:
        patient = User.objects(id=patient_id, role=UserRole.PATIENT).first()
        if not patient:
            flash('Patient not found.', 'error')
            return redirect(url_for('dashboard.doctor_patients'))

        # Get patient's completed appointments
        appointments = Appointment.objects(patient=patient, status=AppointmentStatus.COMPLETED).order_by('-appointment_date')

        # Get patient's reports
        reports = Report.objects(user=patient).order_by('-created_at')

        # Get patient's prescriptions
        prescriptions = Prescription.objects(patient=patient).order_by('-created_at')

        log_action("Viewed patient history", f"Patient: {patient.get_full_name()}")

        return render_template('doctor/patient_history.html',
                             patient=patient,
                             appointments=appointments,
                             reports=reports,
                             prescriptions=prescriptions)
    except Exception as e:
        flash(f'Error loading patient history: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_patients'))

@dashboard.route('/doctor/patient/<patient_id>/schedule-appointment', methods=['GET', 'POST'])
@login_required
@doctor_required
def doctor_schedule_appointment(patient_id):
    """Doctor schedule appointment for specific patient"""
    try:
        patient = User.objects(id=patient_id, role=UserRole.PATIENT).first()
        if not patient:
            flash('Patient not found.', 'error')
            return redirect(url_for('dashboard.doctor_patients'))

        form = AppointmentForm()
        # Pre-populate doctor as current user
        form.doctor_id.choices = [(str(current_user.id), f"Dr. {current_user.get_full_name()} - {current_user.specialization}")]
        form.doctor_id.data = str(current_user.id)

        if form.validate_on_submit():
            appointment = Appointment(
                patient=patient,
                doctor=current_user,
                appointment_date=datetime.combine(form.appointment_date.data, form.appointment_time.data),
                duration=form.duration.data,
                symptoms=form.symptoms.data
            )
            appointment.save()

            # Create notifications for both patient and doctor
            patient_notification = Notification(
                user=patient,
                title="Appointment Scheduled",
                message=f"Dr. {current_user.get_full_name()} has scheduled an appointment for you on {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')}.",
                notification_type=NotificationType.APPOINTMENT,
                related_id=str(appointment.id)
            )
            patient_notification.save()

            doctor_notification = Notification(
                user=current_user,
                title="Appointment Scheduled",
                message=f"Appointment scheduled with {patient.get_full_name()} on {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')}.",
                notification_type=NotificationType.APPOINTMENT,
                related_id=str(appointment.id)
            )
            doctor_notification.save()

            log_action("Appointment scheduled", f"Appointment with {patient.get_full_name()}")
            flash('Appointment scheduled successfully!', 'success')
            return redirect(url_for('dashboard.doctor_patients'))

        return render_template('doctor/schedule_appointment.html', form=form, patient=patient)
    except Exception as e:
        flash(f'Error scheduling appointment: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_patients'))

@dashboard.route('/doctor/chats')
@login_required
@doctor_required
def doctor_chats():
    """Doctor chats"""
    try:
        chat_messages = ChatMessage.objects(user=current_user).order_by('-created_at')
        return render_template('doctor/chats.html', chat_messages=chat_messages)
    except Exception as e:
        flash(f'Error loading chats: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

@dashboard.route('/doctor/predictions')
@login_required
@doctor_required
def doctor_predictions():
    """Doctor predictions"""
    try:
        return render_template('doctor/predictions.html')
    except Exception as e:
        flash(f'Error loading predictions: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

@dashboard.route('/doctor/notifications')
@login_required
@doctor_required
def doctor_notifications():
    """Doctor notifications"""
    try:
        notifications = Notification.objects(user=current_user).order_by('-created_at')
        return render_template('doctor/notifications.html', notifications=notifications)
    except Exception as e:
        flash(f'Error loading notifications: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

# ============================================================================
# PATIENT DASHBOARD ROUTES
# ============================================================================

@dashboard.route('/patient')
@login_required
@patient_required
def patient_dashboard():
    """Patient main dashboard"""
    try:
        # Get patient's statistics
        today = datetime.now().date()
        upcoming_appointments = Appointment.objects(
            patient=current_user,
            appointment_date__gte=today,
            status__in=[AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
        ).order_by('appointment_date').limit(5)
        
        recent_reports = Report.objects(user=current_user).order_by('-created_at').limit(5)
        recent_prescriptions = Prescription.objects(patient=current_user).order_by('-created_at').limit(5)
        
        unread_messages = Message.objects(
            recipient=current_user,
            is_read=False
        ).count()
        
        log_action("Patient dashboard accessed")
        
        return render_template('patient/dashboard.html',
                             upcoming_appointments=upcoming_appointments,
                             recent_reports=recent_reports,
                             recent_prescriptions=recent_prescriptions,
                             unread_messages=unread_messages)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('home'))

@dashboard.route('/patient/book-appointment', methods=['GET', 'POST'])
@login_required
@patient_required
def patient_book_appointment():
    """Patient book appointment"""
    try:
        form = AppointmentForm()
        doctors = User.objects(role=UserRole.DOCTOR, is_active=True)
        if doctors:
            form.doctor_id.choices = [(str(d.id), f"Dr. {d.get_full_name()} - {d.specialization}") for d in doctors]
        else:
            form.doctor_id.choices = []
        
        if form.validate_on_submit():
            doctor = User.objects(id=form.doctor_id.data).first()
            if not doctor:
                flash('Selected doctor not found.', 'error')
                return redirect(url_for('dashboard.patient_book_appointment'))
            
            appointment = Appointment(
                patient=current_user,
                doctor=doctor,
                appointment_date=datetime.combine(form.appointment_date.data, form.appointment_time.data),
                duration=form.duration.data,
                symptoms=form.symptoms.data
            )
            appointment.save()
            
            # Create notifications for both patient and doctor
            patient_notification = Notification(
                user=current_user,
                title="Appointment Booked",
                message=f"Your appointment with Dr. {doctor.get_full_name()} has been booked for {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')}.",
                notification_type=NotificationType.APPOINTMENT,
                related_id=str(appointment.id)
            )
            patient_notification.save()
            
            doctor_notification = Notification(
                user=doctor,
                title="New Appointment",
                message=f"New appointment with {current_user.get_full_name()} scheduled for {appointment.appointment_date.strftime('%B %d, %Y at %I:%M %p')}.",
                notification_type=NotificationType.APPOINTMENT,
                related_id=str(appointment.id)
            )
            doctor_notification.save()
            
            log_action("Appointment booked", f"Appointment with Dr. {doctor.get_full_name()}")
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('dashboard.patient_appointments'))
        
        return render_template('patient/book_appointment.html', form=form)
    except Exception as e:
        current_app.logger.error(f"Patient book appointment error: {str(e)}")
        flash(f'Error booking appointment: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/appointments')
@login_required
@patient_required
def patient_appointments():
    """Patient appointments"""
    try:
        appointments = Appointment.objects(patient=current_user).order_by('-appointment_date')
        return render_template('patient/appointments.html', appointments=appointments)
    except Exception as e:
        current_app.logger.error(f"Patient appointments error: {str(e)}")
        flash(f'Error loading appointments: {str(e)}', 'error')
        return render_template('patient/appointments.html', appointments=[])

@dashboard.route('/patient/history')
@login_required
@patient_required
def patient_history():
    """Patient medical history"""
    try:
        appointments = Appointment.objects(patient=current_user, status=AppointmentStatus.COMPLETED).order_by('-appointment_date')
        reports = Report.objects(user=current_user).order_by('-created_at')
        prescriptions = Prescription.objects(patient=current_user).order_by('-created_at')
        
        return render_template('patient/history.html',
                             appointments=appointments,
                             reports=reports,
                             prescriptions=prescriptions)
    except Exception as e:
        flash(f'Error loading history: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/prescriptions')
@login_required
@patient_required
def patient_prescriptions():
    """Patient prescriptions"""
    try:
        # Get prescriptions with proper reference loading
        prescriptions = Prescription.objects(patient=current_user).order_by('-created_at')
        
        # Ensure doctor references are loaded
        for prescription in prescriptions:
            if prescription.doctor:
                prescription.doctor.reload()
        
        return render_template('patient/prescriptions.html', prescriptions=prescriptions)
    except Exception as e:
        current_app.logger.error(f"Patient prescriptions error: {str(e)}")
        flash(f'Error loading prescriptions: {str(e)}', 'error')
        return render_template('patient/prescriptions.html', prescriptions=[])

@dashboard.route('/patient/profile', methods=['GET', 'POST'])
@login_required
@patient_required
def patient_profile():
    """Patient profile view/update"""
    try:
        form = PatientProfileForm(obj=current_user)
        if form.validate_on_submit():
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone = form.phone.data
            current_user.address = form.address.data
            current_user.bio = form.bio.data
            current_user.blood_group = form.blood_group.data
            current_user.emergency_contact = form.emergency_contact.data
            current_user.medical_history = form.medical_history.data
            current_user.insurance_provider = form.insurance_provider.data
            current_user.insurance_number = form.insurance_number.data

            if form.profile_picture.data:
                filename = secure_filename(form.profile_picture.data.filename)
                upload_dir = os.path.join('uploads', 'profile_pictures')
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                form.profile_picture.data.save(filepath)
                current_user.profile_picture = filepath

            current_user.save()
            log_action("Patient profile updated")
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('dashboard.patient_profile'))

        return render_template('patient/profile.html', form=form)
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/reports')
@login_required
@patient_required
def patient_reports():
    """Patient reports"""
    try:
        reports = Report.objects(user=current_user).order_by('-created_at')
        return render_template('patient/reports.html', reports=reports)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/notifications')
@login_required
@patient_required
def patient_notifications():
    """Patient notifications"""
    try:
        notifications = Notification.objects(user=current_user).order_by('-created_at')
        return render_template('patient/notifications.html', notifications=notifications)
    except Exception as e:
        flash(f'Error loading notifications: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/payments')
@login_required
@patient_required
def patient_payments():
    """Patient payments"""
    try:
        payments = Payment.objects(patient=current_user).order_by('-created_at')
        return render_template('patient/payments.html', payments=payments)
    except Exception as e:
        flash(f'Error loading payments: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/payments/new', methods=['GET', 'POST'])
@login_required
@patient_required
def patient_new_payment():
    """Create a new payment by patient"""
    try:
        form = PaymentForm()

        doctor_id = request.args.get('doctor_id')
        if doctor_id:
            doctor = User.objects(id=doctor_id, role=UserRole.DOCTOR).first()
        else:
            recent_appt = Appointment.objects(patient=current_user).order_by('-appointment_date').first()
            doctor = recent_appt.doctor if recent_appt else None

        if form.validate_on_submit():
            if not doctor:
                flash('No doctor selected or found for payment.', 'error')
                return redirect(url_for('dashboard.patient_payments'))

            payment = Payment(
                patient=current_user,
                doctor=doctor,
                amount=form.amount.data,
                payment_method=form.payment_method.data,
                notes=form.notes.data,
                status=PaymentStatus.PAID,
                payment_date=datetime.utcnow()
            )
            payment.save()

            # Create notification for doctor
            doctor_notification = Notification(
                user=doctor,
                title="Payment Received",
                message=f"Payment of ${form.amount.data} received from {current_user.get_full_name()}.",
                notification_type=NotificationType.PAYMENT,
                related_id=str(payment.id)
            )
            doctor_notification.save()

            # Create notification for patient
            patient_notification = Notification(
                user=current_user,
                title="Payment Processed",
                message=f"Your payment of ${form.amount.data} has been processed successfully.",
                notification_type=NotificationType.PAYMENT,
                related_id=str(payment.id)
            )
            patient_notification.save()

            log_action("Payment created", f"Amount: {form.amount.data}")
            flash('Payment processed successfully!', 'success')
            return redirect(url_for('dashboard.patient_payments'))

        return render_template('patient/payments.html', form=form, selected_doctor=doctor)
    except Exception as e:
        flash(f'Error processing payment: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_payments'))

@dashboard.route('/patient/messages')
@login_required
@patient_required
def patient_messages():
    """Patient messages"""
    try:
        received_messages = Message.objects(recipient=current_user).order_by('-created_at')
        sent_messages = Message.objects(sender=current_user).order_by('-created_at')
        return render_template('patient/messages.html', 
                             received_messages=received_messages,
                             sent_messages=sent_messages)
    except Exception as e:
        flash(f'Error loading messages: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/message/doctor/<doctor_id>', methods=['GET', 'POST'])
@login_required
@patient_required
def patient_message_doctor(doctor_id):
    """Patient send message to specific doctor"""
    try:
        doctor = User.objects(id=doctor_id, role=UserRole.DOCTOR).first()
        if not doctor:
            flash('Doctor not found.', 'error')
            return redirect(url_for('dashboard.patient_messages'))
        
        form = MessageForm()
        form.recipient_id.data = doctor_id
        
        if form.validate_on_submit():
            message = Message(
                sender=current_user,
                recipient=doctor,
                subject=form.subject.data,
                content=form.content.data
            )
            message.save()
            
            log_action("Message sent", f"Message to Dr. {doctor.get_full_name()}")
            flash('Message sent successfully!', 'success')
            return redirect(url_for('dashboard.patient_messages'))
        
        return render_template('patient/message_doctor.html', form=form, doctor=doctor)
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_messages'))

@dashboard.route('/patient/chats')
@login_required
@patient_required
def patient_chats():
    """Patient chats"""
    try:
        chat_messages = ChatMessage.objects(user=current_user).order_by('-created_at')
        return render_template('patient/chats.html', chat_messages=chat_messages)
    except Exception as e:
        flash(f'Error loading chats: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/patient/predictions')
@login_required
@patient_required
def patient_predictions():
    """Patient predictions"""
    try:
        return render_template('patient/predictions.html')
    except Exception as e:
        flash(f'Error loading predictions: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

# ============================================================================
# MENU ROUTES
# ============================================================================

@dashboard.route('/admin/menu')
@login_required
@admin_required
def admin_menu():
    """Admin menu page with cards for different options"""
    try:
        return render_template('admin/menu.html')
    except Exception as e:
        flash(f'Error loading admin menu: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_dashboard'))

@dashboard.route('/doctor/menu')
@login_required
@doctor_required
def doctor_menu_page():
    """Doctor menu page with cards for different options"""
    try:
        return render_template('doctor/menu.html')
    except Exception as e:
        flash(f'Error loading doctor menu: {str(e)}', 'error')
        return redirect(url_for('dashboard.doctor_dashboard'))

@dashboard.route('/patient/menu')
@login_required
@patient_required
def patient_menu():
    """Patient menu page with cards for different options"""
    try:
        return render_template('patient/menu.html')
    except Exception as e:
        flash(f'Error loading patient menu: {str(e)}', 'error')
        return redirect(url_for('dashboard.patient_dashboard'))

@dashboard.route('/guest/menu')
def guest_menu():
    """Guest menu page with cards for different options"""
    try:
        return render_template('guest/menu.html')
    except Exception as e:
        flash(f'Error loading guest menu: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

# ============================================================================
# GUEST DASHBOARD ROUTES
# ============================================================================

@dashboard.route('/guest')
def guest_dashboard():
    """Guest dashboard"""
    try:
        return render_template('guest/dashboard.html')
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('home'))

@dashboard.route('/guest/about')
def guest_about():
    """Guest about page"""
    try:
        return render_template('guest/about.html')
    except Exception as e:
        flash(f'Error loading about page: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

@dashboard.route('/guest/contact')
def guest_contact():
    """Guest contact page"""
    try:
        return render_template('guest/contact.html')
    except Exception as e:
        flash(f'Error loading contact page: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

@dashboard.route('/guest/faq')
def guest_faq():
    """Guest FAQ page"""
    try:
        return render_template('guest/faq.html')
    except Exception as e:
        flash(f'Error loading FAQ page: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

@dashboard.route('/guest/services')
def guest_services():
    """Guest services page"""
    try:
        doctors = User.objects(role=UserRole.DOCTOR, is_active=True)
        return render_template('guest/services.html', doctors=doctors)
    except Exception as e:
        flash(f'Error loading services page: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

@dashboard.route('/guest/messages')
def guest_messages():
    """Guest messages"""
    try:
        return render_template('guest/messages.html')
    except Exception as e:
        flash(f'Error loading messages: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

@dashboard.route('/guest/chats')
def guest_chats():
    """Guest chats"""
    try:
        return render_template('guest/chats.html')
    except Exception as e:
        flash(f'Error loading chats: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

@dashboard.route('/guest/predictions')
def guest_predictions():
    """Guest predictions"""
    try:
        return render_template('guest/predictions.html')
    except Exception as e:
        flash(f'Error loading predictions: {str(e)}', 'error')
        return redirect(url_for('dashboard.guest_dashboard'))

# ============================================================================
# CALL ROUTES
# ============================================================================

@dashboard.route('/calls')
@login_required
def calls():
    """Common calls route"""
    try:
        if current_user.is_admin():
            calls_list = Call.objects.order_by('-created_at')
        else:
            calls_list = Call.objects(
                Q(initiator=current_user) | Q(participants=current_user)
            ).order_by('-created_at')

        return render_template('dashboard/calls.html', calls=calls_list)
    except Exception as e:
        flash(f'Error loading calls: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard_home'))

@dashboard.route('/calls/new', methods=['GET', 'POST'])
@login_required
def new_call():
    """Start a new call"""
    try:
        if request.method == 'POST':
            call_type = request.form.get('call_type', CallType.VIDEO.value)
            participants_ids = request.form.getlist('participants')

            if not participants_ids:
                flash('Please select at least one participant.', 'error')
                return redirect(url_for('dashboard.new_call'))

            # Create unique room ID
            import uuid
            room_id = str(uuid.uuid4())

            # Get participant objects
            participants = []
            for pid in participants_ids:
                user = User.objects(id=pid).first()
                if user and user != current_user:
                    participants.append(user)

            if not participants:
                flash('No valid participants selected.', 'error')
                return redirect(url_for('dashboard.new_call'))

            # Create call
            call = Call(
                initiator=current_user,
                participants=[current_user] + participants,
                call_type=CallType(call_type),
                room_id=room_id,
                is_group_call=len(participants) > 1
            )
            call.save()

            # Create call participants
            for participant in participants:
                call_participant = CallParticipant(
                    call=call,
                    user=participant
                )
                call_participant.save()

            # Create call log
            call_log = CallLog(
                call=call,
                user=current_user,
                action="initiated"
            )
            call_log.save()

            # Create notifications for participants
            for participant in participants:
                notification = Notification(
                    user=participant,
                    title="Incoming Call",
                    message=f"{current_user.get_full_name()} is calling you ({call_type.title()} call)",
                    notification_type=NotificationType.SYSTEM,
                    related_id=str(call.id)
                )
                notification.save()

            log_action("Call initiated", f"Call type: {call_type}, Participants: {len(participants)}")
            flash('Call initiated successfully!', 'success')
            return redirect(url_for('dashboard.join_call', call_id=str(call.id)))

        # Get available participants
        if current_user.is_admin():
            available_participants = User.objects(id__ne=current_user.id, is_active=True)
        elif current_user.is_doctor():
            available_participants = User.objects(
                Q(role=UserRole.PATIENT) | Q(role=UserRole.ADMIN),
                id__ne=current_user.id,
                is_active=True
            )
        else:
            available_participants = User.objects(
                Q(role=UserRole.DOCTOR) | Q(role=UserRole.ADMIN),
                id__ne=current_user.id,
                is_active=True
            )

        return render_template('dashboard/new_call.html', available_participants=available_participants)
    except Exception as e:
        flash(f'Error creating call: {str(e)}', 'error')
        return redirect(url_for('dashboard.calls'))

@dashboard.route('/calls/<call_id>/join')
@login_required
def join_call(call_id):
    """Join a call"""
    try:
        call = Call.objects(id=call_id).first()
        if not call:
            flash('Call not found.', 'error')
            return redirect(url_for('dashboard.calls'))

        # Check if user can join this call
        if not (current_user.is_admin() or
                call.initiator == current_user or
                current_user in call.participants):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.calls'))

        # Update call status if not already started
        if call.status == CallStatus.INITIATED:
            call.status = CallStatus.RINGING
            call.start_time = datetime.utcnow()
            call.save()

        # Get or create call participant
        call_participant = CallParticipant.objects(call=call, user=current_user).first()
        if not call_participant:
            call_participant = CallParticipant(
                call=call,
                user=current_user
            )
            call_participant.save()

        # Update participant status
        call_participant.joined_at = datetime.utcnow()
        call_participant.save()

        # Create call log
        call_log = CallLog(
            call=call,
            user=current_user,
            action="joined"
        )
        call_log.save()

        log_action("Joined call", f"Call ID: {call_id}")
        return render_template('dashboard/call_room.html', call=call, call_participant=call_participant)
    except Exception as e:
        flash(f'Error joining call: {str(e)}', 'error')
        return redirect(url_for('dashboard.calls'))

@dashboard.route('/calls/<call_id>/end', methods=['POST'])
@login_required
def end_call(call_id):
    """End a call"""
    try:
        call = Call.objects(id=call_id).first()
        if not call:
            flash('Call not found.', 'error')
            return redirect(url_for('dashboard.calls'))

        # Check if user can end this call
        if not (current_user.is_admin() or
                call.initiator == current_user or
                current_user in call.participants):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.calls'))

        # Update call status
        call.status = CallStatus.ENDED
        call.end_time = datetime.utcnow()
        if call.start_time:
            call.duration = int((call.end_time - call.start_time).total_seconds())
        call.save()

        # Update all participants
        call_participants = CallParticipant.objects(call=call)
        for participant in call_participants:
            if not participant.left_at:
                participant.left_at = datetime.utcnow()
                participant.save()

        # Create call log
        call_log = CallLog(
            call=call,
            user=current_user,
            action="ended"
        )
        call_log.save()

        # Create notifications for other participants
        for participant in call.participants:
            if participant != current_user:
                notification = Notification(
                    user=participant,
                    title="Call Ended",
                    message=f"The call with {current_user.get_full_name()} has ended",
                    notification_type=NotificationType.SYSTEM,
                    related_id=str(call.id)
                )
                notification.save()

        log_action("Call ended", f"Call ID: {call_id}")
        flash('Call ended successfully!', 'success')
        return redirect(url_for('dashboard.calls'))
    except Exception as e:
        flash(f'Error ending call: {str(e)}', 'error')
        return redirect(url_for('dashboard.calls'))

@dashboard.route('/calls/<call_id>/leave', methods=['POST'])
@login_required
def leave_call(call_id):
    """Leave a call"""
    try:
        call = Call.objects(id=call_id).first()
        if not call:
            flash('Call not found.', 'error')
            return redirect(url_for('dashboard.calls'))

        # Check if user is in this call
        if not (current_user in call.participants):
            flash('You are not in this call.', 'error')
            return redirect(url_for('dashboard.calls'))

        # Update participant status
        call_participant = CallParticipant.objects(call=call, user=current_user).first()
        if call_participant:
            call_participant.left_at = datetime.utcnow()
            call_participant.save()

        # Create call log
        call_log = CallLog(
            call=call,
            user=current_user,
            action="left"
        )
        call_log.save()

        # Check if all participants have left
        active_participants = CallParticipant.objects(
            call=call,
            left_at__exists=False
        ).count()

        if active_participants == 0:
            # End the call if no one is left
            call.status = CallStatus.ENDED
            call.end_time = datetime.utcnow()
            if call.start_time:
                call.duration = int((call.end_time - call.start_time).total_seconds())
            call.save()

        log_action("Left call", f"Call ID: {call_id}")
        flash('You have left the call.', 'success')
        return redirect(url_for('dashboard.calls'))
    except Exception as e:
        flash(f'Error leaving call: {str(e)}', 'error')
        return redirect(url_for('dashboard.calls'))

@dashboard.route('/calls/<call_id>/logs')
@login_required
def call_logs(call_id):
    """View call logs"""
    try:
        call = Call.objects(id=call_id).first()
        if not call:
            flash('Call not found.', 'error')
            return redirect(url_for('dashboard.calls'))

        # Check if user has access to this call
        if not (current_user.is_admin() or
                call.initiator == current_user or
                current_user in call.participants):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.calls'))

        logs = CallLog.objects(call=call).order_by('-timestamp')
        participants = CallParticipant.objects(call=call)

        return render_template('dashboard/call_logs.html',
                             call=call,
                             logs=logs,
                             participants=participants)
    except Exception as e:
        flash(f'Error loading call logs: {str(e)}', 'error')
        return redirect(url_for('dashboard.calls'))

# ============================================================================
# COMMON ROUTES
# ============================================================================

@dashboard.route('/appointments')
@login_required
def appointments():
    """Common appointments route"""
    try:
        if current_user.is_admin():
            appointments_list = Appointment.objects.order_by('-appointment_date')
        elif current_user.is_doctor():
            appointments_list = Appointment.objects(doctor=current_user).order_by('-appointment_date')
        else:
            appointments_list = Appointment.objects(patient=current_user).order_by('-appointment_date')
        
        return render_template('dashboard/appointments.html', appointments=appointments_list)
    except Exception as e:
        flash(f'Error loading appointments: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard_home'))

@dashboard.route('/appointments/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    """Create new appointment"""
    try:
        if not current_user.is_patient():
            flash('Only patients can book appointments.', 'error')
            return redirect(url_for('dashboard.appointments'))
        
        form = AppointmentForm()
        doctors = User.objects(role=UserRole.DOCTOR, is_active=True)
        form.doctor_id.choices = [(str(d.id), f"Dr. {d.get_full_name()} - {d.specialization}") for d in doctors]
        
        if form.validate_on_submit():
            doctor = User.objects(id=form.doctor_id.data).first()
            if not doctor:
                flash('Selected doctor not found.', 'error')
                return redirect(url_for('dashboard.new_appointment'))
            
            appointment = Appointment(
                patient=current_user,
                doctor=doctor,
                appointment_date=datetime.combine(form.appointment_date.data, form.appointment_time.data),
                duration=form.duration.data,
                symptoms=form.symptoms.data
            )
            appointment.save()
            
            log_action("Appointment created", f"Appointment with Dr. {doctor.get_full_name()}")
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('dashboard.appointments'))
        
        return render_template('dashboard/new_appointment.html', form=form)
    except Exception as e:
        flash(f'Error creating appointment: {str(e)}', 'error')
        return redirect(url_for('dashboard.appointments'))

@dashboard.route('/appointments/<appointment_id>')
@login_required
def view_appointment(appointment_id):
    """View appointment details"""
    try:
        appointment = Appointment.objects(id=appointment_id).first()
        if not appointment:
            flash('Appointment not found.', 'error')
            return redirect(url_for('dashboard.appointments'))
        
        # Check if user has access to this appointment
        if not (current_user.is_admin() or 
                appointment.patient == current_user or 
                appointment.doctor == current_user):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.appointments'))
        
        return render_template('dashboard/view_appointment.html', appointment=appointment)
    except Exception as e:
        flash(f'Error loading appointment: {str(e)}', 'error')
        return redirect(url_for('dashboard.appointments'))

@dashboard.route('/appointments/<appointment_id>/update', methods=['POST'])
@login_required
def update_appointment_status(appointment_id):
    """Update appointment status"""
    try:
        appointment = Appointment.objects(id=appointment_id).first()
        if not appointment:
            flash('Appointment not found.', 'error')
            return redirect(url_for('dashboard.appointments'))
        
        # Check if user has permission to update this appointment
        if not (current_user.is_admin() or appointment.doctor == current_user):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.appointments'))
        
        new_status = request.form.get('status')
        if new_status in [status.value for status in AppointmentStatus]:
            old_status = appointment.status.value
            appointment.status = AppointmentStatus(new_status)
            appointment.save()
            
            # Create notification for patient
            patient_notification = Notification(
                user=appointment.patient,
                title="Appointment Status Updated",
                message=f"Your appointment with Dr. {appointment.doctor.get_full_name()} status has been changed from {old_status.title()} to {new_status.title()}.",
                notification_type=NotificationType.APPOINTMENT,
                related_id=str(appointment.id)
            )
            patient_notification.save()
            
            log_action("Appointment status updated", f"Status: {new_status}")
            flash('Appointment status updated successfully!', 'success')
        
        return redirect(url_for('dashboard.view_appointment', appointment_id=appointment_id))
    except Exception as e:
        flash(f'Error updating appointment: {str(e)}', 'error')
        return redirect(url_for('dashboard.appointments'))

@dashboard.route('/reports')
@login_required
def reports():
    """Common reports route"""
    try:
        if current_user.is_admin():
            reports_list = Report.objects.order_by('-created_at')
        else:
            reports_list = Report.objects(user=current_user).order_by('-created_at')
        
        return render_template('dashboard/reports.html', reports=reports_list)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard_home'))

@dashboard.route('/reports/new', methods=['GET', 'POST'])
@login_required
@doctor_required
def new_report():
    """Create new report"""
    try:
        form = ReportForm()

        # Populate patient choices for doctors
        patients = User.objects(role=UserRole.PATIENT, is_active=True)
        form.patient_id.choices = [('', 'Select Patient')] + [(str(p.id), p.get_full_name()) for p in patients]

        if form.validate_on_submit():
            # Determine the user for the report
            if form.patient_id.data:
                patient = User.objects(id=form.patient_id.data).first()
                if not patient:
                    flash('Selected patient not found.', 'error')
                    return redirect(url_for('dashboard.new_report'))
                report_user = patient
            else:
                # If no patient selected, create report for the doctor themselves
                report_user = current_user

            report = Report(
                user=report_user,
                report_type=form.report_type.data,
                title=form.title.data,
                description=form.description.data,
                created_by=current_user
            )

            if form.file.data:
                filename = secure_filename(form.file.data.filename)
                filepath = os.path.join('uploads', 'reports', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                form.file.data.save(filepath)
                report.file_path = filepath

            report.save()

            # Create notification for the patient if report is for a patient
            if report_user != current_user:
                notification = Notification(
                    user=report_user,
                    title="New Report Created",
                    message=f"Dr. {current_user.get_full_name()} has created a new report: {form.title.data}",
                    notification_type=NotificationType.SYSTEM,
                    related_id=str(report.id)
                )
                notification.save()

            log_action("Report created", f"Report: {form.title.data} for {report_user.get_full_name()}")
            flash('Report created successfully!', 'success')
            return redirect(url_for('dashboard.reports'))

        return render_template('dashboard/new_report.html', form=form)
    except Exception as e:
        flash(f'Error creating report: {str(e)}', 'error')
        return redirect(url_for('dashboard.new_report'))

@dashboard.route('/reports/<report_id>')
@login_required
def view_report(report_id):
    """View report details"""
    try:
        report = Report.objects(id=report_id).first()
        if not report:
            flash('Report not found.', 'error')
            return redirect(url_for('dashboard.reports'))
        
        # Check if user has access to this report
        if not (current_user.is_admin() or report.user == current_user):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.reports'))
        
        return render_template('dashboard/view_report.html', report=report)
    except Exception as e:
        flash(f'Error loading report: {str(e)}', 'error')
        return redirect(url_for('dashboard.reports'))

@dashboard.route('/messages')
@login_required
def messages():
    """Common messages route"""
    try:
        received_messages = Message.objects(recipient=current_user).order_by('-created_at')
        sent_messages = Message.objects(sender=current_user).order_by('-created_at')

        # Get all users except current user for call participants
        all_users = User.objects(id__ne=current_user.id, is_active=True)

        return render_template('dashboard/messages.html',
                             received_messages=received_messages,
                             sent_messages=sent_messages,
                             all_users=all_users)
    except Exception as e:
        flash(f'Error loading messages: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard_home'))

@dashboard.route('/messages/new', methods=['GET', 'POST'])
@login_required
def new_message():
    """Send new message"""
    try:
        form = MessageForm()
        
        # Populate recipient choices based on user role
        if current_user.is_admin():
            recipients = User.objects(id__ne=current_user.id)
        elif current_user.is_doctor():
            recipients = User.objects(
                Q(role=UserRole.PATIENT) | Q(role=UserRole.ADMIN)
            )
        else:
            recipients = User.objects(
                Q(role=UserRole.DOCTOR) | Q(role=UserRole.ADMIN)
            )
        
        form.recipient_id.choices = [(str(r.id), r.get_full_name()) for r in recipients]
        
        if form.validate_on_submit():
            recipient = User.objects(id=form.recipient_id.data).first()
            if not recipient:
                flash('Selected recipient not found.', 'error')
                return redirect(url_for('dashboard.new_message'))
            
            message = Message(
                sender=current_user,
                recipient=recipient,
                subject=form.subject.data,
                content=form.content.data
            )
            message.save()
            
            # Create notification for recipient
            notification = Notification(
                user=recipient,
                title="New Message",
                message=f"You have received a new message from {current_user.get_full_name()}: {form.subject.data}",
                notification_type=NotificationType.MESSAGE,
                related_id=str(message.id)
            )
            notification.save()
            
            log_action("Message sent", f"Message to {recipient.get_full_name()}")
            flash('Message sent successfully!', 'success')
            return redirect(url_for('dashboard.messages'))
        
        return render_template('dashboard/new_message.html', form=form)
    except Exception as e:
        flash(f'Error sending message: {str(e)}', 'error')
        return redirect(url_for('dashboard.messages'))

@dashboard.route('/messages/<message_id>')
@login_required
def view_message(message_id):
    """View message details"""
    try:
        message = Message.objects(id=message_id).first()
        if not message:
            flash('Message not found.', 'error')
            return redirect(url_for('dashboard.messages'))
        
        # Check if user has access to this message
        if not (message.sender == current_user or message.recipient == current_user):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.messages'))
        
        # Mark as read if recipient is viewing
        if message.recipient == current_user and not message.is_read:
            message.mark_as_read()
        
        return render_template('dashboard/view_message.html', message=message)
    except Exception as e:
        flash(f'Error loading message: {str(e)}', 'error')
        return redirect(url_for('dashboard.messages'))

# ============================================================================
# ADMIN MANAGEMENT ROUTES
# ============================================================================

@dashboard.route('/admin/users/<user_id>/toggle')
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    try:
        user = User.objects(id=user_id).first()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('dashboard.admin_manage_users'))
        user.is_active = not user.is_active
        user.save()
        
        status = "activated" if user.is_active else "deactivated"
        log_action("User status toggled", f"User {user.get_full_name()} {status}")
        flash(f'User {user.get_full_name()} has been {status}.', 'success')
        return redirect(url_for('dashboard.admin_manage_users'))
    except Exception as e:
        flash(f'Error updating user status: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_manage_users'))

@dashboard.route('/admin/users/<user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    try:
        user = User.objects(id=user_id).first()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('dashboard.admin_manage_users'))
        if user.id == current_user.id:
            flash('You cannot delete your own account.', 'error')
            return redirect(url_for('dashboard.admin_manage_users'))
        
        user_name = user.get_full_name()
        user.delete()
        
        log_action("User deleted", f"User {user_name} deleted")
        flash(f'User {user_name} has been deleted.', 'success')
        return redirect(url_for('dashboard.admin_manage_users'))
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'error')
        return redirect(url_for('dashboard.admin_manage_users'))

# ============================================================================
# API ROUTES
# ============================================================================

@dashboard.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notification_read():
    """Mark notification as read"""
    try:
        notification_id = request.json.get('notification_id')
        notification = Notification.objects(id=notification_id, user=current_user).first()
        
        if notification:
            notification.mark_as_read()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Notification not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard.route('/api/search', methods=['POST'])
@login_required
def search():
    """Search functionality"""
    try:
        query = request.json.get('query', '')
        category = request.json.get('category', 'all')
        
        results = {}
        
        if category in ['all', 'doctors']:
            doctors = User.objects(
                Q(role=UserRole.DOCTOR) & 
                (Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(specialization__icontains=query))
            )
            results['doctors'] = [{'id': str(d.id), 'name': d.get_full_name(), 'specialization': d.specialization} for d in doctors]
        
        if category in ['all', 'appointments']:
            appointments = Appointment.objects(
                (Q(patient=current_user) | Q(doctor=current_user)) &
                (Q(symptoms__icontains=query) | Q(notes__icontains=query))
            )
            results['appointments'] = [{'id': str(a.id), 'date': a.appointment_date.strftime('%Y-%m-%d %H:%M')} for a in appointments]
        
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard.route('/api/messages/delete', methods=['POST'])
@login_required
def delete_message():
    """Delete message"""
    try:
        message_id = request.json.get('message_id')

        # Check if user has permission to delete this message
        if current_user.is_admin():
            message = Message.objects(id=message_id).first()
        else:
            message = Message.objects(
                Q(id=message_id) & (Q(sender=current_user) | Q(recipient=current_user))
            ).first()

        if message:
            message.delete()
            log_action("Message deleted", f"Message ID: {message_id}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Message not found or access denied'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard.route('/api/create_call', methods=['POST'])
@login_required
def create_call():
    """Create a new call"""
    try:
        data = request.get_json()
        participants_ids = data.get('participants', [])
        call_type = data.get('call_type', 'video')
        call_title = data.get('call_title', 'Video Call')
        notes = data.get('notes', '')

        if not participants_ids:
            return jsonify({'success': False, 'error': 'No participants specified'}), 400

        # Create unique room ID
        import uuid
        room_id = str(uuid.uuid4())

        # Get participant objects
        participants = []
        for pid in participants_ids:
            user = User.objects(id=pid).first()
            if user and user != current_user:
                participants.append(user)

        if not participants:
            return jsonify({'success': False, 'error': 'No valid participants found'}), 400

        # Create call
        call = Call(
            initiator=current_user,
            participants=[current_user] + participants,
            call_type=CallType(call_type),
            room_id=room_id,
            is_group_call=len(participants) > 1,
            call_title=call_title,
            notes=notes
        )
        call.save()

        # Create call participants
        for participant in participants:
            call_participant = CallParticipant(
                call=call,
                user=participant
            )
            call_participant.save()

        # Create call log
        call_log = CallLog(
            call=call,
            user=current_user,
            action="initiated"
        )
        call_log.save()

        # Create notifications for participants
        for participant in participants:
            notification = Notification(
                user=participant,
                title="Incoming Call",
                message=f"{current_user.get_full_name()} is calling you ({call_type.title()} call)",
                notification_type=NotificationType.SYSTEM,
                related_id=str(call.id)
            )
            notification.save()

        log_action("Call initiated", f"Call type: {call_type}, Participants: {len(participants)}")

        return jsonify({
            'success': True,
            'call': {
                'id': str(call.id),
                'room_id': room_id,
                'call_type': call_type,
                'participants': [{'id': str(p.id), 'name': p.get_full_name()} for p in participants]
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error creating call: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    """Send a new message"""
    try:
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        subject = data.get('subject', '')
        content = data.get('content', '')

        if not recipient_id or not content:
            return jsonify({'success': False, 'error': 'Recipient and content are required'}), 400

        recipient = User.objects(id=recipient_id).first()
        if not recipient:
            return jsonify({'success': False, 'error': 'Recipient not found'}), 404

        # Check if user can send message to this recipient
        if current_user.is_patient() and not recipient.is_doctor() and not recipient.is_admin():
            return jsonify({'success': False, 'error': 'Patients can only message doctors or admins'}), 403

        if current_user.is_doctor() and not recipient.is_patient() and not recipient.is_admin():
            return jsonify({'success': False, 'error': 'Doctors can only message patients or admins'}), 403

        message = Message(
            sender=current_user,
            recipient=recipient,
            subject=subject,
            content=content
        )
        message.save()

        # Create notification for recipient
        notification = Notification(
            user=recipient,
            title="New Message",
            message=f"You have received a new message from {current_user.get_full_name()}: {subject}",
            notification_type=NotificationType.MESSAGE,
            related_id=str(message.id)
        )
        notification.save()

        log_action("Message sent", f"To: {recipient.get_full_name()}")

        return jsonify({
            'success': True,
            'message': {
                'id': str(message.id),
                'subject': subject,
                'content': content,
                'created_at': message.created_at.isoformat()
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error sending message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard.route('/api/messages/reply/<message_id>', methods=['POST'])
@login_required
def reply_message(message_id):
    """Reply to a message"""
    try:
        data = request.get_json()
        content = data.get('content', '')

        if not content:
            return jsonify({'success': False, 'error': 'Reply content is required'}), 400

        # Get original message
        original_message = Message.objects(id=message_id).first()
        if not original_message:
            return jsonify({'success': False, 'error': 'Original message not found'}), 404

        # Check if user can reply to this message
        if not (original_message.sender == current_user or original_message.recipient == current_user):
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        # Determine recipient for reply
        if original_message.sender == current_user:
            recipient = original_message.recipient
        else:
            recipient = original_message.sender

        # Create reply subject
        reply_subject = original_message.subject
        if not reply_subject.startswith('Re: '):
            reply_subject = f"Re: {reply_subject}"

        message = Message(
            sender=current_user,
            recipient=recipient,
            subject=reply_subject,
            content=content
        )
        message.save()

        # Create notification for recipient
        notification = Notification(
            user=recipient,
            title="New Reply",
            message=f"You have received a reply from {current_user.get_full_name()}: {reply_subject}",
            notification_type=NotificationType.MESSAGE,
            related_id=str(message.id)
        )
        notification.save()

        log_action("Message replied", f"To: {recipient.get_full_name()}")

        return jsonify({
            'success': True,
            'message': {
                'id': str(message.id),
                'subject': reply_subject,
                'content': content,
                'created_at': message.created_at.isoformat()
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error replying to message: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dashboard.route('/api/prescriptions/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_prescription_status():
    """Toggle prescription active status"""
    try:
        prescription_id = request.json.get('prescription_id')
        prescription = Prescription.objects(id=prescription_id).first()

        if prescription:
            prescription.is_active = not prescription.is_active
            prescription.save()

            status = "activated" if prescription.is_active else "deactivated"
            log_action("Prescription status toggled", f"Prescription {prescription_id} {status}")
            return jsonify({'success': True, 'is_active': prescription.is_active})
        else:
            return jsonify({'success': False, 'error': 'Prescription not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard.route('/api/welcome')
def welcome():
    """Welcome API endpoint that logs requests and returns a welcome message"""
    try:
        # Log the request with metadata
        log_action("Welcome API accessed", f"Method: {request.method}, Path: {request.path}")

        # Return JSON response with welcome message
        return jsonify({'message': 'Welcome to the Flask API Service!'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@dashboard.route('/api/chat/<chat_id>')
@login_required
def get_chat_message(chat_id):
    """Get individual chat message details"""
    try:
        chat = ChatMessage.objects(id=chat_id).first()
        if not chat:
            return jsonify({'success': False, 'error': 'Chat message not found'}), 404

        # Check if user has permission to view this chat
        if not (current_user.is_admin() or chat.user == current_user):
            return jsonify({'success': False, 'error': 'Access denied'}), 403

        return jsonify({
            'success': True,
            'id': str(chat.id),
            'user': {
                'id': str(chat.user.id) if chat.user else None,
                'name': chat.user.get_full_name() if chat.user else 'Guest User',
                'email': chat.user.email if chat.user else 'guest@system.com'
            },
            'message': chat.message,
            'response': chat.response,
            'created_at': chat.created_at.isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# FILE SERVING ROUTES
# ============================================================================

@dashboard.route('/uploads/<path:filename>')
@login_required
def serve_uploaded_file(filename):
    """Serve uploaded files with proper access control"""
    try:
        # Security check: prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.dashboard_home'))

        # Extract file path components
        path_parts = filename.split('/')
        if len(path_parts) < 2:
            flash('Invalid file path.', 'error')
            return redirect(url_for('dashboard.dashboard_home'))

        file_type = path_parts[0]  # 'reports', 'profile_pictures', etc.

        # Check permissions based on file type
        if file_type == 'reports':
            # For reports, check if user has access to the specific report
            full_path = f'uploads/{filename}'
            report = Report.objects(file_path=full_path).first()
            if not report:
                flash('File not found.', 'error')
                return redirect(url_for('dashboard.dashboard_home'))

            # Check if user has permission to access this report
            if not (current_user.is_admin() or report.user == current_user or report.created_by == current_user):
                flash('Access denied.', 'error')
                return redirect(url_for('dashboard.dashboard_home'))

        elif file_type == 'profile_pictures':
            # For profile pictures, check if user owns the picture or is admin
            if not current_user.is_admin():
                # Check if this is the user's own profile picture
                full_path = f'uploads/{filename}'
                if hasattr(current_user, 'profile_picture') and current_user.profile_picture == full_path:
                    pass  # Allow access
                else:
                    flash('Access denied.', 'error')
                    return redirect(url_for('dashboard.dashboard_home'))

        # If all checks pass, serve the file
        from flask import send_from_directory
        return send_from_directory('uploads', filename, as_attachment=False)

    except Exception as e:
        flash(f'Error accessing file: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard_home'))

@dashboard.route('/dashboard/uploads/<path:filename>/download')
@login_required
def download_uploaded_file(filename):
    """Download uploaded files with proper access control"""
    try:
        # Security check: only allow access to files in uploads directory
        if not filename.startswith('uploads/'):
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard.dashboard_home'))

        # Extract file path components
        path_parts = filename.split('/')
        if len(path_parts) < 2:
            flash('Invalid file path.', 'error')
            return redirect(url_for('dashboard.dashboard_home'))

        file_type = path_parts[1]  # 'reports', 'profile_pictures', etc.

        # Check permissions based on file type
        if file_type == 'reports':
            # For reports, check if user has access to the specific report
            report = Report.objects(file_path=filename).first()
            if not report:
                flash('File not found.', 'error')
                return redirect(url_for('dashboard.dashboard_home'))

            # Check if user has permission to access this report
            if not (current_user.is_admin() or report.user == current_user or report.created_by == current_user):
                flash('Access denied.', 'error')
                return redirect(url_for('dashboard.dashboard_home'))

        elif file_type == 'profile_pictures':
            # For profile pictures, check if user owns the picture or is admin
            if not current_user.is_admin():
                # Check if this is the user's own profile picture
                if hasattr(current_user, 'profile_picture') and current_user.profile_picture == filename:
                    pass  # Allow access
                else:
                    flash('Access denied.', 'error')
                    return redirect(url_for('dashboard.dashboard_home'))

        # If all checks pass, serve the file as attachment for download
        from flask import send_from_directory
        directory = os.path.dirname(filename)
        filename_only = os.path.basename(filename)

        return send_from_directory(directory, filename_only, as_attachment=True)

    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('dashboard.dashboard_home'))
