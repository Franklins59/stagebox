from pathlib import Path
import os, tempfile

def atomic_write(path: str, data_bytes: bytes) -> None:
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    
    # Get original file ownership/permissions if file exists
    original_uid = None
    original_gid = None
    original_mode = 0o644  # default for new files
    
    if dst.exists():
        stat_info = dst.stat()
        original_uid = stat_info.st_uid
        original_gid = stat_info.st_gid
        original_mode = stat_info.st_mode
    
    with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as tmp:
        tmp.write(data_bytes)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    
    # Restore original ownership and permissions
    if original_uid is not None and original_gid is not None:
        try:
            os.chown(tmp_path, original_uid, original_gid)
        except (OSError, PermissionError):
            pass  # Can't change ownership if not running as root
    
    os.chmod(tmp_path, original_mode)
    os.replace(tmp_path, dst)