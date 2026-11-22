def find_user(cursor, username: str):
    query = "SELECT * FROM users WHERE name = '%s'" % username
    return cursor.execute(query)
