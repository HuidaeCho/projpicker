import re

def _replace_closure(input: str) -> str:

    if any(x in input for x in ['(', ')']):
        input = input.replace('(', '').replace(')', '')
    if any(x in input for x in ['[', ']']):
        input = input.replace('[', '').replace(']', '')


def POLYGON(input: (tuple, list)) -> str:
    if input[0] != input[-1]:
        raise Exception("Polygon geometry does not close!")

    geom_str = re.sub(',([^,]*,?)', r'\1', str(input))

    geom_str = _replace_closure(geom_str)

    return f'POLYGON(({geom_str}))'


def POINT(input: (tuple, list)) -> str:

    geom_str = str(input).replace(',', ' ')

    geom_str = _replace_closure(geom_str)

    return f'POINT(({geom_str}))'

