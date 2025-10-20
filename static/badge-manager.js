/**
 * WebScape Badge Notification System
 * Handles badge awards with animated toasts and Socket.IO integration
 */

(function () {
  'use strict';

  // Badge Toast HTML (will be injected once)
  const badgeToastHTML = `
    <div class="toast-container position-fixed top-0 end-0 p-3" style="z-index: 9999;">
      <div id="badgeToast" class="toast badge-toast" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-body">
          <div class="d-flex align-items-center">
            <div class="badge-icon-wrapper me-3">
              <i class="fas fa-trophy badge-trophy-icon"></i>
            </div>
            <div class="flex-grow-1">
              <div class="badge-toast-title">Badge Earned!</div>
              <div class="badge-toast-name" id="badgeToastName"></div>
            </div>
            <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
        </div>
      </div>
    </div>
  `;

  // CSS Styles for Badge Toast
  const badgeStyles = `
    <style>
      .badge-toast {
        min-width: 350px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        color: white;
        animation: slideInRight 0.5s ease-out, glow 2s ease-in-out infinite;
      }
      
      @keyframes slideInRight {
        from {
          transform: translateX(400px);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
      
      @keyframes glow {
        0%, 100% {
          box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        }
        50% {
          box-shadow: 0 10px 60px rgba(255, 215, 0, 0.6);
        }
      }
      
      .badge-toast .toast-body {
        padding: 1rem 1.25rem;
      }
      
      .badge-icon-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .badge-trophy-icon {
        font-size: 2.5rem;
        color: #ffd700;
        animation: bounce 1s ease-in-out infinite;
        filter: drop-shadow(0 4px 8px rgba(255, 215, 0, 0.5));
      }
      
      @keyframes bounce {
        0%, 100% {
          transform: translateY(0) scale(1);
        }
        50% {
          transform: translateY(-10px) scale(1.1);
        }
      }
      
      .badge-toast-title {
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
      }
      
      .badge-toast-name {
        font-weight: 600;
        font-size: 1.3rem;
        color: #ffd700;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
      }
      
      .badge-toast .btn-close-white {
        opacity: 0.8;
      }
      
      .badge-toast .btn-close-white:hover {
        opacity: 1;
      }
    </style>
  `;

  // Initialize badge toast
  function initBadgeToast() {
    // Check if toast container already exists
    if (document.getElementById('badgeToast')) {
      return;
    }

    // Inject styles
    const styleElement = document.createElement('div');
    styleElement.innerHTML = badgeStyles;
    document.head.appendChild(styleElement.firstElementChild);

    // Inject toast HTML
    const toastContainer = document.createElement('div');
    toastContainer.innerHTML = badgeToastHTML;
    document.body.appendChild(toastContainer.firstElementChild);
  }

  // Show badge notification
  function showBadgeNotification(badge) {
    console.log('🏆 Showing badge notification:', badge);
    initBadgeToast();

    const toastElement = document.getElementById('badgeToast');
    const toastName = document.getElementById('badgeToastName');

    if (!toastElement || !toastName) {
      console.error('❌ Badge toast elements not found', {
        toastElement: !!toastElement,
        toastName: !!toastName
      });
      return;
    }

    // Check if Bootstrap is loaded
    if (typeof bootstrap === 'undefined') {
      console.error('❌ Bootstrap is not loaded! Cannot show toast.');
      return;
    }

    // Set badge data
    toastName.textContent = badge.name || 'New Badge';

    console.log('✅ Badge toast configured, showing now...');

    // Show toast with longer duration (8 seconds)
    const toast = new bootstrap.Toast(toastElement, {
      autohide: true,
      delay: 8000
    });
    toast.show();

    console.log('✅ Toast.show() called');

    // Play celebration sound (optional - you can add a sound file)
    // playBadgeSound();
  }

  // Handle multiple badges
  function showBadges(badges) {
    if (!badges || badges.length === 0) return;

    // Show badges one by one with delay
    badges.forEach((badge, index) => {
      setTimeout(() => {
        showBadgeNotification(badge);
      }, index * 1000); // 1 second delay between each badge
    });
  }

  // Initialize Socket.IO listener
  function initSocketListener() {
    if (typeof io === 'undefined') {
      console.warn('Socket.IO not loaded - badge real-time notifications disabled');
      return;
    }

    try {
      const socket = io();

      socket.on('connect', function () {
        console.log('Badge system connected:', socket.id);
      });

      socket.on('badge_awarded', function (data) {
        console.log('🎉 Badge awarded via socket:', data);
        if (data && data.badges) {
          console.log('📛 Showing badges:', data.badges);
          showBadges(data.badges);
        } else {
          console.warn('⚠️ Badge data missing or invalid:', data);
        }
      });

      socket.on('disconnect', function () {
        console.log('Badge system disconnected');
      });
    } catch (error) {
      console.error('Socket.IO initialization error:', error);
    }
  }

  // Public API
  window.BadgeManager = {
    show: showBadgeNotification,
    showMultiple: showBadges,
    init: function() {
      initBadgeToast();
      initSocketListener();
    }
  };

  // Auto-initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      window.BadgeManager.init();
    });
  } else {
    window.BadgeManager.init();
  }

})();
