from simulator.markov_states import UserState, TRANSITIONS
from simulator.config import *
import random

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
    """
    Distribuzione immagini:
    50% piccole
    30% medie
    20% grandi
    """

    r = random.random()

    if r < 0.5:
        return SMALL_IMAGE
    elif r < 0.8:
        return MEDIUM_IMAGE
    else:
        return LARGE_IMAGE