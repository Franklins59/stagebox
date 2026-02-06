"""
Stagebox Edition Configuration

This file defines the edition at build time.
"""

# =============================================================================
# EDITION SETTING - Change this value for different builds:
#   1 = Personal
#   2 = Pro
# =============================================================================
_E = 1  # Personal Edition
# =============================================================================

# Obfuscated edition resolution (hard to find in compiled binary)
_K = [0x6F, 0x71, 0x6A, 0x60, 0x6C, 0x69, 0x6F, 0x67]  # XOR key
_P = [0x1F, 0x14, 0x18, 0x13, 0x03, 0x07, 0x0E, 0x0B]  # "personal" XOR _K
_R = [0x1F, 0x03, 0x05]                                 # "pro" XOR _K

def _decode(data):
    return ''.join(chr(data[i] ^ _K[i % len(_K)]) for i in range(len(data)))

EDITION = _decode(_P) if _E == 1 else _decode(_R)


def is_pro() -> bool:
    """Check if this is the Pro edition."""
    return _E == 2


def is_personal() -> bool:
    """Check if this is the Personal edition."""
    return _E == 1


def is_limited() -> bool:
    """Check if this edition has limitations (Personal, not Pro)."""
    return not is_pro()


def get_edition_name() -> str:
    """Get display name for the edition."""
    if is_pro():
        return "Pro"
    else:
        return "Personal"


def get_device_limit() -> int:
    """Get the device limit for this edition. 0 = unlimited."""
    return 0  # Both editions unlimited
