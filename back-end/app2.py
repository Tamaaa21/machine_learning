
# app2.py
import joblib
import pandas as pd
import numpy as np
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

# ---------------- KONFIGURASI APLIKASI ----------------
app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql://username:password@localhost/stunting_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}})
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# ---------------- DATABASE MODELS ----------------
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    predictions = db.relationship('Prediction', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Prediction(db.Model):
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    child_name = db.Column(db.String(100), nullable=False)
    age_months = db.Column(db.Integer, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    algorithm = db.Column(db.String(10), nullable=False)
    prediction_code = db.Column(db.Integer, nullable=False)
    prediction_status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'child_name': self.child_name,
            'age_months': self.age_months,
            'height_cm': self.height_cm,
            'gender': self.gender,
            'algorithm': self.algorithm,
            'prediction_code': self.prediction_code,
            'prediction_status': self.prediction_status,
            'created_at': self.created_at.isoformat()
        }

# ---------------- PEMUATAN MODEL SAAT STARTUP ----------------
def load_model_artifacts():
    models = {}
    model_names = ['rf', 'svm', 'xgb']
    try:
        for name in model_names:
            filename = f'model_{name}.joblib'
            models[name] = joblib.load(filename)
            logging.info(f"Model '{name}' berhasil dimuat dari {filename}")
        
        scaler = joblib.load('scaler.joblib')
        label_encoder_jk = joblib.load('label_encoder_jk.joblib')
        logging.info("Scaler dan Label Encoder berhasil dimuat.")
        
        return models, scaler, label_encoder_jk
        
    except FileNotFoundError as e:
        logging.error(f"Error: File model tidak ditemukan - {e}")
        return None, None, None

models, scaler, label_encoder_jk = load_model_artifacts()
reverse_status_mapping = {0: 'severely stunted', 1: 'stunted', 2: 'normal', 3: 'tinggi'}

# ---------------- AUTH ENDPOINTS ----------------
@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('name', 'email', 'password')):
        logging.error("Data registrasi tidak lengkap")
        return jsonify({'error': 'Data tidak lengkap'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        logging.error(f"Email {data['email']} sudah terdaftar")
        return jsonify({'error': 'Email sudah terdaftar'}), 400
    
    user = User(
        name=data['name'],
        email=data['email'],
        role=data.get('role', 'user')
    )
    user.set_password(data['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        logging.info(f"User terdaftar: ID {user.id}, email {user.email}")
        
        return jsonify({
            'message': 'User berhasil didaftarkan',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Gagal mendaftarkan user: {str(e)}")
        return jsonify({'error': f'Gagal mendaftarkan user: {str(e)}'}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('email', 'password')):
        logging.error("Data login tidak lengkap")
        return jsonify({'error': 'Email dan password harus diisi'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        logging.info(f"Login berhasil: ID {user.id}, email {user.email}")
        
        return jsonify({
            'message': 'Login berhasil',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
    
    logging.error(f"Login gagal untuk email {data.get('email')}")
    return jsonify({'error': 'Email atau password salah'}), 401

@app.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id_str = get_jwt_identity()
    try:
        user_id = int(user_id_str)
        user = User.query.get(user_id)
        if not user:
            logging.error(f"User tidak ditemukan untuk ID {user_id_str}")
            return jsonify({'error': 'User tidak ditemukan'}), 404
        access_token = create_access_token(identity=str(user.id))
        logging.info(f"Token refreshed untuk user ID: {user_id}")
        return jsonify({'access_token': access_token}), 200
    except ValueError:
        logging.error(f"Format ID user tidak valid: {user_id_str}")
        return jsonify({'error': 'Invalid user ID format'}), 400

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    logging.info(f"User logout: ID {get_jwt_identity()}")
    return jsonify({'message': 'Logout berhasil'}), 200

@app.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id_str = get_jwt_identity()
    logging.info(f"Mengambil data user: ID {user_id_str}")
    
    try:
        user_id = int(user_id_str)
        user = User.query.get(user_id)
        
        if not user:
            logging.error(f"User tidak ditemukan: ID {user_id}")
            return jsonify({'error': 'User tidak ditemukan'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
    except ValueError:
        logging.error(f"Format ID user tidak valid: {user_id_str}")
        return jsonify({'error': 'Invalid user ID format'}), 400

# ---------------- PREDICTION ENDPOINTS ----------------
@app.route('/', methods=['GET'])
def home():
    logging.info("Akses endpoint home")
    return jsonify({
        "status": "active", 
        "message": "Selamat datang di API Klasifikasi Gizi Balita!",
        "version": "2.0.0"
    })

@app.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    if not all([models, scaler, label_encoder_jk]):
        logging.error("Model atau artefak tidak tersedia")
        return jsonify({"error": "Satu atau lebih model tidak siap, periksa log server."}), 500

    data = request.get_json()
    if not data:
        logging.error("Request body tidak valid")
        return jsonify({"error": "Request body tidak valid."}), 400

    try:
        user_id_str = get_jwt_identity()
        logging.info(f"Prediksi diminta oleh user ID: {user_id_str}")
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            logging.error(f"Format ID user tidak valid: {user_id_str}")
            return jsonify({"error": "Invalid user ID format"}), 400

        # Ambil input dari request
        child_name = data.get('child_name', '')
        algoritma_pilihan = data['algoritma']
        umur = data['umur_bulan']
        jenis_kelamin_input = data['jenis_kelamin']
        tinggi_badan = data['tinggi_badan_cm']

        # Normalisasi dan validasi jenis kelamin
        jenis_kelamin_str = jenis_kelamin_input.strip().lower()

        if jenis_kelamin_str not in label_encoder_jk.classes_:
            logging.error(f"Label jenis kelamin tidak dikenali: {jenis_kelamin_str}")
            return jsonify({
                "error": f"Label jenis kelamin '{jenis_kelamin_input}' tidak dikenali. Harus salah satu dari: {list(label_encoder_jk.classes_)}"
            }), 400

        # Validasi algoritma
        if algoritma_pilihan not in models:
            logging.error(f"Algoritma tidak valid: {algoritma_pilihan}")
            return jsonify({"error": f"Algoritma '{algoritma_pilihan}' tidak valid."}), 400

        # Proses input dan prediksi
        jenis_kelamin_encoded = label_encoder_jk.transform([jenis_kelamin_str])[0]
        input_df = pd.DataFrame([[umur, jenis_kelamin_encoded, tinggi_badan]],
                                columns=['Umur (bulan)', 'Jenis Kelamin', 'Tinggi Badan (cm)'])
        input_scaled = scaler.transform(input_df)
        selected_model = models[algoritma_pilihan]
        prediksi_kode = selected_model.predict(input_scaled)[0]
        prediksi_label = reverse_status_mapping.get(int(prediksi_kode), "Tidak Diketahui")

        # Simpan ke database
        prediction = Prediction(
            user_id=user_id,
            child_name=child_name,
            age_months=umur,
            height_cm=tinggi_badan,
            gender=jenis_kelamin_str,
            algorithm=algoritma_pilihan,
            prediction_code=int(prediksi_kode),
            prediction_status=prediksi_label
        )
        db.session.add(prediction)
        db.session.commit()

        logging.info(f"Prediksi sukses: user ID {user_id}, algoritma {algoritma_pilihan}, status {prediksi_label}")
        return jsonify({
            'prediksi_kode': int(prediksi_kode),
            'prediksi_status_gizi': prediksi_label,
            'prediction_id': str(prediction.id)
        })

    except KeyError as e:
        logging.error(f"Data tidak lengkap: {str(e)}")
        return jsonify({"error": f"Data tidak lengkap, field yang dibutuhkan tidak ada: {e}"}), 400

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saat prediksi: {str(e)}")
        return jsonify({"error": f"Terjadi kesalahan internal: {e}"}), 500

        

@app.route('/predictions', methods=['GET'])
@jwt_required()
def get_predictions():
    user_id_str = get_jwt_identity()
    logging.info(f"Mengambil riwayat prediksi untuk user ID: {user_id_str}")
    
    try:
        user_id = int(user_id_str)
        predictions = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).all()
        
        return jsonify({
            'predictions': [pred.to_dict() for pred in predictions]
        }), 200
    except ValueError:
        logging.error(f"Format ID user tidak valid: {user_id_str}")
        return jsonify({'error': 'Invalid user ID format'}), 400

@app.route('/predictions/<prediction_id>', methods=['DELETE'])
@jwt_required()
def delete_prediction(prediction_id):
    user_id_str = get_jwt_identity()
    
    try:
        user_id = int(user_id_str)
        pred_id = int(prediction_id)
        
        prediction = Prediction.query.filter_by(id=pred_id, user_id=user_id).first()
        
        if not prediction:
            logging.error(f"Prediksi tidak ditemukan: ID {pred_id}, user ID {user_id}")
            return jsonify({'error': 'Prediksi tidak ditemukan'}), 404
        
        db.session.delete(prediction)
        db.session.commit()
        logging.info(f"Prediksi dihapus: ID {pred_id}, user ID {user_id}")
        return jsonify({'message': 'Prediksi berhasil dihapus'}), 200
    except ValueError:
        logging.error(f"Format ID tidak valid: prediction_id {prediction_id}, user_id {user_id_str}")
        return jsonify({'error': 'Invalid ID format'}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Gagal menghapus prediksi: {str(e)}")
        return jsonify({'error': f'Gagal menghapus prediksi: {str(e)}'}), 500

# ---------------- DATABASE INITIALIZATION ----------------
@app.before_request
def load_model():
    if not hasattr(app, 'model_loaded'):
        app.model_loaded = True
    
    admin = User.query.filter_by(email='admin@stunting.com').first()
    if not admin:
        admin = User(
            name='Administrator',
            email='admin@stunting.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logging.info("Admin user created")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
