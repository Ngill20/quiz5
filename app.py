from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from datetime import datetime
import pyodbc
from dotenv import load_dotenv
import os
import math
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = 'supersecret'  # for flash messages

load_dotenv()
password = os.getenv("SQL_PASSWORD")

server = 'quiz5server.database.windows.net'
database = 'quiz5db' 
username = 'quiz5us'
driver = '{ODBC Driver 18 for SQL Server}'

def get_connection():
    return pyodbc.connect(
        f'DRIVER={driver};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password};'
        f'Encrypt=yes;'
        f'TrustServerCertificate=no;'
        f'Connection Timeout=30;'
    )

@app.route('/')
def index():
    print("Rendering index.html")  # Make sure this prints in your terminal
    return render_template('index.html')
    #return "<h1>Test page</h1>"

@app.route('/insert', methods=['GET', 'POST'])
def insert():
    if request.method == 'POST':
        # Extract values from form (for simplified CSV structure)
        quake_id = request.form.get('id')
        time = safe_int(request.form.get('time'))  # Assuming time is an integer like in the CSV
        latitude = safe_float(request.form.get('lat'))
        longitude = safe_float(request.form.get('long'))
        mag = safe_float(request.form.get('mag'))
        nst = safe_int(request.form.get('nst'))
        net = request.form.get('net')

        # Insert into Earthquakes table
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Earthquakes (
                    id, time, latitude, longitude, mag, nst, net
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, quake_id, time, latitude, longitude, mag, nst, net)
            conn.commit()
            flash('Earthquake record inserted successfully!')
        except Exception as e:
            flash(f'Insert failed: {e}')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('index'))

    return render_template('insert.html')


@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        min_mag = request.form.get('Mlow', 0)
        max_mag = request.form.get('Mhigh', 10)
        conn = get_connection()
        query = """
            SELECT id, time, latitude, longitude, mag, nst, net
            FROM Earthquakes
            WHERE mag BETWEEN ? AND ?
            ORDER BY time DESC
        """
        df = pd.read_sql(query, conn, params=[min_mag, max_mag])
        conn.close()

        # Remove leading/trailing \n and whitespace in the HTML
        html_table = df.to_html(classes='table table-striped', index=False).replace('\n', '')

        return render_template('results.html', tables=[html_table], titles=df.columns.values)
    return render_template('query.html')

