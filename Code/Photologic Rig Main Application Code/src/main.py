from app import StateMachine


def main():
    while 1:
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
