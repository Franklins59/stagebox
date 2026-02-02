"""
USB Backup Manager for Stagebox.

Clean, synchronous USB backup operations with mount-by-label.
All operations follow: mount → operation → sync → unmount

Label: STAGEBOXBAK (fixed, 11 chars FAT32 max)
Mountpoint: /mnt/backup_usb (fixed)
Filename: stagebox-<mac_suffix>-<timestamp>.zip (flat, no subdirs)
"""

import os
import subprocess
import zipfile
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import json


# Constants
USB_LABEL = 'STAGEBOXBAK'
MOUNT_POINT = Path('/mnt/backup_usb')
MAX_BACKUPS = 10
SIGNATURE_SECRET = "StageboxValidExport2024"


def _generate_signature(building_name: str, file_count: int) -> str:
    """Generate a signature for Stagebox exports."""
    data = f"{building_name}:{file_count}:{SIGNATURE_SECRET}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def _verify_signature(building_name: str, file_count: int, signature: str) -> bool:
    """Verify a Stagebox export signature."""
    expected = _generate_signature(building_name, file_count)
    return signature == expected


class USBError(Exception):
    """Base exception for USB operations."""
    pass


class USBNotFoundError(USBError):
    """No USB stick with correct label found."""
    pass


class USBMountError(USBError):
    """Failed to mount USB stick."""
    pass


class USBWriteError(USBError):
    """Failed to write to USB stick."""
    pass


@dataclass
class USBDrive:
    """Represents a detected USB drive."""
    device: str
    name: str
    size: str
    fstype: str
    label: str
    mountpoint: Optional[str] = None
    is_stagebox: bool = False
    total_bytes: int = 0
    free_bytes: int = 0
    used_bytes: int = 0
    usage_percent: float = 0.0


@dataclass
class BackupInfo:
    """Represents a backup file on USB."""
    path: str
    filename: str
    date: str
    size: str
    size_bytes: int
    mac_suffix: str


def _run_cmd(cmd: List[str], timeout: int = 30, check: bool = False) -> subprocess.CompletedProcess:
    """Run a command with timeout and capture output."""
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout
    )


def _find_device_by_label(label: str = USB_LABEL) -> Optional[str]:
    """Find block device by filesystem label.
    
    Returns device path like '/dev/sda1' or None if not found.
    """
    result = _run_cmd(['lsblk', '-J', '-o', 'NAME,LABEL,FSTYPE'])
    if result.returncode != 0:
        return None
    
    try:
        data = json.loads(result.stdout)
        for device in data.get('blockdevices', []):
            # Check device itself
            if device.get('label') == label:
                return f"/dev/{device['name']}"
            
            # Check partitions
            for child in device.get('children', []):
                if child.get('label') == label:
                    return f"/dev/{child['name']}"
    except (json.JSONDecodeError, KeyError):
        pass
    
    return None


def _is_mounted(path: Path = MOUNT_POINT) -> bool:
    """Check if mountpoint is currently mounted."""
    result = _run_cmd(['mountpoint', '-q', str(path)])
    return result.returncode == 0


def _is_stale_mount(path: Path = MOUNT_POINT) -> bool:
    """Check if mountpoint is stale (mounted but device unavailable or I/O error).
    
    Returns True if mount exists but is unusable.
    """
    if not _is_mounted(path):
        return False
    
    # Try to access the mountpoint
    try:
        # Simple stat call - will fail with I/O error if stale
        os.statvfs(str(path))
        # Try listing directory
        list(path.iterdir())
        return False
    except OSError as e:
        # I/O error, stale file handle, transport endpoint not connected, etc.
        if e.errno in (5, 116, 107, 112, 121):  # EIO, ESTALE, ENOTCONN, EHOSTDOWN, EREMOTEIO
            return True
        # Permission errors etc. are not stale mounts
        return False
    except Exception:
        return True


