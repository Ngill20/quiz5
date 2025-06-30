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

fvdata = pd.DataFrame([
    [10, "Apples", "F"],
    [2, "Bananas", "F"],
    [40, "Cherries", "F"],
    [1, "Daikon", "V"],
    [10, "Fig", "F"],
    [30, "Grapes", "F"],
    [5, "Peach", "F"],
    [12, "Celery", "V"],
    [1, "Watermelon", "F"]
], columns=["Amount", "Food", "Category"])
fvdata["Amount"] = fvdata["Amount"].astype(int)

@app.route('/')
def index():
    print("Rendering index.html")  # Make sure this prints in your terminal
    return render_template('index.html')
    #return "<h1>Test page</h1>"


@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        try:
            min_amt = safe_int(request.form.get('min_amt'))
            max_amt = safe_int(request.form.get('max_amt'))
            if min_amt is None or max_amt is None:
                flash("Please provide valid amount values.")
                return redirect(url_for('query'))

            total = 0
            # Filter fvdata
            filtered = []
            for _, row in fvdata.iterrows():
                if int(row["Amount"]) > min_amt and int(row["Amount"]) < max_amt:
                    total = total + row["Amount"]
                    filtered.append(row)

            chart_data = [
                {
                    "food": row["Food"],
                    "amount": row["Amount"],
                    "percent": round((row["Amount"] / total) * 100, 1)
                }
                for row in filtered
            ]
            
            print(chart_data)
            return render_template("fv_pie.html", chart_data=chart_data)

        except Exception as e:
            flash(f"Error: {e}")
            return redirect(url_for('query'))

    return render_template('query_form.html')  # create form with min_amt and max_amt fields


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



@app.route('/query_bar', methods=['GET', 'POST'])
def query_bar():
    if request.method == 'POST':
        try:
            min_amt = safe_int(request.form.get('min_amt'))
            max_amt = safe_int(request.form.get('max_amt'))

            if min_amt is None or max_amt is None:
                flash("Please provide valid amount values.")
                return redirect(url_for('query_bar'))

            # Filter and sort (smallest to largest)
            filtered_df = fvdata[(fvdata["Amount"] >= min_amt) & (fvdata["Amount"] <= max_amt)]
            filtered_df = filtered_df.sort_values("Amount", ascending=True)

            chart_data = filtered_df.to_dict(orient='records')
            return render_template("fv_bar.html", chart_data=chart_data)

        except Exception as e:
            flash(f"Error: {e}")
            return redirect(url_for('query_bar'))

    return render_template('query_form_bar.html')


@app.route('/query_scatter', methods=['GET', 'POST'])
def query_scatter():
    if request.method == 'POST':
        points = []
        for i in range(10):
            x = safe_int(request.form.get(f'x{i}'))
            y = safe_int(request.form.get(f'y{i}'))
            c = safe_int(request.form.get(f'c{i}'))
            if x is not None and y is not None and c in [1, 2, 3]:
                points.append({'x': x, 'y': y, 'c': c})

        if not points:
            flash("Please enter at least one valid point with x, y between 0–50 and c = 1, 2, or 3.")
            return redirect(url_for('query_scatter'))

        return render_template('scatter_user_plot.html', points=points)

    return render_template('query_scatter_form.html')



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