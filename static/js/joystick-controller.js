const JoystickController = (function() {
    // Private variables
    let socket;
    let elements;
    let isDragging = false;
    let currentHeading = 0;
    let currentSpeed = 0;
    let rollTimeout = null;
    
    // Initialize the joystick controller
    function init(socketInstance, uiElements) {
        socket = socketInstance;
        elements = uiElements;
        
        // Set up joystick event listeners
        elements.joystick.addEventListener('mousedown', startDrag);
        elements.joystick.addEventListener('touchstart', startDrag, { passive: false });
        document.addEventListener('mousemove', drag);
        document.addEventListener('touchmove', drag, { passive: false });
        document.addEventListener('mouseup', endDrag);
        document.addEventListener('touchend', endDrag);
        
        return {
            getCurrentHeading: () => currentHeading,
            getCurrentSpeed: () => currentSpeed
        };
    }
    
    function startDrag(e) {
        const connected = elements.controlPad.classList.contains('active');
        if (!connected) return;
        e.preventDefault();
        isDragging = true;
    }
    
    function drag(e) {
        if (!isDragging) return;
        e.preventDefault();
        
        const pageX = e.pageX || e.touches[0].pageX;
        const pageY = e.pageY || e.touches[0].pageY;
        
        const padRect = elements.controlPad.getBoundingClientRect();
        const padCenterX = padRect.left + padRect.width / 2;
        const padCenterY = padRect.top + padRect.height / 2;
        
        // Calculate relative position from center
        let deltaX = pageX - padCenterX;
        let deltaY = pageY - padCenterY;
        
        // Calculate distance from center (speed)
        const distance = Math.min(
            Math.sqrt(deltaX * deltaX + deltaY * deltaY),
            padRect.width / 2
        );
        
        // Calculate the speed (0-255) based on distance
        const maxDistance = padRect.width / 2;
        currentSpeed = Math.round((distance / maxDistance) * 255);
        
        // Calculate angle (heading)
        let angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
        angle = (angle + 90) % 360; // Adjust so 0 is top
        if (angle < 0) angle += 360;
        currentHeading = Math.round(angle);
        
        // Update UI
        elements.directionValue.innerText = `${currentHeading}°`;
        elements.speedValue.innerText = currentSpeed;
        
        // Position the joystick
        if (distance < padRect.width / 2) {
            elements.joystick.style.left = `${pageX - padRect.left}px`;
            elements.joystick.style.top = `${pageY - padRect.top}px`;
            elements.joystick.style.transform = 'translate(-50%, -50%)';
        } else {
            // Constrain to circle edge
            const ratio = maxDistance / distance;
            elements.joystick.style.left = `${padCenterX - padRect.left + deltaX * ratio}px`;
            elements.joystick.style.top = `${padCenterY - padRect.top + deltaY * ratio}px`;
            elements.joystick.style.transform = 'translate(-50%, -50%)';
        }
        
        // Rotate direction arrow
        elements.directionArrow.style.transform = `translateX(-50%) rotate(${currentHeading}deg)`;
        
        // Send roll command with throttling
        if (rollTimeout) clearTimeout(rollTimeout);
        rollTimeout = setTimeout(() => {
            if (isDragging && elements.controlPad.classList.contains('active') && currentSpeed > 10) {
                socket.emit('roll', {
                    heading: currentHeading,
                    speed: currentSpeed,
                    duration: 1.0 // Keep rolling continuously
                });
            }
        }, 100); // Throttle to avoid too many commands
    }
    
    function endDrag() {
        if (!isDragging) return;
        isDragging = false;
        
        // Reset joystick position
        elements.joystick.style.left = '50%';
        elements.joystick.style.top = '50%';
        
        // Reset values
        elements.directionValue.innerText = '0°';
        elements.speedValue.innerText = '0';
        
        // Stop the Sphero by sending speed 0
        if (elements.controlPad.classList.contains('active')) {
            socket.emit('roll', {
                heading: currentHeading,
                speed: 0,
                duration: 0.1
            });
        }
        
        if (rollTimeout) clearTimeout(rollTimeout);
    }
    
    // Public API
    return {
        init
    };
})(); 