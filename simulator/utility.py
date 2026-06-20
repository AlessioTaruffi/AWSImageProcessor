from markov_states import UserState, TRANSITIONS
from config import *
import random

'''
Questo modulo contiene funzioni di utilità per il simulatore, tra cui la scelta dello stato successivo dell'utente e la selezione casuale di immagini e operazioni da eseguire.
'''

def choose_next_state(current_state):
    transitions = TRANSITIONS[current_state]
    rand = random.random()

    cumulative = 0
    for state, probability in transitions:
        cumulative += probability
        if rand <= cumulative:
            return state

    return UserState.EXIT


def choose_image():
    r = random.random()

    if r < 0.5:
        return SMALL_IMAGE
    elif r < 0.8:
        return MEDIUM_IMAGE
    else:
        return LARGE_IMAGE

def choose_operation():
    """
    resize -> 40%
    grayscale -> 30%
    rotate -> 20%
    blur -> 10%
    """

    r = random.random()

    if r < 0.4:
        return {
            "op": "resize",
            "width": random.choice([512, 1024, 2048])
        }

    elif r < 0.7:
        return {
            "op": "grayscale"
        }

    elif r < 0.9:
        return {
            "op": "rotate",
            "angle": random.choice([90, 180, 270])
        }

    else:
        return {
            "op": "blur",
            "radius": random.choice([2, 5, 8])
        }
