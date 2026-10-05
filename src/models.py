from enum import Enum

class ParkingAreaType(Enum):
    ON_STREET = 0
    OFF_STREET = 1

class VehicleState(Enum):
    IGNORE = 0
    INCOMING = 1
    ROUTING = 2
    CRUISING_TO_TARGET = 3
    CRUISING_FOR_PARKING = 4
    PARKING_MANEUVER = 5
    PARKING = 6

class TimeStamps(Enum):
    START_OF_TRAVEL = 0
    START_OF_CRUISING = 1
    END_OF_CRUISING = 2
    PARK_IN_DONE = 3