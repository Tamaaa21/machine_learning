from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load('model_rf.pkl')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        tinggi = float(request.form['tinggi'])
        berat = float(request.form['berat'])
        usia = int(request.form['usia'])
        jenkel = 0 if request.form['jenkel'] == 'Pria' else 1
        
        # Prediksi
        input_data = np.array([[tinggi, berat, usia, jenkel]])
        kategori = model.predict(input_data)[0]
        
        return render_template('index.html', 
                            hasil_prediksi=kategori,
                            tinggi=tinggi,
                            berat=berat,
                            usia=usia,
                            jenkel=request.form['jenkel'])
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)