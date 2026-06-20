from enum import Enum

'''
Questo modulo definisce gli stati dell'utente e le transizioni tra di essi per il simulatore.
'''

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