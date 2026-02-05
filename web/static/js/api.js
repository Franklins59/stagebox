/**
 * Stagebox Dashboard - API Module
 * Handles all backend communication including stage execution
 */

const API = {
    baseUrl: '',
    
    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    },
    
    // =========================================================================
    // Backend Status
    // =========================================================================
    
    /**
     * Check backend status
     */
    async checkBackendStatus() {
        return await this.request('/api/backend/status');
    },
    
    /**
     * Get system version and edition info
     */
    async getSystemVersion() {
        return await this.request('/api/system/version');
    },
    
    // =========================================================================
    // Device Management
    // =========================================================================
    
    /**
     * Get all devices
     */
    async getDevices() {
        return await this.request('/api/devices');
    },
    
    /**
     * Get single device by ID (MAC)
     */
    async getDevice(deviceId) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}`);
    },
    
    /**
     * Update device metadata
     */
    async updateDevice(deviceId, data) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    
    /**
     * Check online status of all devices (ping)
     */
    async checkDeviceStatus() {
        return await this.request('/api/status');
    },
    
    /**
     * Sync device info from Shellys to database (e.g. firmware versions)
     */
    async syncDevices() {
        return await this.request('/api/devices/sync', {
            method: 'POST'
        });
    },
    
    // =========================================================================
    // Device Actions
    // =========================================================================
    
    /**
     * Reboot a device
     */
    async rebootDevice(deviceId) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}/reboot`, {
            method: 'POST'
        });
    },
    
    /**
     * Get live config from device
     */
    async getDeviceLiveConfig(deviceId) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}/live`);
    },
    
    /**
     * Update device config (writes to Shelly via RPC)
     */
    async updateDeviceConfig(deviceId, config) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}/config`, {
            method: 'PUT',
            body: JSON.stringify(config)
        });
    },
    
    /**
     * Convert device between switch and cover profile
     * WARNING: This triggers a device reboot!
     * @param {string} deviceId - Device MAC
     * @param {string} profile - "switch" or "cover"
     */
    async convertDeviceProfile(deviceId, profile) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}/convert-profile`, {
            method: 'POST',
            body: JSON.stringify({ profile })
        });
    },
    
    /**
     * Get device component settings (Switch, Cover)
     * @param {string} deviceId - Device MAC
     */
    async getDeviceSettings(deviceId) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}/settings`);
    },
    
    /**
     * Update device component settings
     * @param {string} deviceId - Device MAC
     * @param {object} settings - {switch: {...}, cover: {...}}
     */
    async updateDeviceSettings(deviceId, settings) {
        return await this.request(`/api/devices/${encodeURIComponent(deviceId)}/settings`, {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
    },
    
    // =========================================================================
    // Stage 2: Scan & Adopt
    // =========================================================================
    
    /**
     * Scan network for new Shelly devices
     */
    async stage2Scan() {
        return await this.request('/api/stage2/scan', {
            method: 'POST'
        });
    },
    
    /**
     * Adopt devices (assign static IPs)
     * @param {Object[]} devices - Array of device objects from scan (with ip, mac, was_reset, etc.)
     */
    async stage2Adopt(devices) {
        return await this.request('/api/stage2/adopt', {
            method: 'POST',
            body: JSON.stringify({ devices })
        });
    },
    
    // =========================================================================
    // Stage 3: OTA + Names
    // =========================================================================
    
    /**
     * Run Stage 3 on devices
     * @param {string[]} macs - Array of MAC addresses (or empty for all eligible)
     */
    async stage3Run(macs = []) {
        return await this.request('/api/stage3/run', {
            method: 'POST',
            body: JSON.stringify({ macs })
        });
    },
    
    /**
     * Run Stage 3 on a single device
     */
    async stage3RunSingle(mac) {
        return await this.request(`/api/stage3/run/${encodeURIComponent(mac)}`, {
            method: 'POST'
        });
    },
    
    // =========================================================================
    // Stage 4: Configure
    // =========================================================================
    
    /**
     * Run Stage 4 on devices
     * @param {string[]} macs - Array of MAC addresses (or empty for all eligible)
     */
    async stage4Run(macs = []) {
        return await this.request('/api/stage4/run', {
            method: 'POST',
            body: JSON.stringify({ macs })
        });
    },
    
    /**
     * Run Stage 4 on a single device
     */
    async stage4RunSingle(mac) {
        return await this.request(`/api/stage4/run/${encodeURIComponent(mac)}`, {
            method: 'POST'
        });
    },
    
    // =========================================================================
    // Progress Tracking
    // =========================================================================
    
    /**
     * Get progress of a running job
     * @param {string} jobId - Job ID from stage execution
     */
    async getProgress(jobId) {
        return await this.request(`/api/stage/progress/${encodeURIComponent(jobId)}`);
    },
    
    // =========================================================================
    // Admin: YAML Editor
    // =========================================================================
    
    /**
     * Get YAML file content
     * @param {string} fileType - 'config' or 'secrets'
     */
    async getYamlFile(fileType) {
        return await this.request(`/api/admin/yaml/${encodeURIComponent(fileType)}`);
    },
    
    /**
     * Save YAML file content
     * @param {string} fileType - 'config' or 'secrets'
     * @param {string} content - YAML content
     */
    async saveYamlFile(fileType, content) {
        return await this.request(`/api/admin/yaml/${encodeURIComponent(fileType)}`, {
            method: 'PUT',
            body: JSON.stringify({ content })
        });
    },
    
    /**
     * Validate YAML content without saving
     * @param {string} fileType - 'config' or 'secrets'
     * @param {string} content - YAML content to validate
     */
    async validateYaml(fileType, content) {
        return await this.request(`/api/admin/yaml/${encodeURIComponent(fileType)}/validate`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    },
    
    /**
     * List available backups for a YAML file
     * @param {string} fileType - 'config' or 'secrets'
     */
    async listYamlBackups(fileType) {
        return await this.request(`/api/admin/yaml/${encodeURIComponent(fileType)}/backups`);
    },
    
    /**
     * Restore YAML file from backup
     * @param {string} fileType - 'config' or 'secrets'
     * @param {string} backupPath - Full path to backup file
     */
    async restoreYamlBackup(fileType, backupPath) {
        return await this.request(`/api/admin/yaml/${encodeURIComponent(fileType)}/restore`, {
            method: 'POST',
            body: JSON.stringify({ backup_path: backupPath })
        });
    },
    
    // =========================================================================
    // Building Settings (No PIN required)
    // =========================================================================
    
    /**
     * Get building settings (WiFi + Network ranges)
     */
    async getBuildingSettings() {
        return await this.request('/api/settings/building');
    },
    
    /**
     * Save building settings
     * @param {object} settings - {wifi: {primary, fallback}, network: {pool_start, pool_end, dhcp_scan_start, dhcp_scan_end}}
     */
    async saveBuildingSettings(settings) {
        return await this.request('/api/settings/building', {
            method: 'PUT',
            body: JSON.stringify(settings)
        });
    },
    
    /**
     * Validate network settings without saving
     * @param {object} network - {pool_start, pool_end, dhcp_scan_start, dhcp_scan_end}
     */
    async validateNetworkSettings(network) {
        return await this.request('/api/settings/building/validate-network', {
            method: 'POST',
            body: JSON.stringify(network)
        });
    }
};

// Export for use in other modules
window.API = API;
