"""
This module is the 'launcher' module for the program. Every other module in the program originates from this
location.

If the user requests a 'reset' from the Main GUI, the program controlling 'StateMachine' module destroys itself,
then, this module handles the launcing of a new instance of the program. This is made possible through the mutable `result_container`
object which we can pass to other modules for them to modify, then read the result later.
"""

from app_logic import StateMachine


def main():
    while 1:
        # we pass in a list with one element, because lists in python are mutable items. so we can pass this
        # into the StateMachine, modify the object and view the result when we are done with this instance

        result_container = [0]
        """init result container as mutable list with initial value of 0 (do not restart)"""

        StateMachine(result_container)
        """
        Startup a StateMachine instance to handle experiment logic.
        """

        """ Match on the result to determine whether or not to restart program upon StateMachine return."""
        match result_container[0]:
            case 0:
                break
            case 1:
                continue


if __name__ == "__main__":
    main()
