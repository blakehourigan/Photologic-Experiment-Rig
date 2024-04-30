from program_control import ProgramController

def start_program():
    program_control = ProgramController(restart_callback=restart_program)
    program_control.start_main_gui()

def restart_program():
    print("Restarting the program...")
    start_program()

def main():
    start_program()
    
if __name__ == "__main__":
    main()  