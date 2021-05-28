import pytest
from projpicker.core.db_operations import (authority_codes,
                                           usage_codes,
                                           crs_usage
                                           )
from projpicker.core.connection import ProjConnection, ProjPicker

pp_con = ProjPicker()
proj_con = ProjConnection()


# Test authority code query
def get_authority_codes(auth_code, table):
    codes = authority_codes(proj_con, table=table)
    if auth_code in codes:
        return 0
    return 1


@pytest.mark.parametrize(
        'auth_code, table, expected', [
            ('5070', 'projected_crs', 0),
            ('4326', 'geodetic_crs', 0),
            ('3900', 'vertical_crs', 0),
            ('8729', 'compound_crs', 0)
            ]
        )
def test_auth_codes(auth_code, table, expected):
    assert get_authority_codes(auth_code, table) == expected


# Test usage code query
def get_usage_code(auth_code):
    return usage_codes(proj_con, auth_code)


@pytest.mark.parametrize(
        'auth_code, expected', [
            ('5070', {'extent_code': '1323', 'scope_code': '1109'}),
            ('4326', {'extent_code': '1262', 'scope_code': '1183'}),
            ('3900', {'extent_code': '3333', 'scope_code': '1179'}),
            ('8729', {'extent_code': '2190', 'scope_code': '1142'})
            ]
        )
def test_usage_codes(auth_code, expected):
    assert get_usage_code(auth_code) == expected


def get_crs_usage(code, table):
    crs_usage_dict = crs_usage(proj_con, table=table)
    print(crs_usage_dict[code])
    return crs_usage_dict[code]['scope'][0]


@pytest.mark.parametrize(
        'auth_code, table, expected', [
            ('5070',
             'projected_crs',
             'Data analysis and small scale data presentation for contiguous lower 48 states.'),
            ('4326',
             'geodetic_crs',
             'Horizontal component of 3D system.'),
            ('3900',
             'vertical_crs',
             'Geodesy, engineering survey.'),
            ('8729',
             'compound_crs',
             'Engineering survey, topographic mapping.')
            ]
        )
def test_scope(auth_code, table, expected):
    assert get_crs_usage(auth_code, table) == expected