@app.route('/bar_chart')
def bar_chart():
    conn = get_connection()
    cursor = conn.cursor()

    # Create bins and count earthquakes in each
    query = """
        SELECT 
            CASE 
                WHEN mag >= 1 AND mag < 2 THEN '1-2'
                WHEN mag >= 2 AND mag < 3 THEN '2-3'
                WHEN mag >= 3 AND mag < 4 THEN '3-4'
                WHEN mag >= 4 AND mag < 5 THEN '4-5'
                WHEN mag >= 5 AND mag < 6 THEN '5-6'
                WHEN mag >= 6 AND mag < 7 THEN '6-7'
                WHEN mag >= 7 AND mag < 8 THEN '7-8'
                WHEN mag >= 8 AND mag < 9 THEN '8-9'
                WHEN mag >= 9 AND mag <= 10 THEN '9-10'
                ELSE 'Other'
            END AS magnitude_range,
            COUNT(*) AS count
        FROM Earthquakes
        GROUP BY 
            CASE 
                WHEN mag >= 1 AND mag < 2 THEN '1-2'
                WHEN mag >= 2 AND mag < 3 THEN '2-3'
                WHEN mag >= 3 AND mag < 4 THEN '3-4'
                WHEN mag >= 4 AND mag < 5 THEN '4-5'
                WHEN mag >= 5 AND mag < 6 THEN '5-6'
                WHEN mag >= 6 AND mag < 7 THEN '6-7'
                WHEN mag >= 7 AND mag < 8 THEN '7-8'
                WHEN mag >= 8 AND mag < 9 THEN '8-9'
                WHEN mag >= 9 AND mag <= 10 THEN '9-10'
                ELSE 'Other'
            END
        ORDER BY magnitude_range
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    # Prepare data for JSON
    chart_data = [{"range": row[0], "count": row[1]} for row in results if row[0] != 'Other']
    return render_template("bar_chart.html", chart_data=chart_data)

@app.route('/pie_chart')
def pie_chart():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            CASE 
                WHEN mag >= 0 AND mag < 1 THEN '0-1'
                WHEN mag >= 1 AND mag < 2 THEN '1-2'
                WHEN mag >= 2 AND mag < 3 THEN '2-3'
                WHEN mag >= 3 AND mag < 4 THEN '3-4'
                WHEN mag >= 4 AND mag < 5 THEN '4-5'
                WHEN mag >= 5 AND mag < 6 THEN '5-6'
                WHEN mag >= 6 AND mag < 7 THEN '6-7'
                WHEN mag >= 7 AND mag < 8 THEN '7-8'
                WHEN mag >= 8 AND mag < 9 THEN '8-9'
                WHEN mag >= 9 AND mag <= 10 THEN '9-10'
                ELSE 'Other'
            END AS magnitude_range,
            COUNT(*) AS count
        FROM Earthquakes
        GROUP BY 
            CASE 
                WHEN mag >= 0 AND mag < 1 THEN '0-1'
                WHEN mag >= 1 AND mag < 2 THEN '1-2'
                WHEN mag >= 2 AND mag < 3 THEN '2-3'
                WHEN mag >= 3 AND mag < 4 THEN '3-4'
                WHEN mag >= 4 AND mag < 5 THEN '4-5'
                WHEN mag >= 5 AND mag < 6 THEN '5-6'
                WHEN mag >= 6 AND mag < 7 THEN '6-7'
                WHEN mag >= 7 AND mag < 8 THEN '7-8'
                WHEN mag >= 8 AND mag < 9 THEN '8-9'
                WHEN mag >= 9 AND mag <= 10 THEN '9-10'
                ELSE 'Other'
            END
        ORDER BY magnitude_range
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    chart_data = [{"range": row[0], "count": row[1]} for row in results if row[0] != 'Other']
    return render_template("pie_chart.html", chart_data=chart_data)



@app.route('/scatter_plot')
def scatter_plot():
    conn = get_connection()
    cursor = conn.cursor()

    # Query all earthquakes with lat/long/mag/id
    cursor.execute("""
        SELECT latitude, longitude, mag, id
        FROM Earthquakes
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    #  lat, long, mag
    data = [{"lat": row[0], "long": row[1], "mag": row[2], "id": row[3]} for row in results]
    return render_template("scatter_plot.html", scatter_data=data)




@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            file_path = os.path.join('static', 'uploads', file.filename)
            file.save(file_path)

            # Read CSV with expected columns
            df_cleaned = pd.read_csv(file_path, skip_blank_lines=True)

            conn = get_connection()
            cursor = conn.cursor()
            for index, row in df_cleaned.iterrows():
                try:
                    raw_time = safe_float(row['time'])  # allow decimal minutes/seconds
                    if raw_time is not None:
                        time_new = datetime(1970, 1, 1) + timedelta(minutes=raw_time)  # or timedelta(seconds=raw_time)
                    else:
                        time_new = None
                    time      = safe_int(row['time'])
                    latitude  = safe_float(row['lat'])
                    longitude = safe_float(row['long'])
                    mag       = safe_float(row['mag'])
                    nst       = safe_int(row['nst'])
                    net       = str(row['net']) if pd.notna(row['net']) else None
                    id_       = str(row['id'])
                    
                    print(f"Row {index}: time={time}, lat={latitude}, mag={mag}, id={id_}")
                    cursor.execute("""
                        INSERT INTO Earthquakes (
                            time, latitude, longitude, mag, nst, net, id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, time, latitude, longitude, mag, nst, net, id_)

                except Exception as e:
                    print(f"Failed to insert row {index}: {e}")
                    print(df_cleaned.iloc[index])

            conn.commit()
            cursor.close()
            conn.close()
            flash('CSV data uploaded successfully!')
            return redirect(url_for('index'))
        else:
            flash('Please upload a valid CSV file.')
            return redirect(url_for('upload'))
    return render_template('upload.html')


def safe_float(val):
    try:
        val = str(val).strip()
        if val.lower() in ["", "nan", "null", "none"]:
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    try:
        val = str(val).strip()
        if val.lower() in ["", "nan", "null", "none"]:
            return None
        return int(float(val))  # int("3.0") fails, but int(float("3.0")) works
    except (ValueError, TypeError):
        return None

def safe_datetime(val):
    try:
        return pd.to_datetime(val)
    except Exception:
        return None
    
if __name__ == '__main__':
    os.makedirs(os.path.join('static', 'uploads'), exist_ok=True)
    app.run(debug=True)