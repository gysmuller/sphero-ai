const OpenAIController = (function() {
    // Private variables
    let socket;
    let elements;
    let pc = null; // RTCPeerConnection
    let dc = null; // RTCDataChannel
    let localStream = null;
    let isOpenAISessionActive = false;
    
    // Initialize the OpenAI controller
    function init(socketInstance, uiElements) {
        socket = socketInstance;
        elements = uiElements;
        
        return {
            startSession,
            stopSession,
            isActive: () => isOpenAISessionActive
        };
    }
    
    // Start OpenAI voice session
    async function startSession() {
        if (isOpenAISessionActive) return;
        elements.openaiStatusMessage.innerText = "Connecting to Livvy's voice control...";
        elements.startOpenAISessionBtn.disabled = true;

        try {
            // 1. Get an ephemeral key from the backend /session endpoint
            const tokenResponse = await fetch("/session", { method: "POST" });
            if (!tokenResponse.ok) {
                const errorData = await tokenResponse.json();
                throw new Error(`Failed to connect: ${errorData.error || tokenResponse.statusText}`);
            }
            const sessionData = await tokenResponse.json();
            const EPHEMERAL_KEY = sessionData.client_secret.value;
            elements.openaiStatusMessage.innerText = "Connection established. Setting up voice...";

            // 2. Create RTCPeerConnection
            pc = new RTCPeerConnection();

            pc.ontrack = e => console.log("Received remote audio track (unexpected)");

            // 4. Add local audio track for microphone input
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
                elements.openaiStatusMessage.innerText = "Microphone access granted.";
            } catch (err) {
                elements.openaiStatusMessage.innerText = `Error accessing microphone: ${err.message}. Please grant permission.`;
                throw new Error(`Microphone access denied: ${err.message}`);
            }

            // 5. Set up data channel for sending and receiving events
            dc = pc.createDataChannel("oai-events");
            dc.onopen = () => {
                elements.openaiStatusMessage.innerText = "Livvy is listening. Try saying: 'Hey Livvy, can you dance for me?'";
                isOpenAISessionActive = true;
                UI.updateOpenAIUIState(isOpenAISessionActive);
                console.log("OpenAI Data Channel opened");
            };
            dc.onmessage = handleOpenAIEvent;
            dc.onclose = () => {
                elements.openaiStatusMessage.innerText = "OpenAI data channel closed.";
                console.log("OpenAI Data Channel closed");
                stopSession(); // Clean up if channel closes unexpectedly
            };
            dc.onerror = (error) => {
                elements.openaiStatusMessage.innerText = `OpenAI data channel error: ${error}`;
                console.error("OpenAI Data Channel error:", error);
                stopSession(); // Clean up on error
            };

            // 6. Start the session using SDP
            const offer = await pc.createOffer({
                offerToReceiveAudio: false,
                offerToReceiveVideo: false
            });
            await pc.setLocalDescription(offer);
            elements.openaiStatusMessage.innerText = "Sending connection offer to OpenAI...";

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
            elements.openaiStatusMessage.innerText = "Livvy is ready! Start talking to control Livvy.";
            console.log("WebRTC connection established with OpenAI");

        } catch (error) {
            console.error("Error starting OpenAI session:", error);
            elements.openaiStatusMessage.innerText = `Error: ${error.message}`;
            stopSession(); // Ensure cleanup on error
            UI.updateOpenAIUIState(isOpenAISessionActive);
        }
    }

    // Stop OpenAI voice session
    function stopSession() {
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
        UI.updateOpenAIUIState(isOpenAISessionActive);
        elements.openaiStatusMessage.innerText = "Voice control disabled. Livvy is waiting.";
    }

    // Handle messages from OpenAI
    function handleOpenAIEvent(event) {
        try {
            const serverEvent = JSON.parse(event.data);
            console.log("Voice Event Received:", serverEvent);
            
            // Instead of processing locally, send to backend for processing
            socket.emit('process_openai_response', { event: serverEvent });
            
            // Update user about receiving a response
            if (serverEvent.type === "response.done") {
                elements.openaiStatusMessage.innerText = "Processing response from Livvy...";
            }
            
        } catch (error) {
            console.error("Error parsing OpenAI event:", error, "Raw data:", event.data);
            elements.openaiStatusMessage.innerText = `Error parsing OpenAI response: ${error.message}`;
        }
    }
    
    // Public API
    return {
        init
    };
})(); 