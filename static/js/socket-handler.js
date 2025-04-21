const SocketHandler = (function() {
    // Private variables
    let socket;
    let elements;
    let isConnected = false;
    let isRandomMovementActive = false;
    
    // Initialize module
    function init(socketInstance, uiElements) {
        socket = socketInstance;
        elements = uiElements;
        
        // Set up socket event listeners
        setupSocketEvents();
        
        // Check initial connection status
        socket.emit('check_connection_status');
        
        return {
            scan,
            connectToSphero,
            disconnectFromSphero,
            setColor,
            spin,
            startRandomMovement,
            stopRandomMovement,
            roll
        };
    }
    
    // Set up socket event listeners
    function setupSocketEvents() {
        socket.on('connect', function() {
            console.log('Connected to server');
            socket.emit('check_connection_status');
        });
        
        socket.on('connection_status', function(data) {
            isConnected = data.connected;
            UI.updateUIState(isConnected);
            
            if (isConnected) {
                elements.statusMessage.innerText = 'Connected to Sphero';
            }
        });
        
        socket.on('scan_result', function(data) {
            elements.toySelector.innerHTML = '';
            
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.innerText = 'Select a Sphero';
            elements.toySelector.appendChild(defaultOption);
            
            data.toys.forEach((toy, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.innerText = toy;
                elements.toySelector.appendChild(option);
            });
            
            if (data.toys.length > 0) {
                elements.toySelector.disabled = false;
                elements.statusMessage.innerText = `Found ${data.toys.length} Sphero toys`;
            } else {
                elements.statusMessage.innerText = 'No Sphero toys found';
            }
            
            elements.scanBtn.disabled = false;
        });
        
        socket.on('status', function(data) {
            elements.statusMessage.innerText = data.message;
        });
        
        socket.on('random_movement_status', function(data) {
            isRandomMovementActive = data.active;
            UI.updateRandomMovementUI(isRandomMovementActive);
        });
        
        socket.on('openai_status', function(data) {
            elements.openaiStatusMessage.innerText = data.message;
        });
    }
    
    // Socket command functions
    function scan() {
        elements.statusMessage.innerText = 'Scanning for Sphero toys...';
        elements.scanBtn.disabled = true;
        socket.emit('scan');
    }
    
    function connectToSphero() {
        const selectedToy = elements.toySelector.value;
        if (selectedToy !== '') {
            socket.emit('connect_to_sphero', { toy_index: selectedToy });
        }
    }
    
    function disconnectFromSphero() {
        socket.emit('disconnect_from_sphero');
    }
    
    function setColor() {
        const r = elements.redRange.value;
        const g = elements.greenRange.value;
        const b = elements.blueRange.value;
        socket.emit('set_color', { r, g, b });
    }
    
    function spin() {
        const degrees = elements.spinDegrees.value;
        const duration = elements.spinDuration.value;
        socket.emit('spin', { degrees, duration });
    }
    
    function startRandomMovement() {
        socket.emit('start_random_movement');
        isRandomMovementActive = true;
        UI.updateRandomMovementUI(isRandomMovementActive);
    }
    
    function stopRandomMovement() {
        socket.emit('stop_random_movement');
        isRandomMovementActive = false;
        UI.updateRandomMovementUI(isRandomMovementActive);
    }
    
    function roll(heading, speed, duration) {
        socket.emit('roll', {
            heading: heading,
            speed: speed,
            duration: duration
        });
    }
    
    // Public API
    return {
        init
    };
})(); 