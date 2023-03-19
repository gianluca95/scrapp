from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def Index():
    return render_template('index.html')

@app.route('/scan_receipt/')
def Scan():
    return render_template('scan.html')

if __name__ == '__main__':
    port = os.environ.get("PORT", 8000)
    app.run(debug = False, host = "0.0.0.0", port = port)