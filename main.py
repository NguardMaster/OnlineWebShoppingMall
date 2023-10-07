from flask import Flask, render_template, g, request, jsonify, url_for, redirect
from module.test_module import test_module
import sqlite3, os, base64

app = Flask(__name__)
app.register_blueprint(test_module)
DATABASE = 'maindata.db'
UPLOAD_FOLDER = 'static/img_upload_folder'   # 이미지 업로드 폴더 경로로 변경해주세요
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_pyfile('config.py')


@app.teardown_appcontext
def close_connection(exception):
    # 데이터베이스 연결 종료 시 호출되는 함수입니다.
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.before_request
def create_tables():
    # 앱이 처음 요청되었을 때 데이터베이스 파일과 테이블을 생성합니다.
    if not os.path.exists(DATABASE):
        with app.app_context():
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS product (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, count INTEGER, filename TEXT)")
            conn.commit()

# 이미지 업로드 폴더가 없으면 폴더를 생성하는 함수
def create_upload_folder_if_not_exists():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def get_db():
    # g 객체를 통해 데이터베이스 연결을 관리합니다.
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def save_data_to_db(name, price, count, filepath):
    # 데이터를 DB에 저장하는 함수
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO product (name, price, count, filename) VALUES (?, ?, ?, ?)", (name, price, count, filepath))
        conn.commit()

def save_image(file):
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath


@app.route('/save_data', methods=['POST'])
def save_data():
    create_upload_folder_if_not_exists()  # 업로드 폴더 생성
    # 클라이언트로부터 전송된 데이터 추출
    name = request.form.get('name')
    price = request.form.get('price')
    count = request.form.get('count')
    image = request.files['image']

    filepath = save_image(image)

    # 데이터를 DB에 저장
    save_data_to_db(name, price, count, filepath)
    # 필요한 경우 응답을 반환하거나 리디렉션을 수행
    return render_template('success.html')


def get_data_from_db():
    # 데이터를 DB에서 조회하는 함수
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product")
        rows = cursor.fetchall()
        return rows

@app.route('/get_data', methods=['GET'])
def get_data():
    # DB에서 데이터를 조회
    data = []
    rows = get_data_from_db()
    # 조회한 데이터를 JSON 형식으로 변환하여 클라이언트로 응답
    for row in rows:
        item = {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "count": row[3],
            "file": url_for('static', filename=row[4].replace('\\', '/'))
        }

        data.append(item)
    print(data)
    return jsonify(data)

@app.route('/dec_data', methods=['POST'])
def dec_data():
    name2 = request.form.get('productname1')
    count2 = request.form.get('quantity')
    print(name2, count2)
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE product SET count = count - ? WHERE name = ?", (count2, name2,))
        conn.commit()
    return redirect('/shop')


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/shop")
def about():
    # DB에서 데이터를 조회
    data = get_data_from_db()
    print(data)
    return render_template('shop.html', data=data)

@app.route("/admin", methods=['GET', 'POST'])
def adminpanel():
    if request.method == 'POST':
        # POST 요청을 처리하여 입력된 비밀번호를 확인
        password_attempt = request.form.get('password')
        if password_attempt == app.config['ADMIN_PASSWORD']:
            # 비밀번호가 일치하는 경우, adminpanel.html 페이지로 이동
            return render_template('adminpanel.html')
        else:
            # 비밀번호가 일치하지 않는 경우 에러 메시지를 표시
            error_message = '비밀번호가 올바르지 않습니다.'
            return render_template('admin_login.html', error_message=error_message)

    # GET 요청인 경우, 로그인 폼을 표시
    return render_template('admin_login.html')

if __name__ == "__main__":              
    app.run(host="0.0.0.0", port="8081" ,debug=True)