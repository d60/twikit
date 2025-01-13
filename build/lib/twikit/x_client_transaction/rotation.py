import math
from typing import Union


def convert_rotation_to_matrix(rotation: Union[float, int]):
    rad = math.radians(rotation)
    return [math.cos(rad), -math.sin(rad), math.sin(rad), math.cos(rad)]


def convertRotationToMatrix(degrees: Union[float, int]):
    # first convert degrees to radians
    radians = degrees * math.pi / 180
    # now we do this:
    """
    [cos(r), -sin(r), 0]
    [sin(r), cos(r), 0]

    in this order:
    [cos(r), sin(r), -sin(r), cos(r), 0, 0]
    """
    cos = math.cos(radians)
    sin = math.sin(radians)
    return [cos, sin, -sin, cos, 0, 0]


if __name__ == "__main__":
    pass
