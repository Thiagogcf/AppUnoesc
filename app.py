from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

os.environ['FLASK_DEBUG'] = '1'
app.debug = True

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Quiz questions
quiz_questions = [
    {
        "question": "Qual dos seguintes componentes NÃO faz parte da infraestrutura urbana?",
        "name": "q0",
        "options": [
            "Rede de transporte público",
            "Abastecimento de água",
            "Energia elétrica",
            "Produção agrícola rural"
        ],
        "correct_answer": 3
    },
    {
        "question": "Qual é o principal fator a ser considerado no dimensionamento de uma pavimentação asfáltica urbana?",
        "name": "q1",
        "options": [
            "Cor da pavimentação",
            "Carga dos veículos que utilizarão a via",
            "Proximidade de áreas verdes",
            "Tipo de iluminação pública"
        ],
        "correct_answer": 1
    },
    {
        "question": "Qual é a principal função de uma estrutura de contenção em áreas urbanas?",
        "name": "q2",
        "options": [
            "Melhorar a estética da paisagem",
            "Controlar a erosão e deslizamentos de terra",
            "Aumentar o valor imobiliário",
            "Facilitar o plantio de vegetação"
        ],
        "correct_answer": 1
    },
    {
        "question": "Qual dos seguintes elementos NÃO faz parte de um sistema de saneamento básico?",
        "name": "q3",
        "options": [
            "Tratamento de esgoto",
            "Abastecimento de água",
            "Coleta de resíduos sólidos",
            "Produção de energia elétrica"
        ],
        "correct_answer": 3
    },
    {
        "question": "Qual é a principal função de parques urbanos em áreas densamente povoadas?",
        "name": "q4",
        "options": [
            "Aumentar a área construída",
            "Gerar receita para o município",
            "Proporcionar áreas de lazer e promover a qualidade ambiental",
            "Substituir áreas comerciais"
        ],
        "correct_answer": 2
    },
    {
        "question": "Qual é o principal benefício da implementação de iluminação pública LED nas cidades?",
        "name": "q5",
        "options": [
            "Aumento do consumo de energia",
            "Redução dos custos de manutenção e consumo de energia",
            "Melhoria na estética da cidade durante o dia",
            "Aumento do número de postes necessários"
        ],
        "correct_answer": 1
    }
]

@app.route('/')
def index():
    return render_template('index.html', questions=quiz_questions)

@app.route('/submit', methods=['POST'])
def submit():
    nome = request.form['nome']
    sobrenome = request.form['sobrenome']
    email = request.form['email']
    answers = [request.form.get(f'q{i}', '') for i in range(len(quiz_questions))]
    problem_description = request.form['problem_description']

    if 'image' not in request.files:
        return 'No file uploaded', 400
    file = request.files['image']
    if file.filename == '':
        return 'No file selected', 400
    if file:
        filename = secure_filename(f"{nome}_{sobrenome}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    correct_answers = [q['correct_answer'] for q in quiz_questions]
    total_correct = sum(1 for i, a in enumerate(answers) if a != '' and int(a) == correct_answers[i])

    with open('respostas.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([nome, sobrenome, email] + answers + [problem_description, filename, total_correct])

    return redirect(url_for('thank_you'))

@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/list')
def list_submissions():
    submissions = []
    try:
        with open('respostas.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                submissions.append({
                    'nome': row[0],
                    'sobrenome': row[1],
                    'email': row[2],
                    'respostas': row[3:9],
                    'problema': row[9],
                    'imagem': row[10],
                    'total_acertos': row[11]
                })
    except FileNotFoundError:
        pass
    return render_template('list.html', submissions=submissions, questions=quiz_questions)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)