#!/usr/bin/env python3
"""
Database Initialization Script for Healthcare AI System
Creates database collections and populates with sample data
"""

import os
import sys
from datetime import datetime, timedelta
from app import create_app
from models import User, UserRole, Appointment, AppointmentStatus, Report, ReportType, Message
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize the database with collections and sample data"""
    app = create_app()

    with app.app_context():
        print("Creating database collections...")
        # MongoDB collections are created automatically when first document is inserted
        
        print("Creating admin user...")
        # Create admin user
        admin = User.objects(email='admin@healthcare.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@healthcare.com',
                first_name='System',
                last_name='Administrator',
                role=UserRole.ADMIN,
                phone='555-0001',
                is_active=True
            )
            admin.set_password('admin123')
            admin.save()
            print("✓ Admin user created")
        else:
            print("✓ Admin user already exists")

        print("Creating sample doctors...")
        # Create sample doctors
        doctors_data = [
            {
                'username': 'dr_smith',
                'email': 'dr.smith@healthcare.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'specialization': 'Cardiology',
                'license_number': 'MD123456',
                'experience_years': 15,
                'phone': '555-1001'
            },
            {
                'username': 'dr_johnson',
                'email': 'dr.johnson@healthcare.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'specialization': 'Neurology',
                'license_number': 'MD123457',
                'experience_years': 12,
                'phone': '555-1002'
            },
            {
                'username': 'dr_williams',
                'email': 'dr.williams@healthcare.com',
                'first_name': 'Michael',
                'last_name': 'Williams',
                'specialization': 'Pediatrics',
                'license_number': 'MD123458',
                'experience_years': 8,
                'phone': '555-1003'
            },
            {
                'username': 'dr_brown',
                'email': 'dr.brown@healthcare.com',
                'first_name': 'Emily',
                'last_name': 'Brown',
                'specialization': 'Dermatology',
                'license_number': 'MD123459',
                'experience_years': 10,
                'phone': '555-1004'
            }
        ]

        doctors = []
        for doctor_data in doctors_data:
            doctor = User.objects(email=doctor_data['email']).first()
            if not doctor:
                doctor = User(
                    username=doctor_data['username'],
                    email=doctor_data['email'],
                    first_name=doctor_data['first_name'],
                    last_name=doctor_data['last_name'],
                    role=UserRole.DOCTOR,
                    specialization=doctor_data['specialization'],
                    license_number=doctor_data['license_number'],
                    experience_years=doctor_data['experience_years'],
                    phone=doctor_data['phone'],
                    is_active=True
                )
                doctor.set_password('password123')
                doctor.save()
                doctors.append(doctor)
                print(f"✓ Doctor {doctor.get_full_name()} created")
            else:
                doctors.append(doctor)
                print(f"✓ Doctor {doctor.get_full_name()} already exists")

        print("Creating sample patients...")
        # Create sample patients
        patients_data = [
            {
                'username': 'patient1',
                'email': 'john.doe@email.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'blood_group': 'A+',
                'emergency_contact': '555-2001',
                'phone': '555-2001',
                'medical_history': 'Hypertension, Diabetes Type 2'
            },
            {
                'username': 'patient2',
                'email': 'jane.smith@email.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'blood_group': 'O+',
                'emergency_contact': '555-2002',
                'phone': '555-2002',
                'medical_history': 'Asthma, Seasonal allergies'
            },
            {
                'username': 'patient3',
                'email': 'robert.wilson@email.com',
                'first_name': 'Robert',
                'last_name': 'Wilson',
                'blood_group': 'B+',
                'emergency_contact': '555-2003',
                'phone': '555-2003',
                'medical_history': 'Heart condition, High cholesterol'
            },
            {
                'username': 'lisa_davis',
                'email': 'lisa.davis@email.com',
                'first_name': 'Lisa',
                'last_name': 'Davis',
                'blood_group': 'AB+',
                'emergency_contact': '555-2004',
                'phone': '555-2004',
                'medical_history': 'Migraine, Anxiety'
            }
        ]

        patients = []
        for patient_data in patients_data:
            patient = User.objects(email=patient_data['email']).first()
            if not patient:
                patient = User(
                    username=patient_data['username'],
                    email=patient_data['email'],
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    role=UserRole.PATIENT,
                    blood_group=patient_data['blood_group'],
                    emergency_contact=patient_data['emergency_contact'],
                    phone=patient_data['phone'],
                    medical_history=patient_data['medical_history'],
                    is_active=True
                )
                patient.set_password('password123')
                patient.save()
                patients.append(patient)
                print(f"✓ Patient {patient.get_full_name()} created")
            else:
                patients.append(patient)
                print(f"✓ Patient {patient.get_full_name()} already exists")

        print("Creating sample appointments...")
        # Create sample appointments
        if doctors and patients:
            appointment_data = [
                {
                    'patient': patients[0],
                    'doctor': doctors[0],
                    'date': datetime.now() + timedelta(days=2),
                    'duration': 30,
                    'status': AppointmentStatus.SCHEDULED,
                    'symptoms': 'Chest pain and shortness of breath'
                },
                {
                    'patient': patients[1],
                    'doctor': doctors[1],
                    'date': datetime.now() + timedelta(days=3),
                    'duration': 45,
                    'status': AppointmentStatus.CONFIRMED,
                    'symptoms': 'Severe headaches and dizziness'
                },
                {
                    'patient': patients[2],
                    'doctor': doctors[2],
                    'date': datetime.now() + timedelta(days=1),
                    'duration': 30,
                    'status': AppointmentStatus.SCHEDULED,
                    'symptoms': 'Child with fever and cough'
                },
                {
                    'patient': patients[3],
                    'doctor': doctors[3],
                    'date': datetime.now() - timedelta(days=5),
                    'duration': 30,
                    'status': AppointmentStatus.COMPLETED,
                    'symptoms': 'Skin rash and itching'
                }
            ]

            for appt_data in appointment_data:
                existing_appt = Appointment.objects(
                    patient=appt_data['patient'],
                    doctor=appt_data['doctor'],
                    appointment_date=appt_data['date']
                ).first()

                if not existing_appt:
                    appointment = Appointment(
                        patient=appt_data['patient'],
                        doctor=appt_data['doctor'],
                        appointment_date=appt_data['date'],
                        duration=appt_data['duration'],
                        status=appt_data['status'],
                        symptoms=appt_data['symptoms']
                    )
                    appointment.save()
                    print(f"✓ Appointment created: {appt_data['patient'].get_full_name()} → Dr. {appt_data['doctor'].get_full_name()}")

        print("Creating sample reports...")
        # Create sample reports
        if doctors and patients:
            report_data = [
                {
                    'user': patients[0],
                    'creator': doctors[0],
                    'report_type': ReportType.CONSULTATION_REPORT,
                    'title': 'Cardiac Consultation Report',
                    'description': 'Patient presented with chest pain. ECG and blood tests ordered.',
                    'appointment_id': None
                },
                {
                    'user': patients[1],
                    'creator': doctors[1],
                    'report_type': ReportType.LAB_REPORT,
                    'title': 'Blood Test Results',
                    'description': 'Complete blood count and metabolic panel results.',
                    'appointment_id': None
                },
                {
                    'user': patients[2],
                    'creator': doctors[2],
                    'report_type': ReportType.PRESCRIPTION,
                    'title': 'Antibiotic Prescription',
                    'description': 'Amoxicillin 500mg three times daily for 7 days.',
                    'appointment_id': None
                }
            ]

            for report_data_item in report_data:
                existing_report = Report.objects(
                    user=report_data_item['user'],
                    title=report_data_item['title']
                ).first()

                if not existing_report:
                    report = Report(
                        user=report_data_item['user'],
                        created_by=report_data_item['creator'],
                        report_type=report_data_item['report_type'],
                        title=report_data_item['title'],
                        description=report_data_item['description']
                    )
                    report.save()
                    print(f"✓ Report created: {report_data_item['title']}")

        print("Creating sample messages...")
        # Create sample messages
        if doctors and patients:
            message_data = [
                {
                    'sender': doctors[0],
                    'recipient': patients[0],
                    'subject': 'Appointment Reminder',
                    'content': 'This is a reminder for your appointment tomorrow at 2:00 PM. Please arrive 10 minutes early.'
                },
                {
                    'sender': patients[1],
                    'recipient': doctors[1],
                    'subject': 'Question about medication',
                    'content': 'I have a question about the medication you prescribed. Can you please clarify the dosage?'
                },
                {
                    'sender': admin,
                    'recipient': doctors[0],
                    'subject': 'System Update',
                    'content': 'The healthcare system has been updated with new features. Please review the changes.'
                }
            ]

            for msg_data in message_data:
                existing_msg = Message.objects(
                    sender=msg_data['sender'],
                    recipient=msg_data['recipient'],
                    subject=msg_data['subject']
                ).first()

                if not existing_msg:
                    message = Message(
                        sender=msg_data['sender'],
                        recipient=msg_data['recipient'],
                        subject=msg_data['subject'],
                        content=msg_data['content']
                    )
                    message.save()
                    print(f"✓ Message created: {msg_data['subject']}")

        print("\n✓ Database initialization completed successfully!")
        print("\nDefault login credentials:")
        print("Admin: admin@healthcare.com / admin123")
        print("Doctors: [email] / password123")
        print("Patients: [email] / password123")
        print("\nPlease change passwords after first login!")

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)
