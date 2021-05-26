def query_auth_code(pp_con: object, id):

    sql = f"""
           SELECT auth_code FROM codes WHERE id = {id}
           """
    return pp_con.query(sql)[0][0]


def query_id(pp_con: object, auth_code):
    sql = f"""
           SELECT id FROM codes WHERE auth_code = {auth_code}
           """
    return pp_con.query(sql)[0][0]


def authority_codes(proj_db: object, auth="EPSG", table="projected_crs") -> list:
    """
    Get list of authority_codes
    """
    sql = f"SELECT code, deprecated FROM {table} WHERE auth_name = '{auth}'"
    return [str(code[0]) for code in proj_db.query(sql) if code[1] == 0]


def usage_codes(proj_db: object, auth_code) -> dict:
    """
    Get extent and scope keys from usage table
    """

    sql = f"""SELECT extent_code, scope_code FROM usage
              WHERE object_code = {auth_code}"""

    codes = proj_db.query(sql)[0]
    codes_dict = {"extent_code": codes[0], "scope_code": codes[1]}

    return codes_dict


def usage_index(proj_db: object, auth_codes) -> dict:
    """
    Create full dictionary of CRS codes and their respective usage codes.
    """
    codex = {}
    for code in auth_codes:
        codex[code] = usage_codes(proj_db, code)
    return codex


def get_scope(proj_db: object, code: dict, auth="EPSG") -> list:
    """
    Retrieve scope from CRS code usage index
    """
    scope_code = code["scope_code"]
    sql = f"""SELECT scope FROM scope
              WHERE code = {scope_code}"""
    return list(proj_db.query(sql)[0])


def get_extent(proj_db: object, code: dict, auth="EPSG") -> dict:
    """
    Retrieve extent from CRS code usage index
    """
    extent_code = code["extent_code"]
    sql = f"""SELECT name, description FROM extent
              WHERE code = {extent_code}"""
    area = proj_db.query(sql)[0]
    extent = {"name": area[0], "description": area[1]}

    sql = f"""SELECT south_lat, west_lon, north_lat, east_lon FROM extent
              WHERE auth_name = '{auth}'
              AND code = {extent_code}"""
    bbox = list(proj_db.query(sql)[0])
    bbox_round = list(map(lambda x: round(x, ndigits=2), bbox))
    extent['bbox'] = bbox_round
    return extent


def pop_usage_index(proj_db: object, code: dict, auth="EPSG") -> dict:
    """
    Populate individual usage entry
    """
    scope = get_scope(proj_db, code, auth)
    extent = get_extent(proj_db, code, auth)
    return {"scope": scope, "area": extent}


def get_usage_dict(proj_db, code_idx) -> dict:
    """
    Generate full populated usage dictionary for list of CRS.
    """
    usage = {}
    for code in code_idx:
        usage[code] = pop_usage_index(proj_db, code_idx[str(code)])

    return usage


def crs_usage(proj_db: object, auth="EPSG", table="projected_crs") -> dict:
    """
    Generate a full usage dictionary for a specified CRS.
    """
    auth_codes = authority_codes(proj_db, auth, table)
    usage_idx = usage_index(proj_db, auth_codes)
    usage_dict = get_usage_dict(proj_db, usage_idx)

    return usage_dict

