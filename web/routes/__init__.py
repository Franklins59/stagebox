"""
Stagebox Routes

Blueprint registration for all routes.
"""

from flask import Flask

from web.edition import is_pro, get_edition_name


def register_blueprints(app: Flask):
    """Register all blueprints with the Flask app."""
    
    # Core routes (both editions)
    from web.routes import core
    from web.routes import buildings
    from web.routes import devices
    from web.routes import system
    from web.routes import provisioning
    from web.routes import scripts
    from web.routes import updates
    
    app.register_blueprint(core.bp)
    app.register_blueprint(buildings.bp)
    app.register_blueprint(devices.bp)
    app.register_blueprint(system.bp)
    app.register_blueprint(provisioning.bp)
    app.register_blueprint(scripts.bp)
    app.register_blueprint(updates.bp)
    
    # Admin routes (both editions - PIN, auth, settings)
    from web.routes.pro import admin
    app.register_blueprint(admin.bp)
    
    # Pro-only routes
    if is_pro():
        from web.routes.pro import multi_building
        from web.routes.pro import snapshots
        from web.routes.pro import updates as pro_updates
        from web.routes.pro import replace
        from web.routes.pro import usb
        
        app.register_blueprint(multi_building.bp)
        app.register_blueprint(snapshots.bp)
        app.register_blueprint(pro_updates.bp)
        app.register_blueprint(replace.bp)
        app.register_blueprint(usb.bp)
        
        print("[Routes] Pro edition routes registered")
    else:
        print(f"[Routes] {get_edition_name()} edition routes registered")
