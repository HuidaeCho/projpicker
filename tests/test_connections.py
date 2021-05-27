import pytest
from projpicker.core.connection import ProjConnection, ProjPicker
from projpicker.core.db_operations import query_auth_code


# Test Proj DB
def proj_connection(auth_code):
    proj = ProjConnection()
    sql = f"""select name from projected_crs where code = {auth_code}"""
    query = proj.query(sql)
    if len(query) == 0:
        return None
    return proj.query(sql)[0][0]


@pytest.mark.parametrize(
        'auth_code, expected', [
            (5070, 'NAD83 / Conus Albers'),
            (4326, None),
            (2780, "NAD83(HARN) / Georgia East")
            ]
        )
def test_proj_connection(auth_code, expected):
    assert proj_connection(auth_code) == expected


# Test ProjPicker DB
@pytest.fixture
def pp_connection():
    projpicker = ProjPicker()
    sql = """select * from geombbox limit 1"""
    query = projpicker.query(sql)[0]
    if len(query) == 0:
        return 1
    return 0


def test_connection(pp_connection):
    assert pp_connection == 0

