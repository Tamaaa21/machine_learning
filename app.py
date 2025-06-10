from flask import Flask, render_template, request
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load('model_rf.pkl')

# Add template filters
@app.template_filter('getColorClass')
def get_color_class(prediction):
    prediction = prediction.lower()
    if 'underweight' in prediction:
        return 'bg-blue-500'
    elif 'normal' in prediction:
        return 'bg-green-500'
    elif 'overweight' in prediction:
        return 'bg-yellow-500'
    elif 'obese' in prediction:
        return 'bg-red-500'
    return 'bg-gray-500'

@app.template_filter('getIconClass')
def get_icon_class(prediction):
    prediction = prediction.lower()
    if 'underweight' in prediction:
        return 'fas fa-exclamation-circle'
    elif 'normal' in prediction:
        return 'fas fa-check-circle'
    elif 'overweight' in prediction:
        return 'fas fa-exclamation-triangle'
    elif 'obese' in prediction:
        return 'fas fa-times-circle'
    return 'fas fa-question-circle'

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        tinggi = float(request.form['tinggi']) / 100  # Convert cm to m
        berat = float(request.form['berat'])
        usia = int(request.form['usia'])
        jenkel = 0 if request.form['jenkel'] == 'Pria' else 1
        nama = request.form.get('nama', '')
        
        bmi = berat / (tinggi ** 2)
        input_data = np.array([[tinggi * 100, berat, usia, jenkel]])
        kategori = model.predict(input_data)[0]
        saran_kesehatan = get_health_advice(kategori)

        return render_template('index.html', 
                             hasil_prediksi=kategori,
                             bmi=round(bmi, 1),
                             tinggi=tinggi * 100,
                             berat=berat,
                             usia=usia,
                             jenkel=request.form['jenkel'],
                             nama=nama,
                             saran_kesehatan=saran_kesehatan)
    
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Add this function to your app.py
def get_health_advice(prediction):
    prediction = prediction.lower()
    advice = ""
    
    if 'underweight' in prediction:
        advice = """
        <ul class="list-disc pl-5 text-left">
            <li>Konsumsilah makanan padat nutrisi lebih sering</li>
            <li>Tambah asupan protein (daging, ikan, telur, kacang-kacangan)</li>
            <li>Pilih makanan berkalori sehat seperti alpukat dan kacang-kacangan</li>
            <li>Lakukan latihan kekuatan untuk membangun otot</li>
            <li>Konsultasi dengan ahli gizi jika kesulitan menambah berat</li>
        </ul>
        """
    elif 'normal' in prediction:
        advice = """
        <ul class="list-disc pl-5 text-left">
            <li>Pertahankan pola makan seimbang</li>
            <li>Lakukan aktivitas fisik 150 menit/minggu</li>
            <li>Perbanyak sayur dan buah</li>
            <li>Pantau berat badan secara berkala</li>
            <li>Jaga pola tidur yang cukup</li>
        </ul>
        """
    elif 'overweight' in prediction:
        advice = """
        <ul class="list-disc pl-5 text-left">
            <li>Kurangi porsi makan secara bertahap</li>
            <li>Batasi makanan tinggi gula dan lemak</li>
            <li>Tingkatkan aktivitas fisik harian</li>
            <li>Perbanyak konsumsi serat</li>
            <li>Minum air putih sebelum makan</li>
        </ul>
        """
    elif 'obese' in prediction:
        advice = """
        <ul class="list-disc pl-5 text-left">
            <li>Segera konsultasi dengan dokter atau ahli gizi</li>
            <li>Mulai program penurunan berat badan yang terkontrol</li>
            <li>Hindari makanan cepat saji dan minuman manis</li>
            <li>Lakukan olahraga teratur mulai dari intensitas rendah</li>
            <li>Pantau tekanan darah dan gula darah secara berkala</li>
        </ul>
        """
    else:
        advice = "<p>Konsultasikan dengan profesional kesehatan untuk saran personal</p>"
    
    return advice

if __name__ == '__main__':
    app.run(debug=True)