from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from models import User, UserRole
from forms import (
    LoginForm, RegistrationForm, DoctorRegistrationForm, PatientRegistrationForm, 
    AdminRegistrationForm, PasswordChangeForm, PasswordResetForm, PasswordResetConfirmForm,
    EmailVerificationForm, ResendVerificationForm
)
from datetime import datetime
import os

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Account is deactivated. Please contact administrator.', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.save()
        
        # Redirect based on user role
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            if user.role == UserRole.ADMIN:
                next_page = url_for('dashboard.admin_dashboard')
            elif user.role == UserRole.DOCTOR:
                next_page = url_for('dashboard.doctor_dashboard')
            elif user.role == UserRole.PATIENT:
                next_page = url_for('dashboard.patient_dashboard')
            else:
                next_page = url_for('dashboard.guest_dashboard')
        
        flash(f'Welcome back, {user.get_full_name()}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Separate admin login route with enhanced security"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('dashboard.admin_dashboard'))
        else:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.admin_login'))
        
        if not user.is_active:
            flash('Account is deactivated. Please contact administrator.', 'error')
            return redirect(url_for('auth.admin_login'))
        
        if not user.is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.admin_login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.save()
        
        # Redirect to admin dashboard
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.admin_dashboard')
        
        flash(f'Welcome back, Admin {user.get_full_name()}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/admin_login.html', title='Admin Login', form=form)

@auth.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if current_user.is_authenticated:
        if current_user.is_doctor():
            return redirect(url_for('dashboard.doctor_dashboard'))
        else:
            flash('Access denied. Doctor account required.', 'error')
            return redirect(url_for('auth.login'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.doctor_login'))

        if not user.is_active:
            flash('Account is deactivated. Please contact administrator.', 'error')
            return redirect(url_for('auth.doctor_login'))

        if not user.is_doctor():
            flash('Access denied. Doctor account required.', 'error')
            return redirect(url_for('auth.doctor_login'))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        user.save()

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.doctor_dashboard')

        flash(f'Welcome back, Dr. {user.get_full_name()}!', 'success')
        return redirect(next_page)

    return render_template('auth/doctor_login.html', title='Doctor Login', form=form)

@auth.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    if current_user.is_authenticated:
        if current_user.is_patient():
            return redirect(url_for('dashboard.patient_dashboard'))
        else:
            flash('Access denied. Patient account required.', 'error')
            return redirect(url_for('auth.login'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.objects(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.patient_login'))

        if not user.is_active:
            flash('Account is deactivated. Please contact administrator.', 'error')
            return redirect(url_for('auth.patient_login'))

        if not user.is_patient():
            flash('Access denied. Patient account required.', 'error')
            return redirect(url_for('auth.patient_login'))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        user.save()

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard.patient_dashboard')

        flash(f'Welcome back, {user.get_full_name()}!', 'success')
        return redirect(next_page)

    return render_template('auth/patient_login.html', title='Patient Login', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if username already exists
            if User.objects(username=form.username.data).first():
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('auth/register.html', title='Register', form=form)
            
            # Check if email already exists
            if User.objects(email=form.email.data).first():
                flash('Email already exists. Please use a different email.', 'error')
                return render_template('auth/register.html', title='Register', form=form)
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=UserRole(form.role.data),
                phone=form.phone.data,
                date_of_birth=form.date_of_birth.data,
                address=form.address.data
            )
            user.set_password(form.password.data)
            user.save()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')
            return render_template('auth/register.html', title='Register', form=form)
    
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/register/doctor', methods=['GET', 'POST'])
def register_doctor():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    form = DoctorRegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if username already exists
            if User.objects(username=form.username.data).first():
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('auth/register_doctor.html', title='Register as Doctor', form=form)
            
            # Check if email already exists
            if User.objects(email=form.email.data).first():
                flash('Email already exists. Please use a different email.', 'error')
                return render_template('auth/register_doctor.html', title='Register as Doctor', form=form)
            
            # Check if license number already exists
            if User.objects(license_number=form.license_number.data).first():
                flash('License number already exists. Please use a different license number.', 'error')
                return render_template('auth/register_doctor.html', title='Register as Doctor', form=form)
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=UserRole.DOCTOR,
                phone=form.phone.data,
                date_of_birth=form.date_of_birth.data,
                address=form.address.data,
                specialization=form.specialization.data,
                license_number=form.license_number.data,
                experience_years=form.experience_years.data,
                consultation_fee=form.consultation_fee.data
            )
            user.set_password(form.password.data)
            user.save()
            
            flash('Doctor registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Doctor registration failed: {str(e)}', 'error')
            return render_template('auth/register_doctor.html', title='Register as Doctor', form=form)
    
    return render_template('auth/register_doctor.html', title='Register as Doctor', form=form)

@auth.route('/register/patient', methods=['GET', 'POST'])
def register_patient():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    form = PatientRegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if username already exists
            if User.objects(username=form.username.data).first():
                flash('Username already exists. Please choose a different one.', 'error')
                return render_template('auth/register_patient.html', title='Register as Patient', form=form)
            
            # Check if email already exists
            if User.objects(email=form.email.data).first():
                flash('Email already exists. Please use a different email.', 'error')
                return render_template('auth/register_patient.html', title='Register as Patient', form=form)
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role=UserRole.PATIENT,
                phone=form.phone.data,
                date_of_birth=form.date_of_birth.data,
                address=form.address.data,
                blood_group=form.blood_group.data,
                emergency_contact=form.emergency_contact.data,
                medical_history=form.medical_history.data,
                allergies=form.allergies.data,
                insurance_provider=form.insurance_provider.data
            )
            user.set_password(form.password.data)
            user.save()
            
            flash('Patient registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Patient registration failed: {str(e)}', 'error')
            return render_template('auth/register_patient.html', title='Register as Patient', form=form)
    
    return render_template('auth/register_patient.html', title='Register as Patient', form=form)

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(form.new_password.data)
        current_user.save()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('dashboard.dashboard_home'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.objects(email=email).first()
        if user:
            # Here you would typically send a password reset email
            # For now, we'll just show a message
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        else:
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', title='Forgot Password')

@auth.route('/register/admin', methods=['GET', 'POST'])
def register_admin():
    flash('Admin self-registration is disabled. Please contact an existing administrator.', 'info')
    return redirect(url_for('auth.admin_login'))

@auth.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    form = EmailVerificationForm()
    if form.validate_on_submit():
        # In a real application, you would validate the verification code
        # For now, we'll just show a success message
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/verify_email.html', title='Verify Email', form=form)

@auth.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    form = ResendVerificationForm()
    if form.validate_on_submit():
        # In a real application, you would send a new verification email
        flash('Verification code sent to your email.', 'info')
        return redirect(url_for('auth.verify_email'))
    
    return render_template('auth/resend_verification.html', title='Resend Verification', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard_home'))
    
    form = PasswordResetConfirmForm()
    if form.validate_on_submit():
        # In a real application, you would validate the token and reset the password
        flash('Password reset successfully! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form, token=token)

@auth.route('/account-settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('auth.account_settings'))
        
        current_user.set_password(form.new_password.data)
        current_user.save()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('auth.account_settings'))
    
    return render_template('auth/account_settings.html', title='Account Settings', form=form)

@auth.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    if request.form.get('confirm_delete') == 'DELETE':
        # In a real application, you would soft delete or archive the account
        current_user.is_active = False
        current_user.save()
        logout_user()
        flash('Your account has been deactivated.', 'info')
        return redirect(url_for('home'))
    
    flash('Account deletion cancelled.', 'info')
    return redirect(url_for('auth.account_settings'))
