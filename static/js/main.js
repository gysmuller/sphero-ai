document.addEventListener('DOMContentLoaded', function() {
    // Initialize modules
    const socket = io();
    const uiElements = UI.getElements();
    
    // Initialize modules with dependencies
    const socketHandler = SocketHandler.init(socket, uiElements);
    const joystickController = JoystickController.init(socket, uiElements);
    const openAIController = OpenAIController.init(socket, uiElements);
    
    // Initialize UI last as it depends on other modules
    UI.init(socket, socketHandler, joystickController, openAIController, uiElements);
}); 