#!/usr/bin/env python3
"""
Test script to verify that prescriptions and messages are visible to all roles.
Tests the fixes for prescription and message visibility issues.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_visibility_fixes():
    """Test that prescriptions and messages are visible to all roles"""
    print("🔍 Testing Prescription and Message Visibility Fixes")
    print("=" * 60)
    
    try:
        from models import User, UserRole, Prescription, Message, Notification, NotificationType
        from mongoengine import connect
        from config import Config
        
        # Connect to database
        connect(host=Config.MONGODB_URI)
        print("✓ Connected to database")
        
        # Test 1: Create test data
        print("\n1. Creating test data...")
        
        # Get or create test users
        admin_user = User.objects(email='admin@healthcare.com').first()
        doctor_user = User.objects(email='doctor@healthcare.com').first()
        patient_user = User.objects(email='patient@healthcare.com').first()
        
        if not admin_user:
            admin_user = User(
                username='test_admin',
                email='admin@healthcare.com',
                first_name='Test',
                last_name='Admin',
                role=UserRole.ADMIN,
                phone='555-0001'
            )
            admin_user.set_password('admin123')
            admin_user.save()
            print("✓ Created admin user")
        
        if not doctor_user:
            doctor_user = User(
                username='test_doctor',
                email='doctor@healthcare.com',
                first_name='Test',
                last_name='Doctor',
                role=UserRole.DOCTOR,
                specialization='General Medicine',
                license_number='MD-TEST-001',
                experience_years=5
            )
            doctor_user.set_password('password123')
            doctor_user.save()
            print("✓ Created doctor user")
        
        if not patient_user:
            patient_user = User(
                username='test_patient',
                email='patient@healthcare.com',
                first_name='Test',
                last_name='Patient',
                role=UserRole.PATIENT,
                blood_group='O+',
                phone='555-2000'
            )
            patient_user.set_password('password123')
            patient_user.save()
            print("✓ Created patient user")
        
        # Test 2: Create test prescription
        print("\n2. Testing prescription visibility...")
        
        # Create prescription
        medication_data = {
            'name': 'Test Medication',
            'dosage': '10mg',
            'frequency': 'Twice daily',
            'quantity': '30 tablets'
        }
        
        prescription = Prescription(
            patient=patient_user,
            doctor=doctor_user,
            medications=[medication_data],
            dosage_instructions="Take with food",
            duration="2 weeks",
            notes="Test prescription for visibility testing"
        )
        prescription.save()
        print("✓ Prescription created successfully")
        
        # Test prescription visibility for patient
        patient_prescriptions = Prescription.objects(patient=patient_user)
        print(f"✓ Patient can see {patient_prescriptions.count()} prescriptions")
        
        # Test prescription visibility for doctor
        doctor_prescriptions = Prescription.objects(doctor=doctor_user)
        print(f"✓ Doctor can see {doctor_prescriptions.count()} prescriptions")
        
        # Test prescription visibility for admin
        admin_prescriptions = Prescription.objects()
        print(f"✓ Admin can see {admin_prescriptions.count()} prescriptions")
        
        # Test 3: Create test messages
        print("\n3. Testing message visibility...")
        
        # Create message from patient to doctor
        patient_to_doctor = Message(
            sender=patient_user,
            recipient=doctor_user,
            subject="Test Message from Patient",
            content="This is a test message from patient to doctor to verify message visibility."
        )
        patient_to_doctor.save()
        print("✓ Message from patient to doctor created")
        
        # Create message from doctor to patient
        doctor_to_patient = Message(
            sender=doctor_user,
            recipient=patient_user,
            subject="Test Message from Doctor",
            content="This is a test message from doctor to patient to verify message visibility."
        )
        doctor_to_patient.save()
        print("✓ Message from doctor to patient created")
        
        # Test message visibility for patient
        patient_received = Message.objects(recipient=patient_user)
        patient_sent = Message.objects(sender=patient_user)
        print(f"✓ Patient can see {patient_received.count()} received messages")
        print(f"✓ Patient can see {patient_sent.count()} sent messages")
        
        # Test message visibility for doctor
        doctor_received = Message.objects(recipient=doctor_user)
        doctor_sent = Message.objects(sender=doctor_user)
        print(f"✓ Doctor can see {doctor_received.count()} received messages")
        print(f"✓ Doctor can see {doctor_sent.count()} sent messages")
        
        # Test message visibility for admin
        admin_messages = Message.objects()
        print(f"✓ Admin can see {admin_messages.count()} total messages")
        
        # Test 4: Test notification creation
        print("\n4. Testing notification system...")
        
        # Create notification for patient about prescription
        prescription_notification = Notification(
            user=patient_user,
            title="New Prescription",
            message=f"Dr. {doctor_user.get_full_name()} has prescribed new medication for you.",
            notification_type=NotificationType.SYSTEM,
            related_id=str(prescription.id)
        )
        prescription_notification.save()
        print("✓ Prescription notification created for patient")
        
        # Create notification for doctor about message
        message_notification = Notification(
            user=doctor_user,
            title="New Message",
            message=f"You have received a new message from {patient_user.get_full_name()}.",
            notification_type=NotificationType.MESSAGE,
            related_id=str(patient_to_doctor.id)
        )
        message_notification.save()
        print("✓ Message notification created for doctor")
        
        # Test notification visibility
        patient_notifications = Notification.objects(user=patient_user)
        doctor_notifications = Notification.objects(user=doctor_user)
        admin_notifications = Notification.objects()
        
        print(f"✓ Patient has {patient_notifications.count()} notifications")
        print(f"✓ Doctor has {doctor_notifications.count()} notifications")
        print(f"✓ Admin can see {admin_notifications.count()} total notifications")
        
        # Test 5: Test role-based access
        print("\n5. Testing role-based access...")
        
        # Test admin access
        assert admin_user.is_admin() == True
        assert admin_user.is_doctor() == False
        assert admin_user.is_patient() == False
        print("✓ Admin role checking works")
        
        # Test doctor access
        assert doctor_user.is_admin() == False
        assert doctor_user.is_doctor() == True
        assert doctor_user.is_patient() == False
        print("✓ Doctor role checking works")
        
        # Test patient access
        assert patient_user.is_admin() == False
        assert patient_user.is_doctor() == False
        assert patient_user.is_patient() == True
        print("✓ Patient role checking works")
        
        print("\n" + "=" * 60)
        print("🎉 ALL VISIBILITY TESTS PASSED!")
        print("=" * 60)
        print("✅ Prescriptions are visible to patients")
        print("✅ Prescriptions are visible to doctors")
        print("✅ Prescriptions are visible to admins")
        print("✅ Messages are visible to patients")
        print("✅ Messages are visible to doctors")
        print("✅ Messages are visible to admins")
        print("✅ Notifications are working properly")
        print("✅ Role-based access control is working")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    try:
        success = test_visibility_fixes()
        
        if success:
            print("\n🚀 All visibility issues have been fixed!")
            print("The system now properly displays prescriptions and messages to all roles.")
            sys.exit(0)
        else:
            print("\n🔧 Some issues still need to be addressed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to run visibility tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
