from program_control import ProgramController
from main_gui import MainGUI

def main():
    program_controller = ProgramController()
    program_controller.start_main_gui(MainGUI, program_controller)

if __name__ == "__main__":
    main()