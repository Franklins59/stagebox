/**
 * Main Application Controller
 */

const App = {
    refreshInterval: null,
    statusCheckInterval: null,
    activeBuilding: null,
    
    async init() {
        console.log('Initializing Stagebox Dashboard...');
        
        // Initialize i18n first
        await i18n.init();
        
        // Update manual link with language
        this.updateManualLink();
        
        // Load active building info
        await this.loadBuildingInfo();
        
        // Load edition info
        await this.loadEditionInfo();
        
        UI.init();
        
        await this.checkBackend();
        
        await this.loadDevices();
        
        this.startStatusChecking();
        
        // Auto-refresh disabled - use Refresh button instead
        // this.startAutoRefresh();
        
        console.log('Dashboard initialized successfully');
    },
    
    updateManualLink() {
        const lang = i18n.getLanguage();
        const manualLink = document.getElementById('manual-link');
        if (manualLink && lang !== 'en') {
            manualLink.href = `/manual?lang=${lang}`;
        }
    },
    
    async loadBuildingInfo() {
        try {
            const response = await fetch('/api/buildings/active');
            const data = await response.json();
            
            if (data.success && data.active) {
                this.activeBuilding = data.active;
                const nameEl = document.getElementById('building-name');
                if (nameEl) {
                    nameEl.textContent = data.active;
                }
            }
        } catch (error) {
            console.error('Error loading building info:', error);
        }
    },
    
    async loadEditionInfo() {
        try {
            const result = await API.getSystemVersion();
            if (result.success) {
                const badge = document.getElementById('edition-badge');
                if (badge) {
                    badge.textContent = result.edition_name || '';
                    badge.className = 'edition-badge edition-' + (result.edition || 'pro').toLowerCase();
                }
                // Store edition for later use
                this.edition = result.edition;
                this.isPro = result.is_pro;
                
                // Disable Pro-only features in Personal edition
                if (!result.is_pro) {
                    this.disableProFeatures();
                }
            }
        } catch (error) {
            console.error('Error loading edition info:', error);
        }
    },
    
    disableProFeatures() {
        // Find all elements with data-pro-only="true" (disable + grey out)
        const proElements = document.querySelectorAll('[data-pro-only="true"]');
        
        proElements.forEach(el => {
            el.classList.add('pro-disabled');
            el.disabled = true;
            el.title = 'This feature requires Stagebox Pro';
            
            // Prevent click events
            el.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                UI.showToast('This feature requires Stagebox Pro', 'warning');
            }, true);
        });
        
        // Find all elements with data-pro-only="hide" (completely hide)
        const hideElements = document.querySelectorAll('[data-pro-only="hide"]');
        hideElements.forEach(el => {
            el.style.display = 'none';
        });
        
        console.log(`[Personal Edition] Disabled ${proElements.length} Pro-only features, hidden ${hideElements.length} elements`);
    },
    
    async checkBackend() {
        try {
            const result = await API.checkBackendStatus();
            UI.updateBackendStatus(result.success && result.status === 'online');
        } catch (error) {
            console.error('Backend check failed:', error);
            UI.updateBackendStatus(false);
        }
    },
    
    async loadDevices() {
        try {
            UI.elements.refreshBtn.disabled = true;
            UI.elements.refreshBtn.textContent = i18n.t('device_list.syncing') || 'Syncing...';
            
            // Reset firmware update progress display
            const fwProgress = document.getElementById('firmware-progress');
            if (fwProgress) fwProgress.style.display = 'none';
            
            // First sync device info from Shellys (e.g. firmware versions)
            try {
                await API.syncDevices();
            } catch (syncError) {
                console.warn('Device sync failed:', syncError);
                // Continue with loading even if sync fails
            }
            
            UI.elements.refreshBtn.textContent = i18n.t('device_list.loading') || 'Loading...';
            
            const result = await API.getDevices();
            
            if (result.success) {
                UI.renderDeviceList(result.devices);
                this.checkDeviceStatus();
            } else {
                throw new Error(result.error || 'Failed to load devices');
            }
        } catch (error) {
            console.error('Error loading devices:', error);
            UI.showToast(`Error loading devices: ${error.message}`, 'error');
            UI.renderDeviceList([]);
        } finally {
            UI.elements.refreshBtn.disabled = false;
            UI.elements.refreshBtn.textContent = i18n.t('device_list.refresh') || 'Refresh';
        }
    },
    
    async checkDeviceStatus() {
        try {
            const result = await API.checkDeviceStatus();
            
            if (result.success) {
                UI.updateDeviceStatus(result.status);
            }
        } catch (error) {
            console.error('Error checking device status:', error);
        }
    },
    
    startStatusChecking() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
        
        this.statusCheckInterval = setInterval(() => {
            this.checkDeviceStatus();
        }, 10000);
    },
    
    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            this.loadDevices();
        }, 30000);
    },
    
    stop() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => App.init());
} else {
    App.init();
}

window.addEventListener('beforeunload', () => App.stop());

window.App = App;