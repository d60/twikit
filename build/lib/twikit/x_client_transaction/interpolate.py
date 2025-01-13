from typing import Union, List


def interpolate(from_list: List[Union[float, int]], to_list: List[Union[float, int]], f: Union[float, int]):
    if len(from_list) != len(to_list):
        raise Exception(
            f"Mismatched interpolation arguments {from_list}: {to_list}")
    out = []
    for i in range(len(from_list)):
        out.append(interpolate_num(from_list[i], to_list[i], f))
    return out


def interpolate_num(from_val: List[Union[float, int]], to_val: List[Union[float, int]], f: Union[float, int]):
    if all([isinstance(number, (int, float)) for number in [from_val, to_val]]):
        return from_val * (1 - f) + to_val * f

    if all([isinstance(number, bool) for number in [from_val, to_val]]):
        return from_val if f < 0.5 else to_val


if __name__ == "__main__":
    pass
