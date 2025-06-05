import asyncio


# --- Main Program ---
if __name__ == "__main__":
    print("Voice AI Chatbot Ready!")
    #disp = init_display()

    command = recognize_speech()
    if command:
        response = process_command(command)
        print("Response:", response)
        asyncio.run(speak(response))