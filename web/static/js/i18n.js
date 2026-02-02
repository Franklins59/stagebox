/**
 * Stagebox i18n (Internationalization) Module
 * 
 * Usage:
 *   await i18n.init();  // Load language on page start
 *   i18n.t('greeting.open')  // Get translation
 *   i18n.t('scripts_modal.confirm_delete', {name: 'test.js'})  // With placeholder
 *   i18n.setLanguage('de')  // Change language
 */

const i18n = (function() {
    let translations = {};
    let currentLang = 'en';
    let fallbackLang = 'en';
    let isLoaded = false;
    
    /**
     * Initialize i18n - load language from server and translations
     */
    async function init() {
        try {
            // Get current language setting from server (with cache buster)
            const response = await fetch('/api/system/language?_=' + Date.now());
            const data = await response.json();
            if (data.success && data.language) {
                currentLang = data.language;
            }
        } catch (error) {
            console.warn('Could not load language setting, using default:', fallbackLang);
            currentLang = fallbackLang;
        }
        
        // Load translations
        await loadTranslations(currentLang);
        
        // Also load fallback if different
        if (currentLang !== fallbackLang) {
            await loadTranslations(fallbackLang);
        }
        
        isLoaded = true;
        
        // Apply translations to page
        applyTranslations();
        
        return currentLang;
    }
    
    /**
     * Load translation file for a language
     */
    async function loadTranslations(lang) {
        if (translations[lang]) return; // Already loaded
        
        try {
            const response = await fetch(`/static/i18n/${lang}.json`);
            if (response.ok) {
                translations[lang] = await response.json();
            } else {
                console.warn(`Translation file not found: ${lang}.json`);
            }
        } catch (error) {
            console.error(`Error loading translations for ${lang}:`, error);
        }
    }
    
    /**
     * Get translation for a key
     * @param {string} key - Dot-notation key like 'greeting.open'
     * @param {object} params - Optional parameters for placeholders
     * @returns {string} Translated text or key if not found
     */
    function t(key, params = {}) {
        let text = getNestedValue(translations[currentLang], key);
        
        // Fallback to default language
        if (text === undefined && currentLang !== fallbackLang) {
            text = getNestedValue(translations[fallbackLang], key);
        }
        
        // Fallback to key name
        if (text === undefined) {
            console.warn(`Missing translation: ${key}`);
            return `[${key}]`;
        }
        
        // Replace placeholders like {name}, {count}
        Object.keys(params).forEach(param => {
            text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
        });
        
        return text;
    }
    
    /**
     * Get nested value from object using dot notation
     */
    function getNestedValue(obj, key) {
        if (!obj) return undefined;
        return key.split('.').reduce((o, k) => (o && o[k] !== undefined) ? o[k] : undefined, obj);
    }
    
    /**
     * Change language
     */
    async function setLanguage(lang) {
        if (lang === currentLang) return;
        
        // Save to server
        try {
            const response = await fetch('/api/system/language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language: lang })
            });
            
            const data = await response.json();
            if (!data.success) {
                console.error('Failed to save language setting');
                return false;
            }
        } catch (error) {
            console.error('Error saving language:', error);
            return false;
        }
        
        // Load new translations
        await loadTranslations(lang);
        currentLang = lang;
        
        // Re-apply translations
        applyTranslations();
        
        return true;
    }
    
    /**
     * Get current language
     */
    function getLanguage() {
        return currentLang;
    }
    
    /**
     * Get all available languages
     */
    function getAvailableLanguages() {
        return ['en', 'de', 'fr', 'it', 'nl'];
    }
    
    /**
     * Apply translations to all elements with data-i18n attribute
     * 
     * Usage in HTML:
     *   <span data-i18n="greeting.open">Open</span>
     *   <input data-i18n-placeholder="device_list.search_placeholder">
     *   <button data-i18n-title="common.refresh">🔄</button>
     */
    function applyTranslations() {
        // Text content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = t(key);
            if (!text.startsWith('[')) {
                el.textContent = text;
            }
        });
        
        // Placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const text = t(key);
            if (!text.startsWith('[')) {
                el.placeholder = text;
            }
        });
        
        // Titles (tooltips)
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            const text = t(key);
            if (!text.startsWith('[')) {
                el.title = text;
            }
        });
        
        // HTML content (for formatted text)
        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            const text = t(key);
            if (!text.startsWith('[')) {
                el.innerHTML = text;
            }
        });
    }
    
    /**
     * Check if translations are loaded
     */
    function ready() {
        return isLoaded;
    }
    
    // Public API
    return {
        init,
        t,
        setLanguage,
        getLanguage,
        getAvailableLanguages,
        applyTranslations,
        ready
    };
})();

// Make t() available globally for convenience
const t = (key, params) => i18n.t(key, params);
