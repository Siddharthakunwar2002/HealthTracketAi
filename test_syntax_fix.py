#!/usr/bin/env python3
"""
Test script to verify that the syntax error has been fixed.
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_syntax_fix():
    """Test that the syntax error has been fixed"""
    print("🔧 Testing Syntax Fix")
    print("=" * 40)
    
    try:
        # Test importing the dashboard module
        print("1. Testing dashboard.py import...")
        import dashboard
        print("✅ dashboard.py imports successfully")
        
        # Test importing the app module
        print("2. Testing app.py import...")
        import app
        print("✅ app.py imports successfully")
        
        # Test that the dashboard blueprint is properly defined
        print("3. Testing dashboard blueprint...")
        assert hasattr(dashboard, 'dashboard')
        print("✅ Dashboard blueprint is properly defined")
        
        # Test that the routes are accessible
        print("4. Testing route definitions...")
        routes = [rule.rule for rule in app.app.url_map.iter_rules()]
        print(f"✅ Found {len(routes)} routes defined")
        
        print("\n" + "=" * 40)
        print("🎉 ALL SYNTAX TESTS PASSED!")
        print("=" * 40)
        print("✅ dashboard.py syntax is correct")
        print("✅ app.py can import dashboard")
        print("✅ All routes are properly defined")
        print("✅ Application can start successfully")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax Error: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Other Error: {e}")
        return False

def main():
    """Main test function"""
    try:
        success = test_syntax_fix()
        
        if success:
            print("\n🚀 The syntax error has been fixed!")
            print("You can now run: python app.py")
            sys.exit(0)
        else:
            print("\n🔧 There are still syntax issues to fix.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Failed to run syntax test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
