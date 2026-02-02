"""
Stagebox Core Module Loader

Handles dynamic loading of core provisioning modules.
"""

from typing import Any, Callable, Optional

# Module availability flags
CORE_AVAILABLE = False
STAGE2_AVAILABLE = False
STAGE3_AVAILABLE = False
STAGE4_AVAILABLE = False

# Stage 2 imports
stage2_discover_and_adopt: Optional[Callable] = None
stage2_configure_device_by_ip: Optional[Callable] = None

# Stage 3 imports
Stage3Config: Optional[type] = None
Stage3OtaConfig: Optional[type] = None
Stage3FriendlyConfig: Optional[type] = None
stage3_process_device: Optional[Callable] = None
run_stage3_on_state_dict: Optional[Callable] = None

# Stage 4 imports
Stage4Config: Optional[type] = None
load_all_profiles: Optional[Callable] = None
run_stage4_for_device: Optional[Callable] = None
run_stage4_on_state: Optional[Callable] = None

# RPC Client
RpcClient: Optional[type] = None

# State management
load_state: Optional[Callable] = None
save_state_atomic_with_bak: Optional[Callable] = None
update_device: Optional[Callable] = None
State: Optional[type] = None


def reload_core_modules():
    """Reload core modules after building activation."""
    global CORE_AVAILABLE, STAGE2_AVAILABLE, STAGE3_AVAILABLE, STAGE4_AVAILABLE
    global stage2_discover_and_adopt, stage2_configure_device_by_ip
    global Stage3Config, Stage3OtaConfig, Stage3FriendlyConfig
    global stage3_process_device, run_stage3_on_state_dict
    global Stage4Config, load_all_profiles, run_stage4_for_device, run_stage4_on_state
    global RpcClient
    global load_state, save_state_atomic_with_bak, update_device, State
    
    from web import config
    
    if config.PROJECT_ROOT is None:
        return
    
    # Core state and RPC
    try:
        from core.rpc import RpcClient as _RpcClient
        RpcClient = _RpcClient
        CORE_AVAILABLE = True
    except ImportError as e:
        print(f"WARNING: Core RPC not available: {e}")
        CORE_AVAILABLE = False
    
    # Stage 2
    try:
        from core.provision.stage2_core import (
            stage2_discover_and_adopt as _s2_discover,
            stage2_configure_device_by_ip as _s2_configure,
        )
        stage2_discover_and_adopt = _s2_discover
        stage2_configure_device_by_ip = _s2_configure
        STAGE2_AVAILABLE = True
    except ImportError as e:
        print(f"WARNING: Stage 2 core not available: {e}")
        STAGE2_AVAILABLE = False
    
    # Stage 3
    try:
        from core.provision.stage3_core import (
            Stage3Config as _S3Config,
            Stage3OtaConfig as _S3OtaConfig,
            Stage3FriendlyConfig as _S3FriendlyConfig,
            process_device as _s3_process,
            run_stage3_on_state_dict as _s3_run,
        )
        Stage3Config = _S3Config
        Stage3OtaConfig = _S3OtaConfig
        Stage3FriendlyConfig = _S3FriendlyConfig
        stage3_process_device = _s3_process
        run_stage3_on_state_dict = _s3_run
        STAGE3_AVAILABLE = True
    except ImportError as e:
        print(f"WARNING: Stage 3 core not available: {e}")
        STAGE3_AVAILABLE = False
    
    # Stage 4
    try:
        from core.provision.stage4_core import (
            Stage4Config as _S4Config,
            load_all_profiles as _s4_load_profiles,
            run_stage4_for_device as _s4_run_device,
            run_stage4_on_state as _s4_run,
        )
        Stage4Config = _S4Config
        load_all_profiles = _s4_load_profiles
        run_stage4_for_device = _s4_run_device
        run_stage4_on_state = _s4_run
        STAGE4_AVAILABLE = True
    except ImportError as e:
        print(f"WARNING: Stage 4 core not available: {e}")
        STAGE4_AVAILABLE = False
    
    # State management
    try:
        from core.state import (
            load_state as _load_state,
            save_state_atomic_with_bak as _save_state,
            update_device as _update_device,
            State as _State,
        )
        load_state = _load_state
        save_state_atomic_with_bak = _save_state
        update_device = _update_device
        State = _State
    except ImportError as e:
        print(f"WARNING: Core state not available: {e}")
