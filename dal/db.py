import os

import pyodbc


def get_connection():
    connection = pyodbc.connect(os.environ['DB_CONNECTION_STRING'])
    connection.autocommit = True
    return connection
