# Search.py
"""
Conditional search for Tudo: turns keyword conditions into a
parameterised PostgreSQL query. Pure Python, no DB connection needed,
so it can be tested on its own.

Conditions use  column__operator=value  (operator defaults to "eq"):

    durationSec__gt=2
    flatnessMedian__between=(0.1, 0.5)
    mainPitchHz__lte=200
    transposability__in=[0, 1]
    pitchFluctRate__isnull=False

Tag conditions work on the `identifiers` JSON column:

    tags=["bassoon", "multiphonic"]   # must have ALL of these
    anyTags=["buzz", "rumbling"]      # must have AT LEAST ONE
    noTags=["noise"]                  # must have NONE of these

Other options:

    pathContains="BASSOON"            # case-insensitive substring of path
    orderBy="-centroidMostCommon"     # "-" = descending; str or list
    limit=20, offset=0
    columns=["path", "roughness"]     # default: all columns
    random=True                       # random order (ignores orderBy)
"""

OPERATORS = {
    "eq": "=",
    "ne": "<>",
    "gt": ">",
    "gte": ">=",
    "lt": "<",
    "lte": "<=",
}

SPECIAL_KEYS = {
    "tags", "anyTags", "noTags", "pathContains",
    "orderBy", "limit", "offset", "columns", "random",
}


class SearchError(ValueError):
    pass


def _column(name, validColumns):
    """Postgres folds unquoted names to lowercase, so durationSec == durationsec."""
    col = name.lower()
    if validColumns is not None and col not in validColumns:
        raise SearchError(
            f"Tudo.search: unknown column '{name}'. "
            f"Available: {', '.join(sorted(validColumns))}")
    return col


def _asList(x):
    if isinstance(x, str):
        return [x]
    return list(x)


def buildSearchQuery(table="soundfile_analysis", validColumns=None, **conditions):
    """Returns (sql, params) ready for cursor.execute(sql, params)."""
    if validColumns is not None:
        validColumns = {c.lower() for c in validColumns}

    where, params = [], []

    for key, value in conditions.items():
        if key in SPECIAL_KEYS:
            continue
        if "__" in key:
            name, op = key.rsplit("__", 1)
        else:
            name, op = key, "eq"
        col = _column(name, validColumns)

        if op in OPERATORS:
            if value is None:
                raise SearchError(f"Tudo.search: use {name}__isnull=True instead of None")
            where.append(f"{col} {OPERATORS[op]} %s")
            params.append(value)
        elif op == "between":
            lo, hi = value
            where.append(f"{col} BETWEEN %s AND %s")
            params += [lo, hi]
        elif op == "in":
            where.append(f"{col} = ANY(%s)")
            params.append(list(value))
        elif op == "isnull":
            where.append(f"{col} IS {'' if value else 'NOT '}NULL")
        else:
            raise SearchError(
                f"Tudo.search: unknown operator '{op}' in '{key}'. "
                f"Use one of: {', '.join(list(OPERATORS) + ['between', 'in', 'isnull'])}")

    # tags on the identifiers JSON column (cast to jsonb for ?& ?| operators)
    if conditions.get("tags"):
        where.append("identifiers::jsonb ?& %s")
        params.append(_asList(conditions["tags"]))
    if conditions.get("anyTags"):
        where.append("identifiers::jsonb ?| %s")
        params.append(_asList(conditions["anyTags"]))
    if conditions.get("noTags"):
        where.append("NOT (COALESCE(identifiers::jsonb, '[]'::jsonb) ?| %s)")
        params.append(_asList(conditions["noTags"]))

    if conditions.get("pathContains"):
        where.append("path ILIKE %s")
        params.append(f"%{conditions['pathContains']}%")

    cols = conditions.get("columns")
    select = ", ".join(_column(c, validColumns) for c in _asList(cols)) if cols else "*"

    sql = f"SELECT {select} FROM {table}"
    if where:
        sql += " WHERE " + " AND ".join(where)

    if conditions.get("random"):
        sql += " ORDER BY random()"
    elif conditions.get("orderBy"):
        parts = []
        for o in _asList(conditions["orderBy"]):
            desc = o.startswith("-")
            parts.append(f"{_column(o.lstrip('-'), validColumns)} {'DESC' if desc else 'ASC'}")
        sql += " ORDER BY " + ", ".join(parts)

    if conditions.get("limit") is not None:
        sql += " LIMIT %s"
        params.append(int(conditions["limit"]))
    if conditions.get("offset"):
        sql += " OFFSET %s"
        params.append(int(conditions["offset"]))

    return sql, params
