import json

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
import os
import csv
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.secret_key = os.urandom(24)  # Generate a random secret key

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

CORRECT_ANSWERS = [3, 1, 1, 3, 2, 1]
ADMIN_PASSWORD = generate_password_hash('admin')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    nome = request.form['nome']
    sobrenome = request.form['sobrenome']
    telefone = request.form['telefone']
    escola = request.form['escola']
    answers = [int(request.form.get(f'q{i}', -1)) for i in range(6)]
    problem_description = request.form['problem_description']
    problem_solution = request.form['problem_solution']

    # Check if the phone number has already been used
    if check_duplicate_phone(telefone):
        return jsonify({
            "success": False,
            "message": "Este número de telefone já foi utilizado. Por favor, use um número diferente."
        }), 400

    if 'image' not in request.files:
        return jsonify({"success": False, "message": "Nenhum arquivo foi enviado."}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "message": "Nenhum arquivo foi selecionado."}), 400

    if file:
        filename = secure_filename(f"{nome}_{sobrenome}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

    total_correct = sum(1 for i, a in enumerate(answers) if a == CORRECT_ANSWERS[i])

    respostas_detalhadas = [
        {
            "correta": answers[i] == CORRECT_ANSWERS[i],
            "resposta_correta": CORRECT_ANSWERS[i] if answers[i] != CORRECT_ANSWERS[i] else None
        }
        for i in range(6)
    ]

    # Save to CSV
    with open('respostas.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([nome, sobrenome, telefone, escola] + answers + [problem_description, filename, problem_solution, total_correct])

    return jsonify({
        "success": True,
        "message": "Respostas registradas com sucesso!",
        "total_acertos": total_correct,
        "respostas": respostas_detalhadas
    })

# ... (rest of the code remains the same)

def check_duplicate_phone(telefone):
    try:
        with open('respostas.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[2] == telefone:
                    return True
    except FileNotFoundError:
        pass
    return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password_hash(ADMIN_PASSWORD, password):
            session['logged_in'] = True
            return redirect(url_for('list_submissions'))
        else:
            return render_template('login.html', error='Senha incorreta')
    return render_template('login.html')


def escapejs(val):
    return json.dumps(str(val))

app.jinja_env.filters['escapejs'] = escapejs
@app.route('/list')
def list_submissions():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    submissions = []
    try:
        with open('respostas.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                submissions.append({
                    'nome': row[0],
                    'sobrenome': row[1],
                    'telefone': row[2],
                    'escola': row[3],
                    'respostas': row[4:10],
                    'problema': row[10],
                    'imagem': row[11],
                    'solucao': row[12],
                    'total_acertos': row[13]
                })
    except FileNotFoundError:
        pass
    return render_template('list.html', submissions=submissions)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