def _cleanup_stale_mount(path: Path = MOUNT_POINT) -> bool:
    """Force cleanup of a stale mount.
    
    Returns True if cleanup was successful or not needed.
    """
    if not path.exists():
        return True
    
    if not _is_mounted(path):
        return True
    
    # Try lazy unmount first (for stale mounts)
    result = _run_cmd(['sudo', 'umount', '-l', str(path)], timeout=10)
    if result.returncode == 0:
        return True
    
    # Try force unmount
    result = _run_cmd(['sudo', 'umount', '-f', str(path)], timeout=10)
    if result.returncode == 0:
        return True
    
    return False


def _ensure_mount_health(path: Path = MOUNT_POINT) -> None:
    """Ensure mountpoint is healthy, cleanup if stale.
    
    Raises USBMountError if cleanup fails.
    """
    if _is_stale_mount(path):
        if not _cleanup_stale_mount(path):
            raise USBMountError(f"Failed to cleanup stale mount at {path}")


def _mount(device: str, mount_point: Path = MOUNT_POINT) -> None:
    """Mount device with flush option for safe removal.
    
    Raises USBMountError on failure.
    """
    # Ensure mount point exists
    mount_point.mkdir(parents=True, exist_ok=True)
    
    # Mount with flush option (writes immediately, safer for removal)
    result = _run_cmd([
        'sudo', 'mount', '-o', 'rw,flush', device, str(mount_point)
    ])
    
    if result.returncode != 0:
        raise USBMountError(f"Mount failed: {result.stderr}")


def _unmount(mount_point: Path = MOUNT_POINT) -> None:
    """Sync and unmount. Silent if not mounted. Handles stale mounts."""
    if not _is_mounted(mount_point):
        return
    
    # Check if stale - use lazy unmount if so
    if _is_stale_mount(mount_point):
        _cleanup_stale_mount(mount_point)
        return
    
    # Normal unmount
    _run_cmd(['sync'], timeout=60)
    result = _run_cmd(['sudo', 'umount', str(mount_point)], timeout=30)
    
    # If normal unmount failed, try lazy
    if result.returncode != 0 and _is_mounted(mount_point):
        _run_cmd(['sudo', 'umount', '-l', str(mount_point)], timeout=10)


def _ensure_mounted() -> str:
    """Ensure USB stick is mounted, return device path.
    
    Cleans up stale mounts before attempting to mount.
    
    Raises USBNotFoundError if no stick with label found.
    Raises USBMountError if mount fails.
    """
    # First, cleanup any stale mount
    _ensure_mount_health()
    
    device = _find_device_by_label()
    if not device:
        raise USBNotFoundError(f"No USB stick with label '{USB_LABEL}' found")
    
    if not _is_mounted():
        _mount(device)
    
    # Verify mount is healthy after mounting
    if _is_stale_mount():
        _cleanup_stale_mount()
        raise USBMountError("Mount became stale immediately - USB stick may be faulty")
    
    return device


def cleanup_mounts() -> Dict[str, Any]:
    """Public function to cleanup any stale USB mounts.
    
    Can be called at startup or when I/O errors occur.
    
    Returns:
        Dict with 'success', 'was_stale', 'cleaned' keys
    """
    was_stale = _is_stale_mount()
    cleaned = False
    
    if was_stale:
        cleaned = _cleanup_stale_mount()
    
    return {
        'success': True,
        'was_stale': was_stale,
        'cleaned': cleaned
    }


def get_mac_suffix() -> str:
    """Get the last 6 characters of primary network interface MAC.
    
    Returns '------' if not found.
    """
    try:
        # Try eth0 first, then any interface starting with e
        for iface in ['eth0', 'enp*', 'en*']:
            result = _run_cmd(['bash', '-c', f'cat /sys/class/net/{iface}/address 2>/dev/null | head -1'])
            if result.returncode == 0 and result.stdout.strip():
                mac = result.stdout.strip().replace(':', '')
                return mac[-6:].lower()
        
        # Fallback: try to get any ethernet MAC
        result = _run_cmd(['bash', '-c', "ip link show | grep -A1 '^[0-9].*: e' | grep ether | awk '{print $2}' | head -1"])
        if result.returncode == 0 and result.stdout.strip():
            mac = result.stdout.strip().replace(':', '')
            return mac[-6:].lower()
    except Exception:
        pass
    
    return '------'


