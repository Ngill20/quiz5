import pandas as pd
import pyodbc
from dotenv import load_dotenv
import os

# Load .env file variables
load_dotenv()
password = os.getenv('SQL_PASSWORD')

server = 'quiz5server.database.windows.net'
database = 'quiz5db' 
username = 'quiz5us'
driver = '{ODBC Driver 18 for SQL Server}'

# Connect to Azure SQL
try:
    conn = pyodbc.connect(
        f'DRIVER={driver};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'  # Use the secure password from environment
        f'Encrypt=yes;'
        f'TrustServerCertificate=no;'
        f'Connection Timeout=30;'
    )
    print("Connected to Azure SQL Database!")
except Exception as e:
    print("Error connecting to database:", e)
    exit(1)

