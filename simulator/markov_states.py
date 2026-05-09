from enum import Enum

class UserState(Enum):
    START = 1
    UPLOAD = 2
    RESIZE = 3
    GRAYSCALE = 4
    ROTATE = 5
    BLUR = 6
    EXIT = 7


TRANSITIONS = {
    UserState.START: [
        (UserState.UPLOAD, 1.0)
    ],

    UserState.UPLOAD: [
        (UserState.RESIZE, 0.40),
        (UserState.GRAYSCALE, 0.30),
        (UserState.ROTATE, 0.20),
        (UserState.BLUR, 0.10)
    ],

    UserState.RESIZE: [
        (UserState.EXIT, 1.0)
    ],

    UserState.GRAYSCALE: [
        (UserState.EXIT, 1.0)
    ],

    UserState.ROTATE: [
        (UserState.EXIT, 1.0)
    ],

    UserState.BLUR: [
        (UserState.EXIT, 1.0)
    ]
}