# ============================================================================
# Public API
# ============================================================================

def check_usb_status() -> Dict[str, Any]:
    """Check if USB stick with correct label is available.
    
    Returns status dict with 'available', 'device', 'mounted', 'stale' keys.
    Does NOT mount the stick, but cleans up stale mounts.
    """
    # Cleanup stale mounts first
    stale = _is_stale_mount()
    if stale:
        _cleanup_stale_mount()
    
    device = _find_device_by_label()
    mounted = _is_mounted() if device else False
    
    return {
        'available': device is not None,
        'device': device,
        'mounted': mounted,
        'stale_cleaned': stale,
        'label': USB_LABEL,
        'mount_point': str(MOUNT_POINT)
    }


def list_drives() -> List[USBDrive]:
    """List all USB drives (sd* devices).
    
    Used for format dialog - shows all USB drives, not just STAGEBOXBAK.
    Cleans up any stale mounts first.
    """
    # Cleanup any stale mounts first
    if _is_stale_mount():
        _cleanup_stale_mount()
    
    result = _run_cmd(['lsblk', '-J', '-o', 'NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL'])
    if result.returncode != 0:
        return []
    
    drives = []
    try:
        data = json.loads(result.stdout)
        for device in data.get('blockdevices', []):
            name = device.get('name', '')
            
            # Only sd* devices (USB/SATA)
            if not name.startswith('sd'):
                continue
            
            # Check partitions
            children = device.get('children', [])
            if children:
                for part in children:
                    label = part.get('label') or ''
                    mountpoint = part.get('mountpoint')
                    
                    drive = USBDrive(
                        device=f"/dev/{part['name']}",
                        name=name,
                        size=part.get('size', ''),
                        fstype=part.get('fstype', ''),
                        label=label,
                        mountpoint=mountpoint,
                        is_stagebox=(label == USB_LABEL)
                    )
                    
                    # Get disk usage if mounted
                    if mountpoint:
                        try:
                            st = os.statvfs(mountpoint)
                            drive.total_bytes = st.f_blocks * st.f_frsize
                            drive.free_bytes = st.f_bavail * st.f_frsize
                            drive.used_bytes = drive.total_bytes - drive.free_bytes
                            drive.usage_percent = round((drive.used_bytes / drive.total_bytes) * 100, 1) if drive.total_bytes > 0 else 0
                        except OSError as e:
                            # I/O error - mark mountpoint as problematic
                            if e.errno in (5, 116, 107, 112, 121):
                                drive.mountpoint = f"ERROR: I/O error"
                                # Try to cleanup
                                _run_cmd(['sudo', 'umount', '-l', mountpoint], timeout=5)
                    
                    drives.append(drive)
            else:
                # Unpartitioned drive
                label = device.get('label') or ''
                mountpoint = device.get('mountpoint')
                
                drive = USBDrive(
                    device=f"/dev/{name}",
                    name=name,
                    size=device.get('size', ''),
                    fstype=device.get('fstype', ''),
                    label=label,
                    mountpoint=mountpoint,
                    is_stagebox=(label == USB_LABEL)
                )
                drives.append(drive)
    
    except (json.JSONDecodeError, KeyError):
        pass
    
    return drives


