#!/usr/bin/env python3
"""
Stagebox Web Application

Flask application factory and entry point.
"""

import os
from flask import Flask

from web import usb_manager
from web.edition import EDITION, get_edition_name, is_limited
from web.config import VERSION


def create_app():
    """Create and configure the Flask application."""
    
    app = Flask(__name__)
    app.secret_key = os.urandom(24)
    
    # Cleanup any stale USB mounts at startup
    try:
        usb_manager.cleanup_mounts()
    except Exception:
        pass
    
    # Register all blueprints
    from web.routes import register_blueprints
    register_blueprints(app)
    
    # For Personal edition: ensure at least one building exists
    from web.services.building_manager import (
        discover_buildings, activate_building, get_active_building,
        ensure_default_building_exists
    )
    
    if is_limited():
        ensure_default_building_exists()
    
    print(f"[Stagebox] Version {VERSION} ({get_edition_name()} Edition)")
    print(f"[Stagebox] Edition: {EDITION}")
    
    return app


# Create app instance for WSGI
app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
