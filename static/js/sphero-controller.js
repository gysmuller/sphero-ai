document.addEventListener('DOMContentLoaded', function() {
    // Socket.io setup
    const socket = io();
    let isConnected = false;
    
    // UI elements
    const scanBtn = document.getElementById('scanBtn');
    const toySelector = document.getElementById('toySelector');
    const connectBtn = document.getElementById('connectBtn');
    const disconnectBtn = document.getElementById('disconnectBtn');
    const statusMessage = document.getElementById('statusMessage');
    
    const redRange = document.getElementById('redRange');
    const greenRange = document.getElementById('greenRange');
    const blueRange = document.getElementById('blueRange');
    const colorPreview = document.getElementById('colorPreview');
    const setColorBtn = document.getElementById('setColorBtn');
    
    const controlPad = document.getElementById('controlPad');
    const joystick = document.getElementById('joystick');
    const directionArrow = document.querySelector('.direction-arrow');
    const directionValue = document.getElementById('directionValue');
    const speedValue = document.getElementById('speedValue');
    
    const spinBtn = document.getElementById('spinBtn');
    const spinDegrees = document.getElementById('spinDegrees');
    const spinDuration = document.getElementById('spinDuration');
    
    const startRandomBtn = document.getElementById('startRandomBtn');
    const stopRandomBtn = document.getElementById('stopRandomBtn');
    let isRandomMovementActive = false;

    // OpenAI elements
    const startOpenAISessionBtn = document.getElementById('startOpenAISessionBtn');
    const stopOpenAISessionBtn = document.getElementById('stopOpenAISessionBtn');
    const openaiStatusMessage = document.getElementById('openaiStatusMessage');

    // OpenAI/WebRTC variables
    let pc = null; // RTCPeerConnection
    let dc = null; // RTCDataChannel
    let localStream = null;
    let isOpenAISessionActive = false;
    
    // Update color preview
    function updateColorPreview() {
        const r = redRange.value;
        const g = greenRange.value;
        const b = blueRange.value;
        colorPreview.style.backgroundColor = `rgb(${r},${g},${b})`;
    }
    
    redRange.addEventListener('input', updateColorPreview);
    greenRange.addEventListener('input', updateColorPreview);
    blueRange.addEventListener('input', updateColorPreview);
    updateColorPreview();
    
    // Socket.io event handlers
    socket.on('connect', function() {
        console.log('Connected to server');
        socket.emit('check_connection_status');
    });
    
    socket.on('connection_status', function(data) {
        isConnected = data.connected;
        updateUIState();
        
        if (isConnected) {
            statusMessage.innerText = 'Connected to Sphero';
        }
    });
    
    socket.on('scan_result', function(data) {
        toySelector.innerHTML = '';
        
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.innerText = 'Select a Sphero';
        toySelector.appendChild(defaultOption);
        
        data.toys.forEach((toy, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.innerText = toy;
            toySelector.appendChild(option);
        });
        
        if (data.toys.length > 0) {
            toySelector.disabled = false;
            statusMessage.innerText = `Found ${data.toys.length} Sphero toys`;
        } else {
            statusMessage.innerText = 'No Sphero toys found';
        }
        
        scanBtn.disabled = false;
    });
    
    socket.on('status', function(data) {
        statusMessage.innerText = data.message;
    });
    
    socket.on('random_movement_status', function(data) {
        isRandomMovementActive = data.active;
        updateRandomMovementUI();
    });
    
    // Button event handlers
    scanBtn.addEventListener('click', function() {
        statusMessage.innerText = 'Scanning for Sphero toys...';
        scanBtn.disabled = true;
        socket.emit('scan');
    });
    
    connectBtn.addEventListener('click', function() {
        const selectedToy = toySelector.value;
        if (selectedToy !== '') {
            socket.emit('connect_to_sphero', { toy_index: selectedToy });
        }
    });
    
    disconnectBtn.addEventListener('click', function() {
        socket.emit('disconnect_from_sphero');
    });
    
    setColorBtn.addEventListener('click', function() {
        const r = redRange.value;
        const g = greenRange.value;
        const b = blueRange.value;
        socket.emit('set_color', { r, g, b });
    });
    
    spinBtn.addEventListener('click', function() {
        const degrees = spinDegrees.value;
        const duration = spinDuration.value;
        socket.emit('spin', { degrees, duration });
    });
    
    startRandomBtn.addEventListener('click', function() {
        socket.emit('start_random_movement');
        isRandomMovementActive = true;
        updateRandomMovementUI();
    });
    
    stopRandomBtn.addEventListener('click', function() {
        socket.emit('stop_random_movement');
        isRandomMovementActive = false;
        updateRandomMovementUI();
    });
    
    // OpenAI Button Handlers
    startOpenAISessionBtn.addEventListener('click', startOpenAISession);
    stopOpenAISessionBtn.addEventListener('click', stopOpenAISession);
    
    // Joystick control
    let isDragging = false;
    let currentHeading = 0;
    let currentSpeed = 0;
    let rollTimeout = null;
    
    joystick.addEventListener('mousedown', startDrag);
    joystick.addEventListener('touchstart', startDrag, { passive: false });
    document.addEventListener('mousemove', drag);
    document.addEventListener('touchmove', drag, { passive: false });
    document.addEventListener('mouseup', endDrag);
    document.addEventListener('touchend', endDrag);
    
    function startDrag(e) {
        if (!isConnected) return;
        e.preventDefault();
        isDragging = true;
    }
    
    function drag(e) {
        if (!isDragging) return;
        e.preventDefault();
        
        const pageX = e.pageX || e.touches[0].pageX;
        const pageY = e.pageY || e.touches[0].pageY;
        
        const padRect = controlPad.getBoundingClientRect();
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
        directionValue.innerText = `${currentHeading}°`;
        speedValue.innerText = currentSpeed;
        
        // Position the joystick
        if (distance < padRect.width / 2) {
            joystick.style.left = `${pageX - padRect.left}px`;
            joystick.style.top = `${pageY - padRect.top}px`;
            joystick.style.transform = 'translate(-50%, -50%)';
        } else {
            // Constrain to circle edge
            const ratio = maxDistance / distance;
            joystick.style.left = `${padCenterX - padRect.left + deltaX * ratio}px`;
            joystick.style.top = `${padCenterY - padRect.top + deltaY * ratio}px`;
            joystick.style.transform = 'translate(-50%, -50%)';
        }
        
        // Rotate direction arrow
        directionArrow.style.transform = `translateX(-50%) rotate(${currentHeading}deg)`;
        
        // Send roll command with throttling
        if (rollTimeout) clearTimeout(rollTimeout);
        rollTimeout = setTimeout(() => {
            if (isDragging && isConnected && currentSpeed > 10) {
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
        joystick.style.left = '50%';
        joystick.style.top = '50%';
        
        // Reset values
        directionValue.innerText = '0°';
        speedValue.innerText = '0';
        
        // Stop the Sphero by sending speed 0
        if (isConnected) {
            socket.emit('roll', {
                heading: currentHeading,
                speed: 0,
                duration: 0.1
            });
        }
        
        if (rollTimeout) clearTimeout(rollTimeout);
    }
    
    function updateRandomMovementUI() {
        startRandomBtn.disabled = !isConnected || isRandomMovementActive;
        stopRandomBtn.disabled = !isConnected || !isRandomMovementActive;
    }
    
    // Function to update UI based on connection state
    function updateUIState() {
        connectBtn.disabled = isConnected || toySelector.value === '';
        disconnectBtn.disabled = !isConnected;
        setColorBtn.disabled = !isConnected;
        spinBtn.disabled = !isConnected;
        startRandomBtn.disabled = !isConnected || isRandomMovementActive;
        stopRandomBtn.disabled = !isConnected || !isRandomMovementActive;
        
        if (isConnected) {
            controlPad.classList.add('active');
        } else {
            controlPad.classList.remove('active');
        }
    }
    
    // Add change listener to toy selector
    toySelector.addEventListener('change', updateUIState);

    // OpenAI Functions
    async function startOpenAISession() {
        if (isOpenAISessionActive) return;
        openaiStatusMessage.innerText = "Connecting to Livvy's voice control...";
        startOpenAISessionBtn.disabled = true;

        try {
            // 1. Get an ephemeral key from the backend /session endpoint
            const tokenResponse = await fetch("/session", { method: "POST" });
            if (!tokenResponse.ok) {
                const errorData = await tokenResponse.json();
                throw new Error(`Failed to connect: ${errorData.error || tokenResponse.statusText}`);
            }
            const sessionData = await tokenResponse.json();
            const EPHEMERAL_KEY = sessionData.client_secret.value;
            openaiStatusMessage.innerText = "Connection established. Setting up voice...";

            // 2. Create RTCPeerConnection
            pc = new RTCPeerConnection();

            // 3. Set up to play remote audio (if OpenAI sends any - not expected for function calling only)
            // const audioEl = document.createElement("audio");
            // audioEl.autoplay = true;
            // pc.ontrack = e => audioEl.srcObject = e.streams[0];
            pc.ontrack = e => console.log("Received remote audio track (unexpected)");

            // 4. Add local audio track for microphone input
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
                openaiStatusMessage.innerText = "Microphone access granted.";
            } catch (err) {
                openaiStatusMessage.innerText = `Error accessing microphone: ${err.message}. Please grant permission.`;
                throw new Error(`Microphone access denied: ${err.message}`);
            }

            // 5. Set up data channel for sending and receiving events
            dc = pc.createDataChannel("oai-events");
            dc.onopen = () => {
                openaiStatusMessage.innerText = "Livvy is listening. Try saying: 'Hey Livvy, can you dance for me?'";
                isOpenAISessionActive = true;
                updateOpenAIUIState();
                console.log("OpenAI Data Channel opened");
                // Optional: Send initial session update if needed (e.g., system prompt)
                // dc.send(JSON.stringify({ type: "session.update", session: { instructions: "..." } }));
            };
            dc.onmessage = handleOpenAIEvent;
            dc.onclose = () => {
                openaiStatusMessage.innerText = "OpenAI data channel closed.";
                console.log("OpenAI Data Channel closed");
                stopOpenAISession(); // Clean up if channel closes unexpectedly
            };
            dc.onerror = (error) => {
                openaiStatusMessage.innerText = `OpenAI data channel error: ${error}`;
                console.error("OpenAI Data Channel error:", error);
                stopOpenAISession(); // Clean up on error
            };

            // 6. Start the session using SDP
            const offer = await pc.createOffer({
                offerToReceiveAudio: false,
                offerToReceiveVideo: false
              });
            await pc.setLocalDescription(offer);
            openaiStatusMessage.innerText = "Sending connection offer to OpenAI...";

            const sdpResponse = await fetch(`https://api.openai.com/v1/realtime`, {
                method: "POST",
                body: offer.sdp,
                headers: {
                    Authorization: `Bearer ${EPHEMERAL_KEY}`,
                    "Content-Type": "application/sdp",
                },
            });

            if (!sdpResponse.ok) {
                throw new Error(`Failed to connect to OpenAI Realtime: ${sdpResponse.statusText}`);
            }

            const answer = {
                type: "answer",
                sdp: await sdpResponse.text(),
            };
            await pc.setRemoteDescription(answer);
            openaiStatusMessage.innerText = "Livvy is ready! Start talking to control Livvy.";
            console.log("WebRTC connection established with OpenAI");

        } catch (error) {
            console.error("Error starting OpenAI session:", error);
            openaiStatusMessage.innerText = `Error: ${error.message}`;
            stopOpenAISession(); // Ensure cleanup on error
            updateOpenAIUIState();
        }
    }

    function stopOpenAISession() {
        console.log("Stopping voice session...");
        if (dc) {
            dc.close();
            dc = null;
        }
        if (pc) {
            pc.close();
            pc = null;
        }
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
        isOpenAISessionActive = false;
        updateOpenAIUIState();
        openaiStatusMessage.innerText = "Voice control disabled. Livvy is waiting.";
    }

    function handleOpenAIEvent(event) {
        try {
            const serverEvent = JSON.parse(event.data);
            console.log("Voice Event Received:", serverEvent);
            
            // Instead of processing locally, send to backend for processing
            socket.emit('process_openai_response', { event: serverEvent });
            
            // Update user about receiving a response
            if (serverEvent.type === "response.done") {
                openaiStatusMessage.innerText = "Processing response from Livvy...";
            }
            
        } catch (error) {
            console.error("Error parsing OpenAI event:", error, "Raw data:", event.data);
            openaiStatusMessage.innerText = `Error parsing OpenAI response: ${error.message}`;
        }
    }

    // Listen for status updates from the backend about OpenAI processing
    socket.on('openai_status', function(data) {
        openaiStatusMessage.innerText = data.message;
    });

    function updateOpenAIUIState() {
        startOpenAISessionBtn.disabled = isOpenAISessionActive;
        stopOpenAISessionBtn.disabled = !isOpenAISessionActive;
    }

    // Initial UI state
    updateUIState();
    updateOpenAIUIState();
}); 