def format_drive(device: str) -> Dict[str, Any]:
    """Format a USB drive as FAT32 with STAGEBOXBAK label.
    
    WARNING: Erases all data!
    
    Args:
        device: Device path like '/dev/sda1'
        
    Returns:
        Dict with 'success', 'message' or 'error'
    """
    # Security check
    if not device.startswith('/dev/sd'):
        return {'success': False, 'error': 'Invalid device - only USB drives allowed'}
    
    if not os.path.exists(device):
        return {'success': False, 'error': f'Device {device} does not exist'}
    
    try:
        # Cleanup any stale mounts first
        if _is_stale_mount():
            _cleanup_stale_mount()
        
        # Unmount if mounted (try multiple methods)
        _run_cmd(['sudo', 'umount', device], timeout=30)
        _run_cmd(['sudo', 'umount', '-l', device], timeout=10)  # Lazy unmount as fallback
        
        # Format as FAT32
        result = _run_cmd([
            'sudo', 'mkfs.vfat', '-F', '32', '-n', USB_LABEL, device
        ], timeout=120)
        
        if result.returncode != 0:
            return {'success': False, 'error': f'Format failed: {result.stderr}'}
        
        # Sync to ensure format is complete
        _run_cmd(['sync'], timeout=30)
        
        return {
            'success': True,
            'message': f'Drive formatted as {USB_LABEL}'
        }
        
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Format timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def create_backup(buildings_dir: Path) -> Dict[str, Any]:
    """Create a backup of all buildings to USB.
    
    Flow: mount → create zip → copy → sync → unmount
    
    Args:
        buildings_dir: Path to buildings directory
        
    Returns:
        Dict with 'success', 'filename', 'backup_count' or 'error'
    """
    try:
        # Check buildings exist
        if not buildings_dir.exists() or not any(buildings_dir.iterdir()):
            return {'success': False, 'error': 'No buildings to backup'}
        
        # Mount USB
        _ensure_mounted()
        
        # Generate filename
        mac_suffix = get_mac_suffix()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'stagebox-{mac_suffix}-{timestamp}.zip'
        
        # Create ZIP in temp location first (atomic write)
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            # Create ZIP with all buildings
            with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for building_dir in buildings_dir.iterdir():
                    if not building_dir.is_dir():
                        continue
                    if '_old_' in building_dir.name:
                        continue
                    
                    file_count = 0
                    for file_path in building_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = str(file_path.relative_to(buildings_dir))
                            zf.write(file_path, arcname)
                            file_count += 1
                    
                    # Add signature file for each building
                    signature = _generate_signature(building_dir.name, file_count)
                    sig_content = json.dumps({
                        'version': '1.0',
                        'building': building_dir.name,
                        'files': file_count,
                        'sig': signature
                    })
                    zf.writestr(f"{building_dir.name}/.stagebox", sig_content)
            
            # Copy to USB with sudo
            zip_path = MOUNT_POINT / zip_filename
            result = _run_cmd(['sudo', 'cp', str(tmp_path), str(zip_path)], timeout=60)
            if result.returncode != 0:
                raise USBWriteError(f'Copy failed: {result.stderr}')
            
            _run_cmd(['sudo', 'chmod', '644', str(zip_path)])
            
        finally:
            # Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()
        
        # Rotation: keep only last MAX_BACKUPS
        existing = sorted(
            MOUNT_POINT.glob(f'stagebox-{mac_suffix}-*.zip'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for old in existing[MAX_BACKUPS:]:
            _run_cmd(['sudo', 'rm', str(old)])
        
        # Count backups after rotation (existing already includes the new one)
        backup_count = min(len(existing), MAX_BACKUPS)
        
        # Unmount (makes stick safe to remove)
        _unmount()
        
        return {
            'success': True,
            'message': f'Backup created: {zip_filename}',
            'filename': zip_filename,
            'backup_count': backup_count
        }
        
    except USBNotFoundError as e:
        return {'success': False, 'error': str(e)}
    except USBMountError as e:
        return {'success': False, 'error': str(e)}
    except USBWriteError as e:
        _unmount()
        return {'success': False, 'error': str(e)}
    except Exception as e:
        _unmount()
        return {'success': False, 'error': str(e)}


def list_backups() -> Dict[str, Any]:
    """List all backups on USB stick.
    
    Returns:
        Dict with 'success', 'backups' list, 'own_mac_suffix' or 'error'
    """
    try:
        _ensure_mounted()
        
        backups = []
        # Flat structure: stagebox-*.zip in root
        for zip_path in MOUNT_POINT.glob('stagebox-*.zip'):
            try:
                stat = zip_path.stat()
                filename = zip_path.name
                
                # Parse: stagebox-aabbcc-20250115_143022.zip
                parts = filename.replace('.zip', '').split('-')
                mac_suffix = parts[1] if len(parts) >= 2 else '------'
                
                if len(parts) >= 3:
                    timestamp_str = parts[-1]
                    try:
                        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        date_display = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        date_display = timestamp_str
                else:
                    date_display = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                size_mb = stat.st_size / (1024 * 1024)
                
                backups.append(BackupInfo(
                    path=str(zip_path),
                    filename=filename,
                    date=date_display,
                    size=f'{size_mb:.1f} MB',
                    size_bytes=stat.st_size,
                    mac_suffix=mac_suffix
                ))
            except OSError:
                continue
        
        # Also check old structure (subdirs) for backwards compatibility
        for zip_path in MOUNT_POINT.glob('*/stagebox-*.zip'):
            try:
                stat = zip_path.stat()
                filename = zip_path.name
                mac_suffix = zip_path.parent.name
                
                parts = filename.replace('.zip', '').split('-')
                if len(parts) >= 3:
                    timestamp_str = parts[-1]
                    try:
                        dt = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                        date_display = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        date_display = timestamp_str
                else:
                    date_display = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                size_mb = stat.st_size / (1024 * 1024)
                
                backups.append(BackupInfo(
                    path=str(zip_path),
                    filename=filename,
                    date=date_display,
                    size=f'{size_mb:.1f} MB',
                    size_bytes=stat.st_size,
                    mac_suffix=mac_suffix
                ))
            except OSError:
                continue
        
        # Sort by date (newest first)
        backups.sort(key=lambda x: x.date, reverse=True)
        
        own_mac = get_mac_suffix()
        
        # Unmount after listing
        _unmount()
        
        return {
            'success': True,
            'backups': [vars(b) for b in backups],
            'own_mac_suffix': own_mac
        }
        
    except USBNotFoundError as e:
        return {'success': False, 'error': str(e)}
    except USBMountError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        _unmount()
        return {'success': False, 'error': str(e)}


def analyze_backup(zip_path: str) -> Dict[str, Any]:
    """Analyze a backup ZIP and return list of buildings.
    
    Args:
        zip_path: Path to ZIP file on USB
        
    Returns:
        Dict with 'success', 'buildings' list, 'existing' list or 'error'
    """
    zip_path = Path(zip_path)
    
    # Security check
    if not str(zip_path).startswith(str(MOUNT_POINT)):
        return {'success': False, 'error': 'Invalid backup path'}
    
    try:
        _ensure_mounted()
        
        if not zip_path.exists():
            _unmount()
            return {'success': False, 'error': 'Backup file not found'}
        
        buildings = []
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            
            # Find buildings with valid .stagebox signature
            for name in namelist:
                if name.endswith('/.stagebox'):
                    building_name = name.rsplit('/', 2)[0]
                    try:
                        sig_data = json.loads(zf.read(name).decode('utf-8'))
                        file_count = sig_data.get('files', 0)
                        signature = sig_data.get('sig', '')
                        
                        if _verify_signature(building_name, file_count, signature):
                            # Count devices from ip_state.json if available
                            device_count = 0
                            for state_path in [
                                f"{building_name}/stagebox/data/ip_state.json",
                                f"{building_name}/data/ip_state.json",
                                f"{building_name}/ip_state.json"
                            ]:
                                if state_path in namelist:
                                    try:
                                        state_data = json.loads(zf.read(state_path))
                                        device_count = len(state_data.get('devices', {}))
                                        break
                                    except (json.JSONDecodeError, KeyError):
                                        pass
                            
                            buildings.append({
                                'name': building_name,
                                'device_count': device_count
                            })
                    except:
                        pass
        
        if not buildings:
            _unmount()
            return {'success': False, 'error': 'Invalid backup file. Please use a file created by Stagebox.'}
        
        # Keep mounted for potential restore
        return {
            'success': True,
            'buildings': buildings,
            'backup_path': str(zip_path)
        }
        
    except zipfile.BadZipFile:
        _unmount()
        return {'success': False, 'error': 'Invalid ZIP file'}
    except Exception as e:
        _unmount()
        return {'success': False, 'error': str(e)}


def restore_backup(zip_path: str, selections: List[Dict], buildings_dir: Path) -> Dict[str, Any]:
    """Restore selected buildings from backup.
    
    Args:
        zip_path: Path to ZIP file on USB
        selections: List of {'name': str, 'action': 'import'|'skip'|'overwrite'}
        buildings_dir: Target buildings directory
        
    Returns:
        Dict with 'success', 'imported', 'skipped', 'errors' or 'error'
    """
    zip_path = Path(zip_path)
    
    # Security check
    if not str(zip_path).startswith(str(MOUNT_POINT)):
        return {'success': False, 'error': 'Invalid backup path'}
    
    if not selections:
        return {'success': False, 'error': 'No buildings selected'}
    
    # Sanitize building names
    for sel in selections:
        name = sel.get('name', '')
        if not name or '..' in name or name.startswith('/') or '\\' in name:
            return {'success': False, 'error': 'Invalid backup file'}
    
    try:
        _ensure_mounted()
        
        if not zip_path.exists():
            _unmount()
            return {'success': False, 'error': 'Backup file not found'}
        
        imported = 0
        skipped = 0
        errors = []
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            
            for sel in selections:
                building_name = sel.get('name')
                action = sel.get('action', 'import')
                
                if not building_name:
                    continue
                
                # Verify signature
                sig_file = f"{building_name}/.stagebox"
                if sig_file not in namelist:
                    errors.append(f"{building_name}: Invalid backup")
                    continue
                
                try:
                    sig_data = json.loads(zf.read(sig_file).decode('utf-8'))
                    file_count = sig_data.get('files', 0)
                    signature = sig_data.get('sig', '')
                    if not _verify_signature(building_name, file_count, signature):
                        errors.append(f"{building_name}: Invalid backup")
                        continue
                except:
                    errors.append(f"{building_name}: Invalid backup")
                    continue
                
                target_path = buildings_dir / building_name
                
                if target_path.exists():
                    if action == 'skip':
                        skipped += 1
                        continue
                    elif action == 'overwrite':
                        # Backup existing
                        import shutil
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = buildings_dir / f"{building_name}_old_{timestamp}"
                        shutil.move(str(target_path), str(backup_path))
                
                # Extract building files
                try:
                    prefix = f"{building_name}/"
                    extracted = False
                    
                    for name in namelist:
                        if name.startswith(prefix):
                            # Security: skip suspicious paths and signature file
                            if '..' in name or name.startswith('/'):
                                continue
                            if name.endswith('/.stagebox'):
                                continue
                            
                            target_file = buildings_dir / name
                            
                            if name.endswith('/'):
                                target_file.mkdir(parents=True, exist_ok=True)
                            else:
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                with zf.open(name) as src, open(target_file, 'wb') as dst:
                                    dst.write(src.read())
                                extracted = True
                    
                    if extracted:
                        imported += 1
                    else:
                        errors.append(f"{building_name}: No files found in backup")
                        
                except Exception as e:
                    errors.append(f"{building_name}: {str(e)}")
        
        _unmount()
        
        return {
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }
        
    except zipfile.BadZipFile:
        _unmount()
        return {'success': False, 'error': 'Invalid ZIP file'}
    except Exception as e:
        _unmount()
        return {'success': False, 'error': str(e)}
