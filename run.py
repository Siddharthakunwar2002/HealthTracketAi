#!/usr/bin/env python3
"""
Run script for Healthcare AI System
"""

import os
import sys
from app import create_app

def main():
    """Main function to run the application"""
    print("Healthcare AI System - Starting Application")
    print("=" * 50)

    # Create the Flask app and SocketIO
    app, socketio = create_app()

    # Get configuration
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))

    print(f"Starting server on http://{host}:{port}")
    print(f"Debug mode: {'ON' if debug else 'OFF'}")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Run the application with SocketIO
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug
        )
    except KeyboardInterrupt:
        print("\nShutting down server...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
