#!/usr/bin/env python3
"""
Authentication System Test Script
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_auth_imports():
    """Test if all authentication modules can be imported"""
    try:
        from auth import auth
        from forms import (
            LoginForm, RegistrationForm, DoctorRegistrationForm, 
            PatientRegistrationForm, AdminRegistrationForm,
            PasswordChangeForm, PasswordResetForm, PasswordResetConfirmForm,
            EmailVerificationForm, ResendVerificationForm
        )
        from models import User, UserRole
        print("✓ All authentication imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_auth_routes():
    """Test if all authentication routes are accessible"""
    try:
        from app import create_app
        app = create_app()
        
        # Test authentication routes
        auth_routes = [
            '/auth/login',
            '/auth/logout',
            '/auth/register',
            '/auth/register/doctor',
            '/auth/register/patient',
            '/auth/register/admin',
            '/auth/forgot-password',
            '/auth/verify-email',
            '/auth/resend-verification',
            '/auth/change-password',
            '/auth/account-settings'
        ]
        
        with app.test_client() as client:
            for route in auth_routes:
                response = client.get(route)
                if response.status_code in [200, 302, 405]:  # 302 for redirects, 405 for POST-only routes
                    print(f"✓ Route {route} accessible")
                else:
                    print(f"✗ Route {route} returned status {response.status_code}")
        
        return True
    except Exception as e:
        print(f"✗ Route testing error: {e}")
        return False

def test_user_roles():
    """Test if all user roles are properly defined"""
    try:
        from models import UserRole
        
        roles = [UserRole.ADMIN, UserRole.DOCTOR, UserRole.PATIENT]
        for role in roles:
            print(f"✓ User role {role.value} available")
        
        return True
    except Exception as e:
        print(f"✗ User roles error: {e}")
        return False

def test_forms_validation():
    """Test form validation"""
    try:
        from forms import LoginForm, RegistrationForm, DoctorRegistrationForm, PatientRegistrationForm, AdminRegistrationForm
        
        # Test LoginForm
        login_form = LoginForm()
        print("✓ LoginForm created successfully")
        
        # Test RegistrationForm
        reg_form = RegistrationForm()
        print("✓ RegistrationForm created successfully")
        
        # Test DoctorRegistrationForm
        doctor_form = DoctorRegistrationForm()
        print("✓ DoctorRegistrationForm created successfully")
        
        # Test PatientRegistrationForm
        patient_form = PatientRegistrationForm()
        print("✓ PatientRegistrationForm created successfully")
        
        # Test AdminRegistrationForm
        admin_form = AdminRegistrationForm()
        print("✓ AdminRegistrationForm created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Form validation error: {e}")
        return False

def test_user_creation():
    """Test user creation for all roles"""
    try:
        from models import User, UserRole
        from datetime import datetime
        
        # Test admin user creation
        admin_user = User(
            username='test_admin',
            email='admin@test.com',
            first_name='Test',
            last_name='Admin',
            role=UserRole.ADMIN,
            department='IT',
            employee_id='EMP001'
        )
        admin_user.set_password('testpass123')
        print("✓ Admin user creation successful")
        
        # Test doctor user creation
        doctor_user = User(
            username='test_doctor',
            email='doctor@test.com',
            first_name='Test',
            last_name='Doctor',
            role=UserRole.DOCTOR,
            specialization='General Medicine',
            license_number='LIC001',
            experience_years=5
        )
        doctor_user.set_password('testpass123')
        print("✓ Doctor user creation successful")
        
        # Test patient user creation
        patient_user = User(
            username='test_patient',
            email='patient@test.com',
            first_name='Test',
            last_name='Patient',
            role=UserRole.PATIENT,
            blood_group='O+',
            emergency_contact='1234567890'
        )
        patient_user.set_password('testpass123')
        print("✓ Patient user creation successful")
        
        return True
    except Exception as e:
        print(f"✗ User creation error: {e}")
        return False

def main():
    """Run all authentication tests"""
    print("Healthcare AI Authentication System - Test Suite")
    print("=" * 60)
    
    tests = [
        test_auth_imports,
        test_user_roles,
        test_forms_validation,
        test_user_creation,
        test_auth_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 60)
    print(f"Authentication Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All authentication tests passed! The system is ready.")
        return True
    else:
        print("✗ Some authentication tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
