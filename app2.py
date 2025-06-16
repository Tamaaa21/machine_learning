from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import json
import os

app = Flask(__name__)

# Load model dan preprocessing
pipeline = joblib.load('model/random.pkl')
label_encoder_jk = joblib.load('model/label_encoder_jk.pkl')

with open('status_mapping.json') as f:
    status_mapping = json.load(f)
    inverse_mapping = {v: k for k, v in status_mapping.items()}

@app.route('/')
def home():
    return render_template('index2.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        # Validasi input
        if not all(key in data for key in ['umur', 'jenis_kelamin', 'tinggi_badan']):
            return jsonify({'status': 'error', 'message': 'Input tidak lengkap'}), 400
        
        # Konversi jenis kelamin ke numerik
        gender_encoded = 1 if data['jenis_kelamin'].lower() == 'laki-laki' else 0
        
        # Buat array input
        input_data = np.array([
            float(data['umur']),
            gender_encoded,
            float(data['tinggi_badan'])
        ]).reshape(1, -1)
        
        # Prediksi
        prediction = pipeline.predict(input_data)
        result = inverse_mapping[int(prediction[0])]
        
        return jsonify({
            'status': 'success',
            'prediction': result,
            'confidence': 'high'  # Bisa diganti dengan probabilitas jika diperlukan
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)