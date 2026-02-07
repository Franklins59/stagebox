"""
System APT Updates Routes (Pro Only)

APT package updates for the underlying OS.
"""

import subprocess
from pathlib import Path
from flask import Blueprint, jsonify, request

from web import config
from web.routes.pro.admin import require_admin, require_pro

bp = Blueprint('system_updates', __name__)


def load_dependencies():
    """Load dependencies from dependencies.yaml."""
    try:
        import yaml
        deps_file = config.STAGEBOX_ROOT / 'dependencies.yaml'
        if deps_file.exists():
            with open(deps_file, 'r') as f:
                return yaml.safe_load(f) or {}
    except:
        pass
    return {}


def check_apt_package_installed(package_name):
    """Check if an APT package is installed."""
    try:
        result = subprocess.run(
            ['dpkg', '-s', package_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def check_pip_package_installed(package_name):
    """Check if a pip package is installed."""
    try:
        result = subprocess.run(
            ['pip3', 'show', package_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout
    except:
        return False, ''


@bp.route('/api/admin/system/apt/check', methods=['GET'])
@require_pro
@require_admin
def check_apt_updates():
    """Check for available system package updates.
    
    Returns:
    - required_apt/required_pip: Missing dependencies from dependencies.yaml (must install)
    - security_packages: Security updates available
    - system_packages: System-critical updates available
    """
    # Load whitelist from dependencies.yaml
    deps = load_dependencies()
    system_prefixes = deps.get('apt_update_prefixes', [])
    
    # Fallback if dependencies.yaml not available
    if not system_prefixes:
        system_prefixes = [
            'python3', 'python-', 'libpython',
            'linux-', 'systemd', 'openssl', 'libssl',
            'ca-certificates', 'networkmanager', 'sudo',
            'apt', 'dpkg', 'openssh', 'curl', 'wget',
            'raspi-', 'firmware-', 'libc6', 'libc-bin', 'tzdata', 'base-files',
        ]
    
    def is_system_package(pkg_name):
        """Check if package is system-critical."""
        pkg_lower = pkg_name.lower()
        for prefix in system_prefixes:
            if pkg_lower.startswith(prefix.lower()):
                return True
        return False
    
    try:
        # Check for missing required dependencies first
        required_apt = deps.get('apt', [])
        required_pip = deps.get('pip', [])
        
        missing_apt = []
        missing_pip = []
        
        for pkg in required_apt:
            if not check_apt_package_installed(pkg):
                missing_apt.append(pkg)
        
        for pkg in required_pip:
            # Extract package name without version spec before checking
            pkg_name = pkg.split('>=')[0].split('==')[0].split('<')[0].strip()
            installed, _ = check_pip_package_installed(pkg_name)
            if not installed:
                missing_pip.append(pkg_name)
        
        # Update package lists
        update_result = subprocess.run(
            ['sudo', 'apt-get', 'update'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for slow connections
        )
        
        if update_result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Failed to update package lists: {update_result.stderr}'
            }), 500
        
        # Get list of upgradable packages
        list_result = subprocess.run(
            ['apt', 'list', '--upgradable'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        all_packages = []
        if list_result.returncode == 0:
            lines = list_result.stdout.strip().split('\n')
            # Skip first line "Listing..."
            for line in lines[1:]:
                if line.strip():
                    # Format: package/source version [upgradable from: old_version]
                    pkg_name = line.split('/')[0]
                    all_packages.append(pkg_name)
        
        # Categorize packages
        security_packages = []
        system_packages = []
        other_count = 0
        
        for pkg in all_packages:
            # Check if security update
            policy_result = subprocess.run(
                ['apt-cache', 'policy', pkg],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_security = False
            if policy_result.returncode == 0:
                output = policy_result.stdout.lower()
                is_security = 'security' in output
            
            if is_security:
                security_packages.append(pkg)
            elif is_system_package(pkg):
                system_packages.append(pkg)
            else:
                other_count += 1
        
        return jsonify({
            'success': True,
            # Required (missing dependencies)
            'required_apt': missing_apt,
            'required_pip': missing_pip,
            'required_count': len(missing_apt) + len(missing_pip),
            # Updates
            'security_count': len(security_packages),
            'system_count': len(system_packages),
            'other_count': other_count,
            'security_packages': security_packages,
            'system_packages': system_packages
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Operation timed out'
        }), 504
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/admin/system/apt/upgrade', methods=['POST'])
@require_pro
@require_admin
def run_apt_upgrade():
    """Run APT upgrade for system packages."""
    import threading
    
    try:
        # Get packages from request (optional - if not provided, upgrade all)
        data = request.get_json() or {}
        packages = data.get('packages', [])
        
        if packages:
            # Upgrade specific packages
            cmd = ['sudo', 'apt-get', 'install', '--only-upgrade', '-y'] + packages
        else:
            # Upgrade all
            cmd = ['sudo', 'apt-get', 'upgrade', '-y']
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'message': 'Upgrade failed',
                'error': result.stderr,
                'rebooting': False
            })
        
        # Count upgraded packages
        upgraded_count = len(packages) if packages else 0
        if not packages:
            # Count from output
            for line in result.stdout.split('\n'):
                if 'upgraded' in line.lower():
                    try:
                        upgraded_count = int(line.split()[0])
                    except:
                        pass
                    break
        
        # Schedule reboot in background (give time for response)
        def delayed_reboot():
            import time
            time.sleep(3)
            subprocess.run(['sudo', 'systemctl', 'reboot'], capture_output=True)
        
        reboot_thread = threading.Thread(target=delayed_reboot)
        reboot_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'{upgraded_count} packages updated successfully',
            'rebooting': True
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'message': 'Upgrade timeout',
            'error': 'Operation timed out after 10 minutes',
            'rebooting': False
        }), 504
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Upgrade failed',
            'error': str(e),
            'rebooting': False
        }), 500