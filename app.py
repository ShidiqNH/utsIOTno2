from flask import Flask, jsonify, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',      
    'user': 'root',          
    'password': '',           
    'database': 'db_iot_ee'   
}

def connect_db():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error database connection : ", e)
    return None

def query_data():
    connection = connect_db()
    if not connection:
        return {"error": "Failed to connect to the database"}

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT MAX(suhu) AS suhu_max, MIN(suhu) AS suhu_min, AVG(suhu) AS suhu_rata FROM tb_cuaca")
        suhuStats = cursor.fetchone()
        result = {
            "suhumax": int(suhuStats['suhu_max']),
            "suhumin": int(suhuStats['suhu_min']),
            "suhurata": round(suhuStats['suhu_rata'], 2)
        }

        cursor.execute("""
            SELECT id AS idx, suhu, humid, lux AS kecerahan, ts AS timestamp
            FROM tb_cuaca
            WHERE suhu = (SELECT MAX(suhu) FROM tb_cuaca)
              AND humid = (SELECT MAX(humid) FROM tb_cuaca)
        """)
        maxRecords = cursor.fetchall()
        
        for record in maxRecords:
            record['idx'] = int(record['idx'])
            record['suhu'] = int(record['suhu'])
            record['humid'] = int(record['humid'])
            record['kecerahan'] = int(record['kecerahan'])
            record['timestamp'] = record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    
        result["nilai_suhu_max_humid_max"] = maxRecords

        cursor.execute("""
            SELECT DISTINCT DATE_FORMAT(ts, '%m-%Y') AS month_year
            FROM tb_cuaca
            WHERE suhu = (SELECT MAX(suhu) FROM tb_cuaca)
              AND humid = (SELECT MAX(humid) FROM tb_cuaca)
        """)
        result["month_year_max"] = [{"month_year": row["month_year"]} for row in cursor.fetchall()]

        return result

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    data = query_data()
    return jsonify(data)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
