import sqlite3

def get_user(user_id: str):
    # Vulnerability 1: SQL query built via string concatenation (SQL injection)
    db = sqlite3.connect("database.db")
    cursor = db.cursor()
    query = "SELECT * FROM users WHERE username = '" + user_id + "'"
    cursor.execute(query)
    return cursor.fetchall()

def execute_user_calculation(expression: str):
    # Vulnerability 2: eval() on untrusted user input (Arbitrary code execution)
    result = eval(expression)
    return result

def test_login_fixture():
    # Fake hardcoded credential inside a test fixture
    test_user_password = "SuperSecretPassword123!"
    return {"user": "admin", "token": test_user_password}
