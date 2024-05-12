from fastapi import FastAPI, HTTPException
from typing import List, Optional
import sqlite3

app = FastAPI()

def create_connection():
    conn = sqlite3.connect('shopping_mall.db')
    return conn

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            full_name TEXT,
            address TEXT,
            payment_info TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            category TEXT,
            price REAL,
            thumbnail_url TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_num INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            selected_product TEXT,
            dest_address TEXT,
            DATE INTEGER,
            pay_PG TEXT,
            pay_PG_DATA TEXT,
            state TEXT
        )
    ''')
    conn.commit()

# [NEW] (6) 구매기록 확인 기능
def get_orders_by_username(conn, username):
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM orders where username = "{username}"')
    orders = cursor.fetchall()
    return [{"order_num": order[0], "selected_product": order[2], "dest_address": order[3], "DATE": order[4], "pay_PG": order[5]} for order in orders]

# [NEW] (9) 상품 구매기록 관리 기능 - 조회 기능
def get_orders_by_num(conn, order_num):
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM orders where order_num = {order_num}')
    return cursor.fetchone()

# [NEW] (9) 상품 구매기록 관리 기능 - 수정 기능
def update_orders(conn, order_num, value, column_name):
    cursor = conn.cursor()
    if get_orders_by_num(conn, order_num) == None:
        return {"status": "fail", "message": "cannot found order!"}
    if column_name == "dest_address":
        cursor.execute('UPDATE orders SET dest_address = ? WHERE order_num = ?', (value, order_num))
        conn.commit()
        return {"status": "success", "message": "order update successfully!"}
    elif column_name == "state":
        cursor.execute('UPDATE orders SET state = ? WHERE order_num = ?', (value, order_num))
        conn.commit()
        return {"status": "success", "message": "order update successfully!"}

# [NEW] 상품 구매 시 orders table에 insert
def add_order(conn, username, selected_product, dest_address, DATE, pay_PG, pay_PG_DATA):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO orders (username, selected_product, dest_address, DATE, pay_PG, pay_PG_DATA) VALUES (?, ?, ?, ?, ?, ?)',
                   (username, selected_product, dest_address, DATE, pay_PG, pay_PG_DATA))
    conn.commit()
    return {"status": "success", "message": "order add successfully!"}

# (4) 회원 가입 기능 - SQL 요청
def add_user(conn, username, password, role, full_name, address, payment_info):
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO users (username, password, role, full_name, address, payment_info) VALUES (?, ?, ?, ?, ?, ?)',
                   (username, password, role, full_name, address, payment_info))
    conn.commit()
    user = {"username": username, "password": password, "role": role, "full_name": full_name, "address": address, "payment_info": payment_info}
    return {"status": "success", "message": "User created successfully!", "user": user}

# (8) 관리자 권한 분리 기능 - SQL 요청
def register_admin(conn, username, password, full_name):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)',
                   (username, password, 'admin', full_name))
    conn.commit()
    user = {"username": username, "password": password, "role": 'admin', "full_name": full_name}
    return {"status": "success", "message": "Admin registered successfully!", "user": user}

# (7) 로그인 기능 - SQL 요청
def authenticate_user(conn, username, password):
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM users WHERE username = "{username}" AND password = "{password}"')
    user = cursor.fetchone()
    if user:
        user_info = {"username": user[1], "password": user[2], "role": user[3], "full_name": user[4], "address": user[5], "payment_info": user[6]}
        return {"message": f"Welcome back, {username}!", "user": user_info}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

# (1) 상품 표시 기능 - SQL 요청
def get_all_products(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return [{"name": product[1], "category": product[2], "price": product[3], "thumbnail_url": product[4]} for product in products]

# (10) 상품 업로드 기능 - SQL 요청
def add_product(conn, name, category, price, thumbnail_url):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, category, price, thumbnail_url) VALUES (?, ?, ?, ?)', (name, category, price, thumbnail_url))
    conn.commit()
    return {"status": "success", "message": "Product added successfully!"}

# (5)-2 회원 정보 변경 기능 - SQL 요청
def update_user_info(conn, username, full_name, address, payment_info):
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET full_name = ?, address = ?, payment_info = ? WHERE username = ?', (full_name, address, payment_info, username))
    conn.commit()
    return {"status": "success", "message": "User information updated successfully!"}

# (5)-1 회원 정보 확인 기능 - SQL 요청
def get_user_by_username(conn, username):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone()

# (5)-1, (8) - 서버 실행 시 관리자 계정이 부존재할 경우 추가
@app.on_event("startup")
async def startup_event():
    conn = create_connection()
    create_tables(conn)
    if not get_user_by_username(conn, "admin"):
        register_admin(conn, "admin", "admin", "Admin User")
    conn.close()

@app.get("/register")
async def register_user(username: str, password: str, role: str, full_name: str, address: Optional[str] = None, payment_info: Optional[str] = None):
    conn = create_connection()
    result = add_user(conn, username, password, role, full_name, address, payment_info)
    conn.close()
    return result

@app.get("/login")
async def login(username: str, password: str):
    conn = create_connection()
    result = authenticate_user(conn, username, password)
    conn.close()
    return result

@app.get("/products", response_model=List[dict])
async def get_products():
    conn = create_connection()
    products = get_all_products(conn)
    conn.close()
    return products

@app.get("/add_product")
async def add_new_product(name: str, category: str, price: float, thumbnail_url: str):
    conn = create_connection()
    result = add_product(conn, name, category, price, thumbnail_url)
    conn.close()
    return result

@app.get("/update_user_info")
async def update_user_info_endpoint(username: str, full_name: str, address: str, payment_info: str):
    conn = create_connection()
    result = update_user_info(conn, username, full_name, address, payment_info)
    conn.close()
    return result

# NEW
@app.get("/orders_by_username", response_model=List[dict])
async def get_orders_by_username_endpoint(username: str):
    conn = create_connection()
    orders = get_orders_by_username(conn, username)
    conn.close()
    return orders

# NEW
@app.get("/orders_by_num")
async def get_orders_by_num_endpoint(order_num: int):
    conn = create_connection()
    orders = get_orders_by_num(conn, order_num)
    conn.close()
    return orders

# NEW
@app.get("/update_orders")
async def update_orders_by_num_endpoint(order_num: int, value: str, column_name: str):
    conn = create_connection()
    result = update_orders(conn, order_num, value, column_name)
    conn.close()
    return result

# NEW
@app.get("/add_order")
async def add_order_endpoint(username: str, selected_product: str, dest_address: str, DATE: int, pay_PG: str, pay_PG_DATA: str, status: str):
    conn = create_connection()
    # conn, username, selected_product, dest_address, DATE, pay_PG, pay_PG_DATA
    # result = add_order(conn, order_num, value, column_name)
    result = add_order(conn, username, selected_product, dest_address, DATE, pay_PG, pay_PG_DATA, status)
    conn.close()
    return result
