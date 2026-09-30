# Models & Data Helper Converters

def dict_from_row(row):
    if row is None:
        return None
    return dict(row)

def dicts_from_rows(rows):
    return [dict(row) for row in rows]
