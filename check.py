import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def open_application(app_name):
    try:
        # Map common application names to their respective commands
        app_commands = {
            "microsoft edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "notepad": "notepad",
            "calculator": "calc",
            "chrome": "chrome",
            "firefox": "firefox",
            "vs code": r'C:\Users\oenge\AppData\Local\Programs\Microsoft VS Code\Code.exe',
            # Add more applications as needed
        }

        app_name_lower = app_name.lower()
        if app_name_lower in app_commands:
            command = app_commands[app_name_lower]
            subprocess.Popen([command], shell=True)
            logging.info(f"Opening {app_name}...")
            return f"Opening {app_name}..."
        else:
            logging.warning(f"Application '{app_name}' not found in the command map.")
            return f"Sorry, I don't know how to open {app_name}."

    except Exception as e:
        logging.error(f"An error occurred while trying to open {app_name}: {e}")
        return f"An error occurred while trying to open {app_name}: {e}"

# Example usage
print(open_application("vs code"))