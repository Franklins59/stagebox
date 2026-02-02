"""
Stagebox Pro Routes

Routes only available in Pro edition.
"""

from web.edition import is_pro

# Only import Pro routes if Pro edition
if is_pro():
    from web.routes.pro import admin
    from web.routes.pro import multi_building
    from web.routes.pro import snapshots
    from web.routes.pro import updates
    from web.routes.pro import replace
