// Theme Manager for WebScape
// This file handles theme persistence across all pages

// Theme definitions
const themes = {
    default: {
        '--bg-color': '#240e44',
        '--secondary-color': '#371569',
        '--accent-color': '#ff66c4',
        '--sidebar-bg': '#371569',
        '--card-bg': '#371569',
        '--accent': '#ff66c4',
        '--accent-hover': '#c54fa3',
        '--text-main': '#eaeaea',
        '--text-muted': '#b3b3b3'
    },
    ocean: {
        '--bg-color': '#0f3460',
        '--secondary-color': '#16213e',
        '--accent-color': '#00d4ff',
        '--sidebar-bg': '#16213e',
        '--card-bg': '#16213e',
        '--accent': '#00d4ff',
        '--accent-hover': '#0099cc',
        '--text-main': '#e8f4fd',
        '--text-muted': '#a8d8f0'
    },
    forest: {
        '--bg-color': '#1b4332',
        '--secondary-color': '#2d6a4f',
        '--accent-color': '#52c41a',
        '--sidebar-bg': '#2d6a4f',
        '--card-bg': '#2d6a4f',
        '--accent': '#52c41a',
        '--accent-hover': '#389e0d',
        '--text-main': '#f6ffed',
        '--text-muted': '#b7eb8f'
    },
    sunset: {
        '--bg-color': '#8b4513',
        '--secondary-color': '#d2691e',
        '--accent-color': '#ff8c00',
        '--sidebar-bg': '#d2691e',
        '--card-bg': '#d2691e',
        '--accent': '#ff8c00',
        '--accent-hover': '#e67e00',
        '--text-main': '#fff8dc',
        '--text-muted': '#f4d03f'
    },
    midnight: {
        '--bg-color': '#0a0a0a',
        '--secondary-color': '#1a1a1a',
        '--accent-color': '#ffffff',
        '--sidebar-bg': '#1a1a1a',
        '--card-bg': '#1a1a1a',
        '--accent': '#ffffff',
        '--accent-hover': '#cccccc',
        '--text-main': '#ffffff',
        '--text-muted': '#888888'
    }
};

// Initialize theme from localStorage
function initializeTheme() {
    const savedTheme = localStorage.getItem('webscape-theme');
    if (savedTheme) {
        if (themes[savedTheme]) {
            applyThemeByName(savedTheme);
        } else if (savedTheme === 'custom') {
            const savedCustomTheme = localStorage.getItem('webscape-custom-theme');
            if (savedCustomTheme) {
                applyCustomTheme(JSON.parse(savedCustomTheme));
            }
        }
    }
}

// Apply theme by name
function applyThemeByName(themeName) {
    if (themes[themeName]) {
        const root = document.documentElement;
        Object.entries(themes[themeName]).forEach(([property, value]) => {
            root.style.setProperty(property, value);
        });
    }
}

// Apply custom theme
function applyCustomTheme(customTheme) {
    const root = document.documentElement;
    Object.entries(customTheme).forEach(([property, value]) => {
        root.style.setProperty(property, value);
    });
}

// Adjust brightness of a color (utility function)
function adjustBrightness(hex, percent) {
    const num = parseInt(hex.replace("#", ""), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
        (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
        (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1);
}

// Initialize theme when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
});

// Also apply theme immediately if DOM is already loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTheme);
} else {
    initializeTheme();
} 