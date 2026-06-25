document.addEventListener('DOMContentLoaded', () => {
    // Select all tab buttons and day panels
    const tabBtns = document.querySelectorAll('.tab-btn');
    const dayPanels = document.querySelectorAll('.day-panel');
    
    // Smooth scrolling the tabs to keep active tab somewhat centered
    const tabsContainer = document.getElementById('tabs');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons and panels
            tabBtns.forEach(b => b.classList.remove('active'));
            dayPanels.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked button
            btn.classList.add('active');
            
            // Find target panel and activate it
            const targetId = btn.getAttribute('data-target');
            const targetPanel = document.getElementById(targetId);
            
            if (targetPanel) {
                targetPanel.classList.add('active');
                // Small animation when switching
                targetPanel.style.animation = 'none';
                targetPanel.offsetHeight; // trigger reflow
                targetPanel.style.animation = 'fadeIn 0.4s ease forwards';
            }
            
            // Scroll tab button into view gracefully within the scrollable container
            const btnRect = btn.getBoundingClientRect();
            const containerRect = tabsContainer.getBoundingClientRect();
            
            if (btnRect.left < containerRect.left || btnRect.right > containerRect.right) {
                btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        });
    });

    // Provide haptic feedback on devices that support vibration when clicking navigation icons
    const navButtons = document.querySelectorAll('.nav-button, .sm-btn, .btn-primary');
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            if (navigator.vibrate) {
                navigator.vibrate(50); // Small 50ms vibration
            }
        });
    });

    // =========================================================================
    // UI Enhancements: Collapsible Sections, Check-offs, Category Icons
    // =========================================================================

    // 1. Setup Time Markers (Collapsible + Marker Icon fix)
    const timeBlocks = document.querySelectorAll('.time-block');
    timeBlocks.forEach(block => {
        const marker = block.querySelector('.time-marker');
        if (marker) {
            // Add marker-icon class to the first icon
            const firstIcon = marker.querySelector('i');
            if (firstIcon) {
                firstIcon.classList.add('marker-icon');
            }
            
            // Append a toggle icon (Caret down)
            const toggleIcon = document.createElement('i');
            toggleIcon.className = 'ph-bold ph-caret-down toggle-icon';
            marker.appendChild(toggleIcon);

            // Click event to toggle collapse
            marker.addEventListener('click', () => {
                block.classList.toggle('collapsed');
                if (navigator.vibrate) navigator.vibrate(20);
            });
        }
    });

    // 2. Setup Event Cards (Checkmarks, Auto Icons, Save State)
    const eventCards = document.querySelectorAll('.event-card:not(.disney-card)');
    
    // Auto-detect keywords for icons
    const keywordIcons = [
        { keywords: ['麵', '生煎', '海鲜', '餐廳', '得月樓', '松鹤楼', '蟹', '宴'], icon: 'ph-fork-knife', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.25)' },
        { keywords: ['寺', '園', '博物館', '西湖', '古墓', '沉浸', '密室', '體驗', '外灘', '夜景'], icon: 'ph-camera', color: '#14b8a6', bg: 'rgba(20, 184, 166, 0.2)' },
        { keywords: ['街', '市集', '夜市', '百貨', '寶可夢'], icon: 'ph-shopping-bag', color: '#ec4899', bg: 'rgba(236, 72, 153, 0.2)' },
        { keywords: ['民宿', '入住', '酒店'], icon: 'ph-bed', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.2)' },
        { keywords: ['機場', '飛機'], icon: 'ph-airplane-tilt', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.2)' }
    ];

    eventCards.forEach((card, index) => {
        const infoDiv = card.querySelector('.event-info');
        if (!infoDiv) return;

        // Wrap .event-info in .event-card-inner and prepend a check button
        const innerWrapper = document.createElement('div');
        innerWrapper.className = 'event-card-inner';
        
        const checkBtn = document.createElement('button');
        checkBtn.className = 'check-btn';
        checkBtn.innerHTML = '<i class="ph-bold ph-check"></i>';
        
        card.insertBefore(innerWrapper, infoDiv);
        innerWrapper.appendChild(checkBtn);
        innerWrapper.appendChild(infoDiv);

        // Auto Icons logic
        const titleText = infoDiv.querySelector('h3') ? infoDiv.querySelector('h3').innerText : '';
        const descText = infoDiv.querySelector('.event-desc') ? infoDiv.querySelector('.event-desc').innerText : '';
        const fullText = (titleText + ' ' + descText).toLowerCase();

        let matched = false;
        for (const cat of keywordIcons) {
            if (cat.keywords.some(k => fullText.includes(k.toLowerCase()))) {
                // Prepend an auto-tag to the description if no specific icon exists yet in the description
                const descEl = infoDiv.querySelector('.event-desc');
                if (descEl && !descEl.querySelector('.ph-fill')) {
                    const tagHtml = `<span class="tag" style="background:${cat.bg}; color:${cat.color}; margin-right:6px;"><i class="ph-fill ${cat.icon}"></i></span>`;
                    descEl.insertAdjacentHTML('afterbegin', tagHtml);
                }
                matched = true;
                break;
            }
        }

        // Checkmark toggle logic + LocalStorage saving
        const storageKey = `travel_app_event_${index}`;
        
        // Restore state
        if (localStorage.getItem(storageKey) === 'completed') {
            card.classList.add('completed');
        }

        checkBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent card clicks if we add them later
            const isCompleted = card.classList.toggle('completed');
            
            if (isCompleted) {
                localStorage.setItem(storageKey, 'completed');
            } else {
                localStorage.removeItem(storageKey);
            }
            
            if (navigator.vibrate) navigator.vibrate([30, 50, 30]); // success vibration
        });
    });

    // 3. Fix for App Deep Linking (Universal Links)
    // Removing target="_blank" helps iOS/Android trigger the native APP directly
    // instead of forcing the link to open in a new browser tab.
    const amapLinks = document.querySelectorAll('a[href*="amap.com"]');
    amapLinks.forEach(link => {
        link.removeAttribute('target');
        
        // Optional: We can also add a click listener to try explicitly firing the URI scheme,
        // but without lat/lon coordinates, the safest way for surl.amap.com is relying on Universal Links.
    });
});

