const UI = (function() {
    // Private variables
    let elements = {};
    let isConnected = false;
    let isRandomMovementActive = false;
    
    // Get all UI elements
    function getElements() {
        return {
            scanBtn: document.getElementById('scanBtn'),
            toySelector: document.getElementById('toySelector'),
            connectBtn: document.getElementById('connectBtn'),
            disconnectBtn: document.getElementById('disconnectBtn'),
            statusMessage: document.getElementById('statusMessage'),
            
            redRange: document.getElementById('redRange'),
            greenRange: document.getElementById('greenRange'),
            blueRange: document.getElementById('blueRange'),
            colorPreview: document.getElementById('colorPreview'),
            setColorBtn: document.getElementById('setColorBtn'),
            
            controlPad: document.getElementById('controlPad'),
            joystick: document.getElementById('joystick'),
            directionArrow: document.querySelector('.direction-arrow'),
            directionValue: document.getElementById('directionValue'),
            speedValue: document.getElementById('speedValue'),
            
            spinBtn: document.getElementById('spinBtn'),
            spinDegrees: document.getElementById('spinDegrees'),
            spinDuration: document.getElementById('spinDuration'),
            
            startRandomBtn: document.getElementById('startRandomBtn'),
            stopRandomBtn: document.getElementById('stopRandomBtn'),
            
            startOpenAISessionBtn: document.getElementById('startOpenAISessionBtn'),
            stopOpenAISessionBtn: document.getElementById('stopOpenAISessionBtn'),
            openaiStatusMessage: document.getElementById('openaiStatusMessage')
        };
    }
    
    // Initialize UI
    function init(socket, socketHandler, joystickController, openAIController, uiElements) {
        elements = uiElements;
        
        // Set up event listeners
        elements.scanBtn.addEventListener('click', socketHandler.scan);
        elements.connectBtn.addEventListener('click', socketHandler.connectToSphero);
        elements.disconnectBtn.addEventListener('click', socketHandler.disconnectFromSphero);
        elements.setColorBtn.addEventListener('click', socketHandler.setColor);
        elements.spinBtn.addEventListener('click', socketHandler.spin);
        elements.startRandomBtn.addEventListener('click', socketHandler.startRandomMovement);
        elements.stopRandomBtn.addEventListener('click', socketHandler.stopRandomMovement);
        elements.toySelector.addEventListener('change', updateUIState);
        
        // Color preview
        elements.redRange.addEventListener('input', updateColorPreview);
        elements.greenRange.addEventListener('input', updateColorPreview);
        elements.blueRange.addEventListener('input', updateColorPreview);
        
        // OpenAI controls
        elements.startOpenAISessionBtn.addEventListener('click', openAIController.startSession);
        elements.stopOpenAISessionBtn.addEventListener('click', openAIController.stopSession);
        
        // Initial UI updates
        updateColorPreview();
        updateUIState();
        updateOpenAIUIState();
    }
    
    // Update color preview
    function updateColorPreview() {
        const r = elements.redRange.value;
        const g = elements.greenRange.value;
        const b = elements.blueRange.value;
        elements.colorPreview.style.backgroundColor = `rgb(${r},${g},${b})`;
    }
    
    // Update UI based on connection state
    function updateUIState() {
        elements.connectBtn.disabled = isConnected || elements.toySelector.value === '';
        elements.disconnectBtn.disabled = !isConnected;
        elements.setColorBtn.disabled = !isConnected;
        elements.spinBtn.disabled = !isConnected;
        elements.startRandomBtn.disabled = !isConnected || isRandomMovementActive;
        elements.stopRandomBtn.disabled = !isConnected || !isRandomMovementActive;
        
        if (isConnected) {
            elements.controlPad.classList.add('active');
        } else {
            elements.controlPad.classList.remove('active');
        }
    }
    
    function updateOpenAIUIState(isOpenAISessionActive) {
        elements.startOpenAISessionBtn.disabled = isOpenAISessionActive;
        elements.stopOpenAISessionBtn.disabled = !isOpenAISessionActive;
    }
    
    function updateRandomMovementUI() {
        elements.startRandomBtn.disabled = !isConnected || isRandomMovementActive;
        elements.stopRandomBtn.disabled = !isConnected || !isRandomMovementActive;
    }
    
    // Public methods
    return {
        getElements,
        init,
        updateUIState: function(connected) {
            isConnected = connected;
            updateUIState();
        },
        updateRandomMovementUI: function(active) {
            isRandomMovementActive = active;
            updateRandomMovementUI();
        },
        updateOpenAIUIState,
        updateColorPreview
    };
})(); 