#!/usr/bin/env python3
"""
Comprehensive test script for the Healthcare AI Chatbot system.
Tests all major functionality including user creation, notifications, messages, and prescriptions.
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_system():
    """Test the entire system functionality"""
    print("🏥 Healthcare AI Chatbot System - Comprehensive Test")
    print("=" * 60)
    
    # Test results
    results = {
        'admin_user_creation': False,
        'notification_system': False,
        'message_system': False,
        'prescription_system': False,
        'appointment_system': False,
        'payment_system': False,
        'role_permissions': False
    }
    
    try:
        # Test 1: Admin User Creation
        print("\n1. Testing Admin User Creation...")
        try:
            from models import User, UserRole, Notification, NotificationType
            from forms import AdminUserCreationForm
            
            # Test form creation
            form = AdminUserCreationForm()
            print("✓ AdminUserCreationForm created successfully")
            
            # Test user creation with all roles
            test_users = [
                {
                    'username': 'test_admin_2',
                    'email': 'admin2@test.com',
                    'first_name': 'Test',
                    'last_name': 'Admin',
                    'role': UserRole.ADMIN,
                    'department': 'IT',
                    'employee_id': 'EMP002'
                },
                {
                    'username': 'test_doctor_2',
                    'email': 'doctor2@test.com',
                    'first_name': 'Test',
                    'last_name': 'Doctor',
                    'role': UserRole.DOCTOR,
                    'specialization': 'Cardiology',
                    'license_number': 'LIC002',
                    'experience_years': 10
                },
                {
                    'username': 'test_patient_2',
                    'email': 'patient2@test.com',
                    'first_name': 'Test',
                    'last_name': 'Patient',
                    'role': UserRole.PATIENT,
                    'blood_group': 'A+',
                    'emergency_contact': '1234567890'
                }
            ]
            
            for user_data in test_users:
                user = User(**user_data)
                user.set_password('testpass123')
                print(f"✓ {user_data['role'].value.title()} user created successfully")
            
            results['admin_user_creation'] = True
            print("✅ Admin User Creation: PASSED")
            
        except Exception as e:
            print(f"❌ Admin User Creation: FAILED - {e}")
        
        # Test 2: Notification System
        print("\n2. Testing Notification System...")
        try:
            # Test notification creation
            test_user = User.objects(email='admin@healthcare.com').first()
            if test_user:
                notification = Notification(
                    user=test_user,
                    title="Test Notification",
                    message="This is a test notification to verify the system is working.",
                    notification_type=NotificationType.SYSTEM
                )
                notification.save()
                print("✓ Notification created successfully")
                
                # Test notification retrieval
                notifications = Notification.objects(user=test_user)
                print(f"✓ Found {notifications.count()} notifications for user")
                
                # Test notification marking as read
                notification.mark_as_read()
                print("✓ Notification marked as read")
                
                results['notification_system'] = True
                print("✅ Notification System: PASSED")
            else:
                print("❌ Test user not found")
                
        except Exception as e:
            print(f"❌ Notification System: FAILED - {e}")
        
        # Test 3: Message System
        print("\n3. Testing Message System...")
        try:
            from models import Message
            
            # Test message creation
            admin_user = User.objects(email='admin@healthcare.com').first()
            doctor_user = User.objects(email='doctor@healthcare.com').first()
            
            if admin_user and doctor_user:
                message = Message(
                    sender=admin_user,
                    recipient=doctor_user,
                    subject="Test Message",
                    content="This is a test message to verify the messaging system."
                )
                message.save()
                print("✓ Message created successfully")
                
                # Test message retrieval
                sent_messages = Message.objects(sender=admin_user)
                received_messages = Message.objects(recipient=doctor_user)
                print(f"✓ Found {sent_messages.count()} sent messages")
                print(f"✓ Found {received_messages.count()} received messages")
                
                results['message_system'] = True
                print("✅ Message System: PASSED")
            else:
                print("❌ Required users not found")
                
        except Exception as e:
            print(f"❌ Message System: FAILED - {e}")
        
        # Test 4: Prescription System
        print("\n4. Testing Prescription System...")
        try:
            from models import Prescription
            
            admin_user = User.objects(email='admin@healthcare.com').first()
            patient_user = User.objects(email='patient@healthcare.com').first()
            
            if admin_user and patient_user:
                # Test prescription creation
                medication_data = {
                    'name': 'Test Medication',
                    'dosage': '10mg',
                    'frequency': 'Twice daily',
                    'quantity': '30 tablets'
                }
                
                prescription = Prescription(
                    patient=patient_user,
                    doctor=admin_user,  # Using admin as doctor for test
                    medications=[medication_data],
                    dosage_instructions="Take with food",
                    duration="2 weeks",
                    notes="Test prescription"
                )
                prescription.save()
                print("✓ Prescription created successfully")
                
                # Test prescription retrieval
                prescriptions = Prescription.objects(patient=patient_user)
                print(f"✓ Found {prescriptions.count()} prescriptions for patient")
                
                results['prescription_system'] = True
                print("✅ Prescription System: PASSED")
            else:
                print("❌ Required users not found")
                
        except Exception as e:
            print(f"❌ Prescription System: FAILED - {e}")
        
        # Test 5: Appointment System
        print("\n5. Testing Appointment System...")
        try:
            from models import Appointment, AppointmentStatus
            
            admin_user = User.objects(email='admin@healthcare.com').first()
            patient_user = User.objects(email='patient@healthcare.com').first()
            
            if admin_user and patient_user:
                # Test appointment creation
                appointment = Appointment(
                    patient=patient_user,
                    doctor=admin_user,  # Using admin as doctor for test
                    appointment_date=datetime.utcnow() + timedelta(days=1),
                    duration=30,
                    status=AppointmentStatus.SCHEDULED,
                    symptoms="Test symptoms"
                )
                appointment.save()
                print("✓ Appointment created successfully")
                
                # Test appointment retrieval
                appointments = Appointment.objects(patient=patient_user)
                print(f"✓ Found {appointments.count()} appointments for patient")
                
                results['appointment_system'] = True
                print("✅ Appointment System: PASSED")
            else:
                print("❌ Required users not found")
                
        except Exception as e:
            print(f"❌ Appointment System: FAILED - {e}")
        
        # Test 6: Payment System
        print("\n6. Testing Payment System...")
        try:
            from models import Payment, PaymentStatus, PaymentMethod
            
            admin_user = User.objects(email='admin@healthcare.com').first()
            patient_user = User.objects(email='patient@healthcare.com').first()
            
            if admin_user and patient_user:
                # Test payment creation
                payment = Payment(
                    patient=patient_user,
                    doctor=admin_user,  # Using admin as doctor for test
                    amount=100.00,
                    payment_method=PaymentMethod.CASH,
                    status=PaymentStatus.PAID,
                    payment_date=datetime.utcnow()
                )
                payment.save()
                print("✓ Payment created successfully")
                
                # Test payment retrieval
                payments = Payment.objects(patient=patient_user)
                print(f"✓ Found {payments.count()} payments for patient")
                
                results['payment_system'] = True
                print("✅ Payment System: PASSED")
            else:
                print("❌ Required users not found")
                
        except Exception as e:
            print(f"❌ Payment System: FAILED - {e}")
        
        # Test 7: Role Permissions
        print("\n7. Testing Role Permissions...")
        try:
            # Test role checking methods
            admin_user = User.objects(email='admin@healthcare.com').first()
            doctor_user = User.objects(email='doctor@healthcare.com').first()
            patient_user = User.objects(email='patient@healthcare.com').first()
            
            if admin_user and doctor_user and patient_user:
                # Test role checking
                assert admin_user.is_admin() == True
                assert admin_user.is_doctor() == False
                assert admin_user.is_patient() == False
                print("✓ Admin role checking works")
                
                assert doctor_user.is_admin() == False
                assert doctor_user.is_doctor() == True
                assert doctor_user.is_patient() == False
                print("✓ Doctor role checking works")
                
                assert patient_user.is_admin() == False
                assert patient_user.is_doctor() == False
                assert patient_user.is_patient() == True
                print("✓ Patient role checking works")
                
                results['role_permissions'] = True
                print("✅ Role Permissions: PASSED")
            else:
                print("❌ Required users not found")
                
        except Exception as e:
            print(f"❌ Role Permissions: FAILED - {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! The system is working correctly.")
            return True
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
            return False
            
    except Exception as e:
        print(f"❌ System test failed with error: {e}")
        return False

def main():
    """Main test function"""
    try:
        # Import required modules
        from mongoengine import connect
        from config import Config
        
        # Connect to database
        connect(host=Config.MONGODB_URI)
        print("✓ Connected to database")
        
        # Run tests
        success = test_system()
        
        if success:
            print("\n🚀 System is ready for production!")
            sys.exit(0)
        else:
            print("\n🔧 System needs fixes before production.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
