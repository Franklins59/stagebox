/**
 * Stagebox Dashboard - UI Module
 * Handles all UI rendering, interactions, stage panels, and filtering
 */

const UI = {
    // State
    elements: {},
    allDevices: [],          // All devices from backend
    filteredDevices: [],     // Currently displayed devices
    selectedDevices: new Set(), // Multi-selected device IDs
    deviceStatus: {},        // Online/offline status
    selectedDevice: null,
    originalFormData: {},
    currentFilter: 'all',
    currentStage: null,
    currentTab: null,        // Currently active right panel tab
    
    /**
     * Initialize UI elements and bind events
     */
    init() {
        this.elements = {
            // Device list
            deviceList: document.getElementById('device-list'),
            deviceCount: document.getElementById('device-count'),
            searchInput: document.getElementById('search-input'),
            refreshBtn: document.getElementById('refresh-btn'),
            
            // Backend status
            backendStatus: document.getElementById('backend-status'),
            
            // Tabs
            tabBtns: document.querySelectorAll('.tab-btn'),
            
            // Details form
            deviceForm: document.getElementById('device-form'),
            saveBtn: document.getElementById('save-btn'),
            cancelBtn: document.getElementById('cancel-btn'),
            
            // Stage buttons
            stageBtns: document.querySelectorAll('.stage-btn'),
            filterBtns: document.querySelectorAll('.filter-btn'),
            
            // Stage panels
            stagePlaceholder: document.getElementById('stage-placeholder'),
            panelStage2: document.getElementById('panel-stage2'),
            panelStage3: document.getElementById('panel-stage3'),
            panelStage4: document.getElementById('panel-stage4'),
            
            // Action buttons
            btnReboot: document.getElementById('btn-reboot'),
            btnVisit: document.getElementById('btn-visit')
        };
        
        this.bindEvents();
        this.initTabs();
        this.updateEligibleCounts();
    },
    
    /**
     * Bind all event listeners
     */
    bindEvents() {
        // Search
        this.elements.searchInput.addEventListener('input', (e) => {
            this.applyFilters();
        });
        
        // Refresh button
        this.elements.refreshBtn.addEventListener('click', () => {
            window.App.loadDevices();
        });
        
        // Form events
        this.elements.deviceForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveDevice();
        });
        
        this.elements.cancelBtn.addEventListener('click', () => {
            if (this.selectedDevice) {
                this.loadDeviceDetails(this.selectedDevice);
            }
        });
        
        // Track form changes
        this.elements.deviceForm.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', () => {
                this.checkFormChanges();
            });
        });
        
        // Track settings changes (select and checkbox)
        this.elements.deviceForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', () => {
                this.checkFormChanges();
            });
        });
        
        // Track checkbox changes in settings sections
        document.querySelectorAll('#switch-settings-section input, #cover-settings-section input').forEach(input => {
            input.addEventListener('change', () => {
                this.checkFormChanges();
            });
            input.addEventListener('input', () => {
                this.checkFormChanges();
            });
        });
        
        // Stage buttons (S2, S3, S4) - open stage panels
        this.elements.stageBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const stage = btn.dataset.stage;
                this.openStagePanel(stage);
            });
        });
        
        // Filter buttons
        this.elements.filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.setFilter(btn.dataset.filter);
            });
        });
        
        // Action buttons
        if (this.elements.btnReboot) {
            this.elements.btnReboot.addEventListener('click', () => {
                this.rebootSelectedDevice();
            });
        }
        
        if (this.elements.btnVisit) {
            this.elements.btnVisit.addEventListener('click', () => {
                if (this.selectedDevice) {
                    this.visitDevice(this.selectedDevice.ip);
                }
            });
        }
        
        // Profile convert button
        const btnConvertProfile = document.getElementById('btn-convert-profile');
        if (btnConvertProfile) {
            btnConvertProfile.addEventListener('click', () => {
                this.convertDeviceProfile();
            });
        }
        
        // Stage panel buttons
        const btnScan = document.getElementById('btn-scan');
        if (btnScan) {
            btnScan.addEventListener('click', () => this.runStage2Scan());
        }
        
        const btnRunStage3 = document.getElementById('btn-run-stage3');
        if (btnRunStage3) {
            btnRunStage3.addEventListener('click', () => this.runStage3());
        }
        
        const btnRunStage4 = document.getElementById('btn-run-stage4');
        if (btnRunStage4) {
            btnRunStage4.addEventListener('click', () => this.runStage4());
        }
    },
    
    /**
     * Initialize tab switching
     */
    initTabs() {
        this.elements.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                this.switchTab(tabId);
            });
        });
    },
    
    /**
     * Switch between tabs (details/stage)
     */
    switchTab(tabId) {
        this.currentTab = tabId;
        
        this.elements.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabId);
        });
        
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.id === `tab-${tabId}`);
        });
    },
    
    /**
     * Update backend status indicator
     */
    updateBackendStatus(isOnline) {
        this.elements.backendStatus.classList.toggle('online', isOnline);
        this.elements.backendStatus.classList.toggle('offline', !isOnline);
    },
    
    // =========================================================================
    // Device List Rendering
    // =========================================================================
    
    /**
     * Render device list with current filters applied
     */
    renderDeviceList(devices) {
        this.allDevices = devices || [];
        this.applyFilters();
        this.updateEligibleCounts();
    },
    
    /**
     * Apply current filter and search to device list
     */
    applyFilters() {
        const searchQuery = this.elements.searchInput.value.toLowerCase();
        
        let filtered = this.allDevices;
        
        // Apply stage/status filter
        if (this.currentFilter !== 'all') {
            if (this.currentFilter === 'online') {
                filtered = filtered.filter(d => this.deviceStatus[d.id] === true);
            } else if (this.currentFilter === 'offline') {
                filtered = filtered.filter(d => this.deviceStatus[d.id] === false);
            } else {
                const stage = parseInt(this.currentFilter);
                filtered = filtered.filter(d => d.stage_completed === stage);
            }
        }
        
        // Apply search filter
        if (searchQuery) {
            filtered = filtered.filter(device => {
                const searchStr = `${device.friendly_name || ''} ${device.id || ''} ${device.ip || ''} ${device.location || ''} ${device.room || ''} ${device.model || ''}`.toLowerCase();
                return searchStr.includes(searchQuery);
            });
        }
        
        this.filteredDevices = filtered;
        this.renderFilteredList();
        
        // Dispatch event for tabs that use filtered devices
        document.dispatchEvent(new CustomEvent('devicesFiltered'));
    },
    
    /**
     * Render the filtered device list
     */
    renderFilteredList() {
        const devices = this.filteredDevices;
        
        if (!devices || devices.length === 0) {
            this.elements.deviceList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📦</div>
                    <div class="empty-state-text">${i18n.t('device_list.no_devices')}</div>
                </div>
            `;
            this.elements.deviceCount.textContent = `0 / ${this.allDevices.length}`;
            return;
        }
        
        this.elements.deviceCount.textContent = `${devices.length} / ${this.allDevices.length}`;
        
        this.elements.deviceList.innerHTML = devices.map(device => {
            const deviceId = device.id || device.ip || 'unknown';
            const isOnline = this.deviceStatus[deviceId];
            const statusClass = isOnline === undefined ? 'checking' : (isOnline ? 'online' : 'offline');
            const deviceName = device.friendly_name || device.id || i18n.t('device_list.unnamed');
            const stageCompleted = device.stage_completed || 0;
            const stageBadge = stageCompleted > 0 ? `S${stageCompleted}` : '--';
            const stageClass = stageCompleted === 4 ? 'stage-complete' : 
                               stageCompleted === 3 ? 'stage-3' : 
                               stageCompleted === 2 ? 'stage-2' : 'stage-none';
            
            return `
                <div class="device-item" data-id="${deviceId}">
                    <div class="device-header">
                        <div class="device-title">
                            <span class="status-indicator ${statusClass}"></span>
                            <div>
                                <div class="device-name">${this.escapeHtml(deviceName)}</div>
                                <div class="device-id">${device.ip || deviceId}</div>
                            </div>
                        </div>
                        <div class="device-actions">
                            <span class="stage-badge ${stageClass}">${stageBadge}</span>
                            <button class="visit-btn" onclick="event.stopPropagation(); window.UI.visitDevice('${device.ip}')" 
                                    title="${i18n.t('device_list.visit_title')}">${i18n.t('device_list.visit')}</button>
                        </div>
                    </div>
                    <div class="device-info">
                        <div class="device-info-item">
                            <span class="info-label">${i18n.t('details.model')}</span>
                            <span class="info-value">${device.model || 'N/A'}</span>
                        </div>
                        <div class="device-info-item">
                            <span class="info-label">${i18n.t('details.location')}</span>
                            <span class="info-value">${this.escapeHtml(device.location || 'N/A')}</span>
                        </div>
                        <div class="device-info-item">
                            <span class="info-label">${i18n.t('details.room')}</span>
                            <span class="info-value">${this.escapeHtml(device.room || 'N/A')}</span>
                        </div>
                        <div class="device-info-item">
                            <span class="info-label">FW</span>
                            <span class="info-value">${device.fw || 'N/A'}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add click handlers
        this.elements.deviceList.querySelectorAll('.device-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('button')) {
                    this.selectDevice(item.dataset.id);
                }
            });
        });
    },
    
    /**
     * Update device status indicators (online/offline)
     */
    updateDeviceStatus(status) {
        this.deviceStatus = status;
        
        Object.entries(status).forEach(([deviceId, isOnline]) => {
            const deviceItem = this.elements.deviceList.querySelector(`[data-id="${deviceId}"]`);
            if (deviceItem) {
                const indicator = deviceItem.querySelector('.status-indicator');
                indicator.classList.remove('online', 'offline', 'checking');
                indicator.classList.add(isOnline ? 'online' : 'offline');
            }
        });
    },
    
    // =========================================================================
    // Filtering
    // =========================================================================
    
    /**
     * Set current filter and update UI
     */
    setFilter(filter) {
        this.currentFilter = filter;
        
        this.elements.filterBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        this.applyFilters();
    },
    
    // =========================================================================
    // Device Selection & Details
    // =========================================================================
    
    /**
     * Select a device and show details
     */
    selectDevice(deviceId) {
        // Remove previous selection
        this.elements.deviceList.querySelectorAll('.device-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        // Add selection
        const deviceItem = this.elements.deviceList.querySelector(`[data-id="${deviceId}"]`);
        if (deviceItem) {
            deviceItem.classList.add('selected');
        }
        
        // Update selectedDevices set (single selection for now)
        this.selectedDevices.clear();
        this.selectedDevices.add(deviceId);
        
        // Find device data
        const device = this.allDevices.find(d => (d.id || d.ip) === deviceId);
        if (device) {
            this.selectedDevice = device;
            this.loadDeviceDetails(device);
            // Only switch to details if no tab is currently active (first selection)
            if (!this.currentTab) {
                this.switchTab('details');
            }
            this.updateActionButtons();
            
            // Dispatch event for KVS tab with device MAC
            document.dispatchEvent(new CustomEvent('deviceSelected', { 
                detail: { mac: device.id, ip: device.ip, device: device }
            }));
        }
        
        // Dispatch event for scripts tab and others
        document.dispatchEvent(new CustomEvent('deviceSelectionChanged'));
    },
    
    /**
     * Load device details into form
     */
    loadDeviceDetails(device) {
        // Show form, hide placeholder
        const placeholder = document.querySelector('#tab-details .placeholder');
        if (placeholder) placeholder.style.display = 'none';
        this.elements.deviceForm.style.display = 'flex';
        
        // Populate form
        document.getElementById('device-id').value = device.id || '';
        document.getElementById('device-ip').value = device.ip || '';
        document.getElementById('device-name').value = device.friendly_name || '';
        document.getElementById('device-room').value = device.room || '';
        document.getElementById('device-location').value = device.location || '';
        document.getElementById('device-model').value = device.model || '';
        
        const fwField = document.getElementById('device-fw');
        if (fwField) fwField.value = device.fw || '';
        
        const stageField = document.getElementById('device-stage');
        if (stageField) {
            const stage = device.stage_completed || 0;
            stageField.value = stage > 0 ? `Stage ${stage} completed` : 'Not provisioned';
        }
        
        // Handle Profile Convert Section (only for 2PM devices)
        this.updateProfileConvertSection(device);
        
        // Load component settings (Switch/Cover)
        this.loadDeviceSettings(device);
        
        // Store original data for change detection
        this.originalFormData = {
            friendly_name: device.friendly_name || '',
            room: device.room || '',
            location: device.location || ''
        };
        
        // Reset original settings (will be set when settings load)
        this.originalSettings = null;
        
        // Reset save button
        this.elements.saveBtn.disabled = true;
        this.clearModifiedFields();
    },
    
    /**
     * Update profile convert section visibility and state
     */
    async updateProfileConvertSection(device) {
        const section = document.getElementById('profile-convert-section');
        const currentProfileSpan = document.getElementById('current-profile');
        const convertBtn = document.getElementById('btn-convert-profile');
        
        if (!section || !currentProfileSpan || !convertBtn) return;
        
        // List of hw_models that support switch/cover profiles
        const profileSupportedModels = [
            'S3SW-002P16EU',  // 2PM Gen3
            'S2PMG3',
            'SNSW-102P16EU',  // Plus 2PM
            'SNSW-102X16EU',  // Plus 2
            'SPSW-202PE16EU', // Pro 2PM
            'SPSW-202XE16EU', // Pro 2
        ];
        
        const hwModel = device.hw_model || device.model || '';
        const supportsProfiles = profileSupportedModels.includes(hwModel);
        
        if (!supportsProfiles) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        currentProfileSpan.textContent = i18n.t('details.loading');
        convertBtn.disabled = true;
        
        // Try to get live profile from device
        let currentProfile = device.stage4?.shelly_profile || 'switch';
        
        try {
            const liveData = await API.getDeviceLiveConfig(device.id);
            if (liveData.success && liveData.device_info?.profile) {
                currentProfile = liveData.device_info.profile;
            }
        } catch (e) {
            // Use stored profile if live fetch fails
            console.log('Could not fetch live profile, using stored value');
        }
        
        const targetProfile = currentProfile === 'cover' ? 'switch' : 'cover';
        
        currentProfileSpan.textContent = currentProfile;
        currentProfileSpan.className = 'current-profile ' + currentProfile;
        
        convertBtn.textContent = i18n.t('details.convert_to', {profile: targetProfile.charAt(0).toUpperCase() + targetProfile.slice(1)});
        convertBtn.dataset.targetProfile = targetProfile;
        convertBtn.disabled = false;
    },
    
    /**
     * Load device component settings (Switch/Cover/Input/Light)
     */
    async loadDeviceSettings(device) {
        const switchSection = document.getElementById('switch-settings-section');
        const coverSection = document.getElementById('cover-settings-section');
        const lightSection = document.getElementById('light-settings-section');
        const inputSection = document.getElementById('input-settings-section');
        const inputContainer = document.getElementById('input-settings-container');
        
        // Hide all sections initially
        if (switchSection) switchSection.style.display = 'none';
        if (coverSection) coverSection.style.display = 'none';
        if (lightSection) lightSection.style.display = 'none';
        if (inputSection) inputSection.style.display = 'none';
        if (inputContainer) inputContainer.innerHTML = '';
        
        try {
            const settings = await API.getDeviceSettings(device.id);
            
            if (!settings.success) {
                console.log('Could not load device settings:', settings.error);
                return;
            }
            
            // Store current profile type
            this.currentDeviceType = settings.device_type;
            
            // Initialize original settings
            this.originalSettings = {};
            
            // Show appropriate section based on device type
            if (settings.device_type === 'cover' && settings.cover) {
                // Show Cover settings
                if (coverSection) {
                    coverSection.style.display = 'block';
                    document.getElementById('cover-name').value = settings.cover.name || '';
                    document.getElementById('cover-open-time').value = settings.cover.maxtime_open || 60;
                    document.getElementById('cover-close-time').value = settings.cover.maxtime_close || 60;
                    document.getElementById('cover-swap-inputs').checked = settings.cover.swap_inputs || false;
                    document.getElementById('cover-invert').checked = settings.cover.invert_directions || false;
                    
                    this.originalSettings.cover = { ...settings.cover };
                }
            } else if (settings.light) {
                // Show Dimmer/Light settings
                if (lightSection) {
                    lightSection.style.display = 'block';
                    document.getElementById('light-name').value = settings.light.name || '';
                    document.getElementById('light-initial-state').value = settings.light.initial_state || 'off';
                    document.getElementById('light-default-brightness').value = settings.light.default_brightness || 100;
                    document.getElementById('light-min-brightness').value = settings.light.min_brightness_on_toggle || 0;
                    document.getElementById('light-night-mode').checked = settings.light.night_mode_enable || false;
                    document.getElementById('light-night-brightness').value = settings.light.night_mode_brightness || 50;
                    document.getElementById('light-auto-off').checked = settings.light.auto_off || false;
                    document.getElementById('light-auto-off-delay').value = settings.light.auto_off_delay || 60;
                    document.getElementById('light-auto-on-delay').value = settings.light.auto_on_delay || 60;
                    
                    this.originalSettings.light = { ...settings.light };
                    this.originalSettings.inputModeSource = settings.input_mode_source;
                }
            } else if (settings.switch) {
                // Show Switch settings
                if (switchSection) {
                    switchSection.style.display = 'block';
                    
                    // Switch name
                    document.getElementById('switch-name').value = settings.switch.name || '';
                    
                    // Initial state is not supported on Minis (input_mode_source == 'switch')
                    const initialStateGroup = document.getElementById('switch-initial-state')?.closest('.form-group');
                    if (initialStateGroup) {
                        initialStateGroup.style.display = settings.input_mode_source === 'switch' ? 'none' : 'block';
                    }
                    
                    document.getElementById('switch-initial-state').value = settings.switch.initial_state || 'off';
                    document.getElementById('switch-auto-off').checked = settings.switch.auto_off || false;
                    document.getElementById('switch-auto-off-delay').value = settings.switch.auto_off_delay || 60;
                    document.getElementById('switch-auto-on').checked = settings.switch.auto_on || false;
                    document.getElementById('switch-auto-on-delay').value = settings.switch.auto_on_delay || 60;
                    
                    this.originalSettings.switch = { ...settings.switch };
                    this.originalSettings.inputModeSource = settings.input_mode_source;
                }
            }
            
            // Show Input settings if device has inputs
            if (settings.inputs && settings.inputs.length > 0 && inputSection && inputContainer) {
                inputSection.style.display = 'block';
                
                // For devices with switch component (Minis), input mode comes from switch.in_mode
                // For devices without (I4), input mode comes from input.type
                const inputModeSource = settings.input_mode_source || 'input';
                const switchInMode = settings.switch?.in_mode || 'momentary';
                
                // Store for later use when saving
                this.inputModeSource = inputModeSource;
                this.originalSettings.inputModeSource = inputModeSource;
                
                // Process and store original settings with corrected type values
                this.originalSettings.inputs = settings.inputs.map((input, idx) => {
                    let displayedType;
                    if (inputModeSource === 'switch') {
                        // Mini: derive type from in_mode
                        displayedType = switchInMode === 'follow' ? 'switch' : 'button';
                    } else {
                        // I4: use type directly
                        displayedType = input.type;
                    }
                    return {
                        id: input.id,
                        name: input.name || '',
                        type: displayedType,
                        invert: input.invert,
                        modeSource: inputModeSource,
                    };
                });
                
                // Create input rows dynamically
                settings.inputs.forEach((input, idx) => {
                    const row = document.createElement('div');
                    row.className = 'form-row input-row';
                    
                    // Determine current mode value
                    let currentMode;
                    if (inputModeSource === 'switch') {
                        currentMode = switchInMode === 'follow' ? 'switch' : 'button';
                    } else {
                        currentMode = input.type;
                    }
                    
                    const modeControl = `<select id="input-type-${input.id}" data-input-id="${input.id}" data-mode-source="${inputModeSource}">
                               <option value="button" ${currentMode === 'button' ? 'selected' : ''}>Button</option>
                               <option value="switch" ${currentMode === 'switch' ? 'selected' : ''}>Switch</option>
                           </select>`;
                    
                    row.innerHTML = `
                        <div class="form-group" style="flex: 2;">
                            <label>Input ${input.id}</label>
                            <input type="text" id="input-name-${input.id}" data-input-id="${input.id}" 
                                   value="${input.name || ''}" maxlength="32" placeholder="e.g. taster_licht">
                        </div>
                        <div class="form-group" style="flex: 1;">
                            <label>Type</label>
                            ${modeControl}
                        </div>
                        <div class="form-group checkbox-group" style="flex: 0; padding-top: 1.4rem;">
                            <label>
                                <input type="checkbox" id="input-invert-${input.id}" data-input-id="${input.id}" ${input.invert ? 'checked' : ''}>
                                Inv
                            </label>
                        </div>
                    `;
                    inputContainer.appendChild(row);
                    
                    // Add change listeners
                    row.querySelectorAll('select, input').forEach(el => {
                        el.addEventListener('change', () => this.checkFormChanges());
                    });
                });
            }
            
        } catch (e) {
            console.log('Error loading device settings:', e);
        }
    },
    
    /**
     * Get current settings from form
     */
    getCurrentSettings() {
        const settings = {};
        
        const switchSection = document.getElementById('switch-settings-section');
        const coverSection = document.getElementById('cover-settings-section');
        const lightSection = document.getElementById('light-settings-section');
        const inputSection = document.getElementById('input-settings-section');
        
        if (switchSection && switchSection.style.display !== 'none') {
            settings.switch = {
                name: document.getElementById('switch-name').value,
                initial_state: document.getElementById('switch-initial-state').value,
                auto_off: document.getElementById('switch-auto-off').checked,
                auto_off_delay: parseFloat(document.getElementById('switch-auto-off-delay').value) || 60,
                auto_on: document.getElementById('switch-auto-on').checked,
                auto_on_delay: parseFloat(document.getElementById('switch-auto-on-delay').value) || 60,
            };
        }
        
        if (coverSection && coverSection.style.display !== 'none') {
            settings.cover = {
                name: document.getElementById('cover-name').value,
                maxtime_open: parseFloat(document.getElementById('cover-open-time').value) || 60,
                maxtime_close: parseFloat(document.getElementById('cover-close-time').value) || 60,
                swap_inputs: document.getElementById('cover-swap-inputs').checked,
                invert_directions: document.getElementById('cover-invert').checked,
            };
        }
        
        if (lightSection && lightSection.style.display !== 'none') {
            settings.light = {
                name: document.getElementById('light-name').value,
                initial_state: document.getElementById('light-initial-state').value,
                default_brightness: parseInt(document.getElementById('light-default-brightness').value) || 100,
                min_brightness_on_toggle: parseInt(document.getElementById('light-min-brightness').value) || 0,
                night_mode_enable: document.getElementById('light-night-mode').checked,
                night_mode_brightness: parseInt(document.getElementById('light-night-brightness').value) || 50,
                auto_off: document.getElementById('light-auto-off').checked,
                auto_off_delay: parseFloat(document.getElementById('light-auto-off-delay').value) || 60,
                auto_on_delay: parseFloat(document.getElementById('light-auto-on-delay').value) || 60,
            };
        }
        
        if (inputSection && inputSection.style.display !== 'none') {
            settings.inputs = [];
            settings.inputModeSource = this.inputModeSource || 'input';
            
            // Find all input controls
            document.querySelectorAll('#input-settings-container select[id^="input-type-"]').forEach(el => {
                const inputId = parseInt(el.dataset.inputId);
                const invertCheckbox = document.getElementById(`input-invert-${inputId}`);
                const nameInput = document.getElementById(`input-name-${inputId}`);
                const modeSource = el.dataset.modeSource || 'input';
                
                settings.inputs.push({
                    id: inputId,
                    name: nameInput ? nameInput.value : '',
                    type: el.value,
                    invert: invertCheckbox ? invertCheckbox.checked : false,
                    modeSource: modeSource,
                });
            });
        }
        
        return settings;
    },
    
    /**
     * Check if settings have changed
     */
    hasSettingsChanged() {
        if (!this.originalSettings) return false;
        
        const current = this.getCurrentSettings();
        
        if (current.switch && this.originalSettings.switch) {
            const orig = this.originalSettings.switch;
            const curr = current.switch;
            if ((orig.name || '') !== curr.name) return true;
            if (orig.initial_state !== curr.initial_state) return true;
            if (orig.auto_off !== curr.auto_off) return true;
            if (orig.auto_off_delay !== curr.auto_off_delay) return true;
            if (orig.auto_on !== curr.auto_on) return true;
            if (orig.auto_on_delay !== curr.auto_on_delay) return true;
        }
        
        if (current.cover && this.originalSettings.cover) {
            const orig = this.originalSettings.cover;
            const curr = current.cover;
            if ((orig.name || '') !== curr.name) return true;
            if (orig.maxtime_open !== curr.maxtime_open) return true;
            if (orig.maxtime_close !== curr.maxtime_close) return true;
            if (orig.swap_inputs !== curr.swap_inputs) return true;
            if (orig.invert_directions !== curr.invert_directions) return true;
        }
        
        if (current.light && this.originalSettings.light) {
            const orig = this.originalSettings.light;
            const curr = current.light;
            if ((orig.name || '') !== curr.name) return true;
            if (orig.initial_state !== curr.initial_state) return true;
            if (orig.default_brightness !== curr.default_brightness) return true;
            if (orig.min_brightness_on_toggle !== curr.min_brightness_on_toggle) return true;
            if (orig.night_mode_enable !== curr.night_mode_enable) return true;
            if (orig.night_mode_brightness !== curr.night_mode_brightness) return true;
            if (orig.auto_off !== curr.auto_off) return true;
            if (orig.auto_off_delay !== curr.auto_off_delay) return true;
            if (orig.auto_on_delay !== curr.auto_on_delay) return true;
        }
        
        if (current.inputs && this.originalSettings.inputs) {
            for (let i = 0; i < current.inputs.length; i++) {
                const curr = current.inputs[i];
                const orig = this.originalSettings.inputs.find(inp => inp.id === curr.id);
                if (orig) {
                    if ((orig.name || '') !== curr.name) return true;
                    if (orig.type !== curr.type) return true;
                    if (orig.invert !== curr.invert) return true;
                }
            }
        }
        
        return false;
    },
    
    /**
     * Check if form has unsaved changes
     */
    checkFormChanges() {
        const currentData = {
            friendly_name: document.getElementById('device-name').value,
            room: document.getElementById('device-room').value,
            location: document.getElementById('device-location').value
        };
        
        const hasFormChanges = Object.keys(currentData).some(
            key => currentData[key] !== this.originalFormData[key]
        );
        
        const hasSettingsChanges = this.hasSettingsChanged();
        
        this.elements.saveBtn.disabled = !(hasFormChanges || hasSettingsChanges);
        
        // Mark modified fields visually
        const fieldMap = {
            friendly_name: 'device-name',
            room: 'device-room',
            location: 'device-location'
        };
        
        Object.keys(currentData).forEach(key => {
            const input = document.getElementById(fieldMap[key]);
            if (input) {
                input.classList.toggle('modified', currentData[key] !== this.originalFormData[key]);
            }
        });
    },
    
    /**
     * Clear modified field markers
     */
    clearModifiedFields() {
        this.elements.deviceForm.querySelectorAll('input').forEach(input => {
            input.classList.remove('modified');
        });
    },
    
    /**
     * Save device changes to backend and Shelly
     */
    async saveDevice() {
        if (!this.selectedDevice) return;
        
        // device.id IS the MAC (uppercase, no colons) - matches ip_state.json keys
        const deviceId = this.selectedDevice.id;
        const newName = document.getElementById('device-name').value;
        const newRoom = document.getElementById('device-room').value;
        const newLocation = document.getElementById('device-location').value;
        
        const updates = {
            friendly_name: newName,
            room: newRoom,
            location: newLocation
        };
        
        // Check if friendly_name changed (triggers Shelly device.name update)
        const nameChanged = newName !== (this.selectedDevice.friendly_name || '');
        
        try {
            this.elements.saveBtn.disabled = true;
            this.elements.saveBtn.textContent = i18n.t('details.saving');
            
            // 1. Save to ip_state.json
            const result = await API.updateDevice(deviceId, updates);
            
            if (!result.success) {
                throw new Error(result.error || 'Update failed');
            }
            
            // 2. If friendly_name changed, update Shelly device.name (sanitized for HA)
            if (nameChanged) {
                this.elements.saveBtn.textContent = i18n.t('details.writing_label');
                const configResult = await API.updateDeviceConfig(deviceId, {
                    friendly_name: newName
                });
                if (!configResult.success) {
                    this.showToast(`${i18n.t('details.saved_local_label_failed')}: ${configResult.error}`, 'warning');
                } else if (configResult.shelly_name) {
                    this.showToast(`${i18n.t('details.shelly_name_set')}: ${configResult.shelly_name}`, 'info');
                }
            }
            
            // 3. Save component settings if changed
            if (this.hasSettingsChanged()) {
                this.elements.saveBtn.textContent = i18n.t('details.writing_settings');
                const settings = this.getCurrentSettings();
                const settingsResult = await API.updateDeviceSettings(deviceId, settings);
                if (!settingsResult.success) {
                    this.showToast(`${i18n.t('details.saved_local_settings_failed')}: ${settingsResult.error}`, 'warning');
                    window.App.loadDevices();
                    return;
                }
            }
            
            this.showToast(i18n.t('details.update_success'), 'success');
            
            // Reload and re-select device
            await window.App.loadDevices();
            const updatedDevice = this.allDevices.find(d => d.id === deviceId);
            if (updatedDevice) {
                this.selectedDevice = updatedDevice;
                this.loadDeviceDetails(updatedDevice);
                document.querySelectorAll('.device-item').forEach(item => {
                    item.classList.toggle('selected', item.dataset.id === deviceId);
                });
            }
            
        } catch (error) {
            this.showToast(`${i18n.t('common.error')}: ${error.message}`, 'error');
        } finally {
            this.elements.saveBtn.textContent = i18n.t('details.save');
        }
    },
    
    /**
     * Update action button states based on selection
     */
    updateActionButtons() {
        const hasSelection = this.selectedDevice !== null;
        
        if (this.elements.btnReboot) {
            this.elements.btnReboot.disabled = !hasSelection;
        }
        if (this.elements.btnVisit) {
            this.elements.btnVisit.disabled = !hasSelection;
        }
    },
    
    // =========================================================================
    // Stage Panels
    // =========================================================================
    
    /**
     * Open a stage panel (S2, S3, or S4)
     */
    openStagePanel(stage) {
        // Convert to number for comparisons
        const stageNum = parseInt(stage, 10);
        
        // Update button states
        this.elements.stageBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.stage === stage);
        });
        
        // Hide all panels and placeholder
        this.elements.stagePlaceholder.style.display = 'none';
        this.elements.panelStage2.style.display = 'none';
        this.elements.panelStage3.style.display = 'none';
        this.elements.panelStage4.style.display = 'none';
        
        // Show selected panel
        const panel = document.getElementById(`panel-stage${stage}`);
        if (panel) {
            panel.style.display = 'block';
        }
        
        // Switch to stage tab
        this.switchTab('stage');
        this.currentStage = stageNum;
        
        // Update eligible counts
        this.updateEligibleCounts();
        
        // Render device lists for stage 3 and 4
        if (stageNum === 3) {
            this.renderStage3DeviceList();
        } else if (stageNum === 4) {
            this.renderStage4DeviceList();
        }
    },
    
    /**
     * Update the "X devices ready" counts in stage panels
     */
    updateEligibleCounts() {
        // Stage 3: devices at S2
        const stage3Eligible = this.allDevices.filter(d => d.stage_completed === 2).length;
        const stage3El = document.getElementById('stage3-eligible');
        if (stage3El) stage3El.textContent = stage3Eligible;
        
        // Stage 4: devices at S3
        const stage4Eligible = this.allDevices.filter(d => d.stage_completed === 3).length;
        const stage4El = document.getElementById('stage4-eligible');
        if (stage4El) stage4El.textContent = stage4Eligible;
        
        // Also render device lists if panels are visible
        if (this.currentStage === 3) {
            this.renderStage3DeviceList();
        } else if (this.currentStage === 4) {
            this.renderStage4DeviceList();
        }
    },
    
    // =========================================================================
    // Stage 2: Scan & Adopt
    // =========================================================================
    
    /**
     * Run Stage 2 network scan
     */
    async runStage2Scan() {
        const btnScan = document.getElementById('btn-scan');
        const resultsDiv = document.getElementById('results-stage2');
        const progressDiv = document.getElementById('progress-stage2');
        
        try {
            btnScan.disabled = true;
            btnScan.textContent = i18n.t('stage.scanning');
            progressDiv.style.display = 'block';
            this.updateProgress(2, 0, i18n.t('stage.scanning_network'));
            resultsDiv.innerHTML = '';
            
            const result = await API.stage2Scan();
            
            if (result.success && result.devices) {
                this.renderScanResults(result.devices);
                this.showToast(i18n.t('stage.found_devices', {count: result.devices.length}), 'success');
            } else {
                throw new Error(result.error || 'Scan failed');
            }
        } catch (error) {
            this.showToast(`${i18n.t('stage.scan_error')}: ${error.message}`, 'error');
            resultsDiv.innerHTML = `<div class="error-message">${i18n.t('stage.scan_failed')}: ${error.message}</div>`;
        } finally {
            btnScan.disabled = false;
            btnScan.textContent = i18n.t('stage.scan_network');
            progressDiv.style.display = 'none';
        }
    },
    
    /**
     * Render scan results with checkboxes for adoption
     */
    renderScanResults(devices) {
        const resultsDiv = document.getElementById('results-stage2');
        
        if (devices.length === 0) {
            resultsDiv.innerHTML = `<p class="no-results">${i18n.t('stage.no_devices_found')}</p>`;
            return;
        }
        
        let html = `
            <div class="scan-actions">
                <button class="btn-primary" id="btn-adopt-all">${i18n.t('stage.adopt_all')} (${devices.length})</button>
                <button class="btn-secondary" id="btn-adopt-selected" disabled>${i18n.t('stage.adopt_selected')}</button>
            </div>
            <div class="scan-results-list">
        `;
        
        devices.forEach(device => {
            const existingBadge = device.existing ? `<span class="existing-badge">${i18n.t('stage.re_adopt')}</span>` : '';
            html += `
                <div class="scan-result-item" data-ip="${device.ip}" data-mac="${device.mac}">
                    <input type="checkbox" class="scan-checkbox" checked>
                    <div class="device-info">
                        <span class="device-ip">${device.ip}</span>
                        <span class="device-model">${device.model || i18n.t('common.unknown')} ${existingBadge}</span>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        resultsDiv.innerHTML = html;
        
        // Store devices for later reference
        this._scanResults = devices;
        
        // Bind adopt buttons
        document.getElementById('btn-adopt-all').addEventListener('click', () => {
            this.runStage2Adopt(this._scanResults);
        });
        
        document.getElementById('btn-adopt-selected').addEventListener('click', () => {
            const selectedMacs = Array.from(resultsDiv.querySelectorAll('.scan-checkbox:checked'))
                .map(cb => cb.closest('.scan-result-item').dataset.mac);
            console.log('Selected MACs from DOM:', selectedMacs);
            console.log('Available devices:', this._scanResults.map(d => d.mac));
            const selectedDevices = this._scanResults.filter(d => selectedMacs.includes(d.mac));
            console.log('Filtered devices:', selectedDevices);
            this.runStage2Adopt(selectedDevices);
        });
        
        // Enable/disable adopt selected based on checkbox state
        resultsDiv.querySelectorAll('.scan-checkbox').forEach(cb => {
            cb.addEventListener('change', () => {
                const anyChecked = resultsDiv.querySelector('.scan-checkbox:checked');
                document.getElementById('btn-adopt-selected').disabled = !anyChecked;
            });
        });
    },
    
    /**
     * Run Stage 2 adoption on selected devices
     * @param {Object[]} devices - Array of device objects from scan
     */
    async runStage2Adopt(devices) {
        const progressDiv = document.getElementById('progress-stage2');
        
        try {
            progressDiv.style.display = 'block';
            this.updateProgress(2, 0, `Adopting ${devices.length} device(s)...`);
            
            const result = await API.stage2Adopt(devices);
            
            if (result.job_id) {
                await this.pollProgress(2, result.job_id);
            }
            
            this.showToast('Adoption complete', 'success');
            window.App.loadDevices();
            
        } catch (error) {
            this.showToast(`Adoption error: ${error.message}`, 'error');
        } finally {
            progressDiv.style.display = 'none';
        }
    },
    
    // =========================================================================
    // Stage 3: OTA + Names
    // =========================================================================
    
    /**
     * Render Stage 3 device list with checkboxes
     */
    renderStage3DeviceList() {
        const listDiv = document.getElementById('stage3-device-list');
        if (!listDiv) return;
        
        const eligibleDevices = this.allDevices.filter(d => d.stage_completed === 2);
        
        if (eligibleDevices.length === 0) {
            listDiv.innerHTML = `<div class="stage-empty">${i18n.t('stage.no_devices_s2')}</div>`;
            return;
        }
        
        listDiv.innerHTML = eligibleDevices.map(device => {
            const deviceName = device.friendly_name || device.id || i18n.t('device_list.unnamed');
            return `
                <div class="stage-device-item">
                    <input type="checkbox" class="stage3-checkbox" data-mac="${device.id}" checked>
                    <span class="stage-device-name">${this.escapeHtml(deviceName)}</span>
                    <span class="stage-device-ip">${device.ip || '-'}</span>
                    <span class="stage-device-model">${device.model || '-'}</span>
                </div>
            `;
        }).join('');
        
        // Update button state on checkbox change
        listDiv.querySelectorAll('.stage3-checkbox').forEach(cb => {
            cb.addEventListener('change', () => this.updateStage3Button());
        });
        
        this.updateStage3Button();
    },
    
    /**
     * Update Stage 3 Run button text
     */
    updateStage3Button() {
        const checkboxes = document.querySelectorAll('.stage3-checkbox:checked');
        const btn = document.getElementById('btn-run-stage3');
        if (btn) {
            btn.textContent = `${i18n.t('stage.run_stage3')} (${checkboxes.length})`;
            btn.disabled = checkboxes.length === 0;
        }
    },
    
    /**
     * Get selected MACs from Stage 3 list
     */
    getStage3SelectedMacs() {
        const checkboxes = document.querySelectorAll('.stage3-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.dataset.mac);
    },
    
    /**
     * Run Stage 3 on selected devices
     */
    async runStage3() {
        const progressDiv = document.getElementById('progress-stage3');
        const resultsDiv = document.getElementById('results-stage3');
        const btn = document.getElementById('btn-run-stage3');
        
        const macs = this.getStage3SelectedMacs();
        
        if (macs.length === 0) {
            this.showToast(i18n.t('stage.no_devices_selected'), 'info');
            return;
        }
        
        try {
            btn.disabled = true;
            progressDiv.style.display = 'block';
            resultsDiv.innerHTML = '';
            
            this.updateProgress(3, 0, i18n.t('stage.processing_devices', {count: macs.length}));
            
            const result = await API.stage3Run(macs);
            
            if (result.job_id) {
                const pollResult = await this.pollProgress(3, result.job_id);
                
                if (pollResult.failedDevices && pollResult.failedDevices.length > 0) {
                    const failedNames = pollResult.failedDevices.map(d => d.name || d.mac).join(', ');
                    const errorMsgs = pollResult.failedDevices.map(d => d.message).filter(m => m).join('; ');
                    this.showToast(`${i18n.t('stage.stage3_error')}: ${failedNames}${errorMsgs ? ' - ' + errorMsgs : ''}`, 'error');
                } else {
                    this.showToast(i18n.t('stage.stage3_complete'), 'success');
                }
            } else {
                this.showToast(i18n.t('stage.stage3_complete'), 'success');
            }
            window.App.loadDevices();
            
        } catch (error) {
            this.showToast(`${i18n.t('stage.stage3_error')}: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            progressDiv.style.display = 'none';
            this.renderStage3DeviceList();
        }
    },
    
    // =========================================================================
    // Stage 4: Configure
    // =========================================================================
    
    /**
     * Render Stage 4 device list with checkboxes
     */
    renderStage4DeviceList() {
        const listDiv = document.getElementById('stage4-device-list');
        if (!listDiv) return;
        
        const eligibleDevices = this.allDevices.filter(d => d.stage_completed === 3);
        
        if (eligibleDevices.length === 0) {
            listDiv.innerHTML = `<div class="stage-empty">${i18n.t('stage.no_devices_s3')}</div>`;
            return;
        }
        
        listDiv.innerHTML = eligibleDevices.map(device => {
            const deviceName = device.friendly_name || device.id || i18n.t('device_list.unnamed');
            return `
                <div class="stage-device-item">
                    <input type="checkbox" class="stage4-checkbox" data-mac="${device.id}" checked>
                    <span class="stage-device-name">${this.escapeHtml(deviceName)}</span>
                    <span class="stage-device-ip">${device.ip || '-'}</span>
                    <span class="stage-device-model">${device.model || '-'}</span>
                </div>
            `;
        }).join('');
        
        // Update button state on checkbox change
        listDiv.querySelectorAll('.stage4-checkbox').forEach(cb => {
            cb.addEventListener('change', () => this.updateStage4Button());
        });
        
        this.updateStage4Button();
    },
    
    /**
     * Update Stage 4 Run button text
     */
    updateStage4Button() {
        const checkboxes = document.querySelectorAll('.stage4-checkbox:checked');
        const btn = document.getElementById('btn-run-stage4');
        if (btn) {
            btn.textContent = `${i18n.t('stage.run_stage4')} (${checkboxes.length})`;
            btn.disabled = checkboxes.length === 0;
        }
    },
    
    /**
     * Get selected MACs from Stage 4 list
     */
    getStage4SelectedMacs() {
        const checkboxes = document.querySelectorAll('.stage4-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.dataset.mac);
    },
    
    /**
     * Run Stage 4 on selected devices
     */
    async runStage4() {
        const progressDiv = document.getElementById('progress-stage4');
        const resultsDiv = document.getElementById('results-stage4');
        const btn = document.getElementById('btn-run-stage4');
        
        const macs = this.getStage4SelectedMacs();
        
        if (macs.length === 0) {
            this.showToast(i18n.t('stage.no_devices_selected'), 'info');
            return;
        }
        
        try {
            btn.disabled = true;
            progressDiv.style.display = 'block';
            resultsDiv.innerHTML = '';
            
            this.updateProgress(4, 0, i18n.t('stage.processing_devices', {count: macs.length}));
            
            const result = await API.stage4Run(macs);
            
            if (result.job_id) {
                await this.pollProgress(4, result.job_id);
            }
            
            this.showToast(i18n.t('stage.stage4_complete'), 'success');
            window.App.loadDevices();
            
        } catch (error) {
            this.showToast(`${i18n.t('stage.stage4_error')}: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            progressDiv.style.display = 'none';
            this.renderStage4DeviceList();
        }
    },
    
    // =========================================================================
    // Progress Tracking
    // =========================================================================
    
    /**
     * Update progress bar and text
     */
    updateProgress(stage, percent, text) {
        const fill = document.getElementById(`progress-fill-${stage}`);
        const textEl = document.getElementById(`progress-text-${stage}`);
        
        if (fill) fill.style.width = `${percent}%`;
        if (textEl) textEl.textContent = text;
    },
    
    /**
     * Poll for job progress
     */
    async pollProgress(stage, jobId) {
        const resultsDiv = document.getElementById(`results-stage${stage}`);
        let finalStatus = 'completed';
        let failedDevices = [];
        
        while (true) {
            try {
                const progress = await API.getProgress(jobId);
                
                const percent = progress.total > 0 
                    ? Math.round((progress.current / progress.total) * 100) 
                    : 0;
                
                this.updateProgress(stage, percent, 
                    `${progress.current}/${progress.total} - ${progress.current_device || 'Processing...'}`);
                
                // Update results list
                if (progress.results) {
                    this.renderStageResults(resultsDiv, progress.results);
                    // Track failed devices
                    failedDevices = progress.results.filter(r => r.status === 'error');
                }
                
                if (progress.status === 'completed' || progress.status === 'failed') {
                    finalStatus = progress.status;
                    this.updateProgress(stage, 100, 
                        progress.status === 'completed' ? 'Complete!' : 'Failed');
                    break;
                }
                
                await this.sleep(500);
                
            } catch (error) {
                console.error('Progress poll error:', error);
                finalStatus = 'failed';
                break;
            }
        }
        
        return { status: finalStatus, failedDevices };
    },
    
    /**
     * Render stage execution results
     */
    renderStageResults(container, results) {
        container.innerHTML = results.map(r => {
            const icon = r.status === 'ok' ? '✓' : r.status === 'error' ? '✗' : '⋯';
            const iconClass = r.status === 'ok' ? 'ok' : r.status === 'error' ? 'error' : 'pending';
            
            return `
                <div class="result-item">
                    <span class="status-icon ${iconClass}">${icon}</span>
                    <span class="device-name">${this.escapeHtml(r.name || r.mac)}</span>
                    <span class="result-msg">${this.escapeHtml(r.message || '')}</span>
                </div>
            `;
        }).join('');
    },
    
    // =========================================================================
    // Device Actions
    // =========================================================================
    
    /**
     * Reboot selected device
     */
    async rebootSelectedDevice() {
        if (!this.selectedDevice) return;
        
        const deviceName = this.selectedDevice.friendly_name || this.selectedDevice.ip;
        if (!confirm(i18n.t('device_actions.confirm_reboot', {name: deviceName}))) {
            return;
        }
        
        try {
            const result = await API.rebootDevice(this.selectedDevice.id);
            if (result.success) {
                this.showToast(i18n.t('device_actions.reboot_sent'), 'success');
            } else {
                throw new Error(result.error || 'Reboot failed');
            }
        } catch (error) {
            this.showToast(`${i18n.t('device_actions.reboot_error')}: ${error.message}`, 'error');
        }
    },
    
    /**
     * Open device's Shelly web UI
     */
    visitDevice(ip) {
        if (ip) {
            window.open(`http://${ip}`, '_blank');
        }
    },
    
    /**
     * Convert device between switch and cover profile
     */
    async convertDeviceProfile() {
        if (!this.selectedDevice) return;
        
        const convertBtn = document.getElementById('btn-convert-profile');
        const targetProfile = convertBtn?.dataset.targetProfile;
        
        if (!targetProfile) return;
        
        const deviceName = this.selectedDevice.friendly_name || this.selectedDevice.ip;
        const confirmMsg = i18n.t('device_actions.confirm_convert', {name: deviceName, profile: targetProfile});
        
        if (!confirm(confirmMsg)) {
            return;
        }
        
        // Store device ID for re-selection after reload
        const deviceId = this.selectedDevice.id;
        
        try {
            // Disable button and show progress
            convertBtn.disabled = true;
            convertBtn.textContent = i18n.t('details.converting');
            
            const result = await API.convertDeviceProfile(deviceId, targetProfile);
            
            if (result.success) {
                if (result.changed) {
                    this.showToast(i18n.t('details.converted_to', {profile: targetProfile}), 'success');
                } else {
                    this.showToast(result.message, 'info');
                }
                
                // Reload devices and re-select this device
                await window.App.loadDevices();
                
                // Re-select the device to update the form
                const updatedDevice = this.allDevices.find(d => d.id === deviceId);
                if (updatedDevice) {
                    this.selectedDevice = updatedDevice;
                    this.loadDeviceDetails(updatedDevice);
                    // Re-highlight in list
                    document.querySelectorAll('.device-item').forEach(item => {
                        item.classList.toggle('selected', item.dataset.id === deviceId);
                    });
                }
                
            } else {
                throw new Error(result.error || 'Conversion failed');
            }
            
        } catch (error) {
            this.showToast(`${i18n.t('details.conversion_error')}: ${error.message}`, 'error');
            // Reset button on error
            if (convertBtn) {
                convertBtn.disabled = false;
                const currentProfile = this.selectedDevice?.stage4?.shelly_profile || 'switch';
                const newTarget = currentProfile === 'cover' ? 'switch' : 'cover';
                convertBtn.textContent = i18n.t('details.convert_to', {profile: newTarget.charAt(0).toUpperCase() + newTarget.slice(1)});
            }
        }
    },
    
    // =========================================================================
    // Utilities
    // =========================================================================
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 3000) {
        // Remove existing toast
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<div class="toast-message">${this.escapeHtml(message)}</div>`;
        
        document.body.appendChild(toast);
        
        // Trigger show animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },
    
    /**
     * Sleep helper
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

// Export for use in other modules
window.UI = UI;
