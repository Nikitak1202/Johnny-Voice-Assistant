from CommandManager import CommandManager

# Main function block: initialize CommandManager and start the loop.
def main():
    # Initialize the CommandManager instance.
    cmd_manager = CommandManager()
    
    # Infinite loop block: wait for the wake word and process the command.
    while True:
        print("Waiting for wake word...")
        # Wait for the wake word; if detected, process the command.
        if cmd_manager.Start_Word_Detection():
            print("Wake word detected. Processing command...")
            response = cmd_manager.Create_Answer()
            print("Response:", response)
            cmd_manager.Speak(response)

# Entry point block: start the main function.
if __name__ == "__main__":
    main()