from app_logic import StateMachine


def main():
    while 1:
        # we pass in a list with one element, because lists in python are mutable items. so we can pass this
        # into the StateMachine, modify the object and view the result when we are done with this instance

        result_container = [0]
        StateMachine(result_container)
        """ 
        match the result that comes back from the 
        StateMachine instance. if the value was flipped to a 1
        then we want to reset the entire application to the prior state
        """
        match result_container[0]:
            case 0:
                break
            case 1:
                continue


if __name__ == "__main__":
    main()
