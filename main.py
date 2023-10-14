from flask import Flask, render_template, g, request, jsonify, url_for, redirect, flash, session
from flask_session import Session
from module.test_module import test_module
import sqlite3, os, base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import random
import string
import secrets
import string
import hashlib

app = Flask(__name__)
app.register_blueprint(test_module)
DATABASE = 'maindata.db'
UPLOAD_FOLDER = 'static/img_upload_folder'   # 이미지 업로드 폴더 경로로 변경해주세요
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_pyfile('config.py')
app.secret_key = 'hellowk09!'
app.config['SESSION_TYPE'] = 'filesystem'  # 세션을 파일 시스템에 저장
Session(app)

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 비밀번호 안전성 검사 로직을 추가
        if not is_password_secure(password):
            flash('비밀번호가 안전성 요건을 충족하지 않습니다. 비밀번호는 최소 8자 이상이어야 하며, 대문자, 소문자, 숫자, 특수문자를 혼합해야 합니다.', 'danger')
            return redirect(url_for('register'))
        
        conn = sqlite3.connect('user.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username=?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash('이미 사용 중인 사용자 이름입니다. 다른 사용자 이름을 선택해주세요.', 'danger')
        else:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()

            flash('회원가입이 완료되었습니다.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

def is_password_secure(password):
    # 비밀번호의 안전성 검사 로직
    # 최소 8자 이상, 대문자, 소문자, 숫자, 특수문자를 혼합해야 함
    if len(password) < 8:
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char in string.punctuation for char in password):
        return False
    return True


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('user.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            # 세션에 사용자 정보 저장
            session['username'] = username

            flash('로그인 성공!', 'success')
            return redirect('/')
        else:
            flash('로그인 실패. 사용자 이름 또는 비밀번호가 일치하지 않습니다.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    # 세션에서 사용자 정보 제거 (로그아웃)
    session.pop('username', None)
    flash('로그아웃되었습니다.', 'success')
    return redirect('/')

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
    count2 = int(request.form.get('quantity'))
    buyer_email = request.form['email']  # 구매자 이메일 주소 수집
    seller_email = 'insanenwk@gmail.com'  # 판매자 이메일 주소 (수정 가능)
    name = request.form['name']
    address = request.form['address']
    phone = request.form['phone']
    price = int(request.form.get('price'))
    finalprice = price * count2
    order_id = request.form['order_id']
    conn = sqlite3.connect('orderid.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (order_id, product_name, quantity) VALUES (?, ?, ?)', (order_id, name2, count2))
    conn.commit()
    conn.close()

    # 이메일 내용 생성
    subject = "주문 요청이 발송되었습니다."
    buyer_body = f"성명: {name}님<br>주소: {address}<br>전화번호: {phone}<br>상품 이름: {name2}<br>주문 수량: {count2}개<br>주문 수량: {price}원<br>합계 : {finalprice}원<br>정보를 확인하시고 아래 계좌로 {finalprice}원을 입금해 주세요.<br>입금주 : 나원규<br>계좌번호 : 123412341234  농협은행<br>!주의! : 입금하실 떄 입금자명을 \"{order_id}\" 로 변경하여 입금해주세요.<br>주의사항을 따르지 않으시면 결제 및 배송에 지연이 발생할 수 있습니다."
    seller_body = f"주문자 이름: {name}<br>이메일: {buyer_email}<br>주소: {address}<br>전화번호: {phone}<br>상품 이름: {name2}<br>주문 수량: {count2}개<br>제품 가격 : {price}원<br>주문 번호 : {order_id}<br>합계 : {finalprice}원<br>" \
              f"<a href='http://127.0.0.1:8081/process_order/{order_id}' style='display: inline-block; padding: 10px 20px; background-color: #007BFF; color: #fff; text-decoration: none; border-radius: 5px;'>주문 처리</a>"


    # 이메일 보내기
    send_email(buyer_email, subject, buyer_body)  # 구매자에게 이메일 전송
    send_email(seller_email, subject, seller_body)  # 판매자에게 이메일 전송

    return redirect('/shop')
    
@app.route('/process_order/<order_id>', methods=['GET'])
def process_order(order_id):
    # 첫 번째로 유저네임이 "Administrator"인지 확인
    if 'username' in session and session['username'] == 'Administrator':
        # 주문 ID로 DB에서 해당 주문 정보 조회
        with sqlite3.connect('orderid.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT order_id, product_name, quantity FROM orders WHERE order_id = ?", (order_id,))
            order_data = cursor.fetchall()

        # 만약 주문 ID가 DB에 없으면 오류 페이지를 표시
        if not order_data:
            error_message = '주문을 찾을 수 없습니다.'
            return render_template('error.html', error_message=error_message)

        # 주문 정보 추출
        for order_id1, name1, count1 in order_data:
            # 상품 재고를 업데이트
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT count FROM product WHERE name = ?", (name1,))
                selected_data = cursor.fetchone()

                if selected_data:
                    if (selected_data[0] - count1) >= 0:
                        cursor.execute("UPDATE product SET count = count - ? WHERE name = ?", (count1, name1,))
                        conn.commit()
                        
                        # 처리가 완료된 order_id를 삭제
                        with sqlite3.connect('orderid.db') as delete_conn:
                            delete_cursor = delete_conn.cursor()
                            delete_cursor.execute("DELETE FROM orders WHERE order_id = ?", (order_id1,))
                            delete_conn.commit()
                    else:
                        error_message = '상품 재고가 부족합니다.'
                        return render_template('error.html', error_message=error_message)

        # 주문 처리가 완료되면 어떤 화면을 보여줄지 여기에 구현합니다.
        return render_template('order_processed.html')
    else:
        # 유저네임이 "Administrator"가 아닌 경우 오류 메시지를 표시
        error_message = '관리자만 접근할 수 있습니다.'
        return render_template('error.html', error_message=error_message)

def send_email(to_email, subject, body):
    # Gmail SMTP 서버 설정
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'sanenwk@gmail.com'  # Gmail 계정 이메일 주소
    smtp_password = 'dhihurllpxvhruql'  # Gmail 계정 비밀번호

    # 이메일 메시지 생성
    msg = MIMEMultipart()
    msg['From'] = 'Receipt'
    msg['To'] = to_email  # 받는 사람 이메일 주소
    msg['Subject'] = subject

    # 이메일 본문 추가
    msg.attach(MIMEText(body, 'html'))

    # SMTP 서버 연결 및 이메일 보내기
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())
        server.quit()
        print(f"이메일이 성공적으로 발송하였습니다. (받는 사람: {to_email})")
    except Exception as e:
        print(f"이메일 발송에 실패하였습니다. (받는 사람: {to_email}): {str(e)}")


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
    # Remove the password check
    # if request.method == 'POST':
    #     password_attempt = request.form.get('password')
    #     if password_attempt == app.config['ADMIN_PASSWORD']:
    #         return render_template('adminpanel.html')
    #     else:
    #         error_message = '비밀번호가 올바르지 않습니다.'
    #         return render_template('admin_login.html', error_message=error_message)

    # Check if the user is logged in as Administrator
    if 'username' in session and session['username'] == 'Administrator':
        return render_template('adminpanel.html')
    else:
        return render_template('error.html', error_message="관리자만 접근할 수 있습니다.")

if __name__ == "__main__":              
    app.run(host="0.0.0.0", port="8081" ,debug=True)