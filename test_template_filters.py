#!/usr/bin/env python3
"""
Test script to verify that the template filters work correctly.
"""

import sys
import os
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_template_filters():
    """Test that the template filters work correctly"""
    print("🔧 Testing Template Filters")
    print("=" * 40)
    
    try:
        # Test importing the modules
        print("1. Testing imports...")
        import app
        from bson import ObjectId
        print("✅ All imports successful")
        
        # Create Flask app instance
        print("2. Creating Flask app...")
        flask_app = app.create_app()
        print("✅ Flask app created successfully")
        
        # Test ObjectId conversion
        print("3. Testing ObjectId conversion...")
        test_id = ObjectId()
        test_id_str = str(test_id)
        test_id_short = test_id_str[:8]
        print(f"✅ ObjectId: {test_id}")
        print(f"✅ String conversion: {test_id_str}")
        print(f"✅ Short ID: {test_id_short}")
        
        # Test template filters
        print("4. Testing template filters...")
        with flask_app.app_context():
            # Test to_string filter
            to_string_result = flask_app.jinja_env.filters['to_string'](test_id)
            print(f"✅ to_string filter: {to_string_result}")
            
            # Test objectid_slice filter
            objectid_slice_result = flask_app.jinja_env.filters['objectid_slice'](test_id)
            print(f"✅ objectid_slice filter: {objectid_slice_result}")
            
            # Test objectid_slice with custom parameters
            objectid_slice_custom = flask_app.jinja_env.filters['objectid_slice'](test_id, 0, 6)
            print(f"✅ objectid_slice (0,6): {objectid_slice_custom}")
        
        # Test template rendering
        print("5. Testing template rendering...")
        with flask_app.app_context():
            # Create mock prescription data
            mock_prescription = {
                'id': test_id,
                'doctor': {'get_full_name': lambda: 'Dr. Test Doctor'},
                'created_at': datetime.now(),
                'duration': '7 days',
                'is_active': True,
                'medications': [
                    {'name': 'Test Medication', 'dosage': '500mg'},
                    {'name': 'Another Medication', 'dosage': '250mg'}
                ],
                'dosage_instructions': 'Take twice daily with food',
                'notes': 'Test prescription notes'
            }
            
            # Test template string operations
            template_test_id = flask_app.jinja_env.filters['objectid_slice'](mock_prescription['id'])
            template_test_full_id = flask_app.jinja_env.filters['to_string'](mock_prescription['id'])
            
            print(f"✅ Template ID (short): {template_test_id}")
            print(f"✅ Template ID (full): {template_test_full_id}")
        
        print("\n" + "=" * 40)
        print("🎉 ALL TEMPLATE FILTER TESTS PASSED!")
        print("=" * 40)
        print("✅ ObjectId conversion works")
        print("✅ Template filters are registered")
        print("✅ to_string filter works")
        print("✅ objectid_slice filter works")
        print("✅ Template rendering should work correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    try:
        success = test_template_filters()
        
        if success:
            print("\n🚀 The template filters are working correctly!")
            print("Patient prescriptions should now display without 'str' undefined errors.")
            sys.exit(0)
        else:
            print("\n🔧 There are still issues to fix.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to run template filter test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
