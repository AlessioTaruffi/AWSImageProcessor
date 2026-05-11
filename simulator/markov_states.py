from enum import Enum

class UserState(Enum):
    START = 1
    PROCESS_IMAGE = 2
    EXIT = 3


TRANSITIONS = {
    UserState.START: [
        (UserState.PROCESS_IMAGE, 1.0)
    ],

    UserState.PROCESS_IMAGE: [
        (UserState.EXIT, 1.0)
    ]
}