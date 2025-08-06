#!/usr/bin/env python3
# wsgi.py - Production WSGI entry point
import os
from app.core.factory import create_app

# Create application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(
        debug=debug,
        host='0.0.0.0',
        port=port,
        threaded=True
    )