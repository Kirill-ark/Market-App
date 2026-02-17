import sqlite3
from flask import Flask, render_template, redirect, request, session, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'my_super_secret_key'


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    conn = get_db_connection()

    search = request.args.get("q", "")

    if search:
        products = conn.execute(
            "SELECT * FROM products WHERE LOWER(name) LIKE LOWER(?)", (f"%{search}%",)).fetchall()
    else:
        products = conn.execute("SELECT * FROM products").fetchall()
    user = session.get('username')
    cart_dict = {}
    if user:
        user_row = conn.execute('SELECT id FROM users WHERE username = ?', (user,)).fetchone()
        if user_row:
            user_id = user_row['id']
            cart_data = conn.execute('SELECT product_id, quantity FROM cart WHERE user_id = ?', (user_id,)).fetchall()
            cart_dict = {
                item['product_id']: item['quantity']
                for item in cart_data
            }
    conn.close()
    return render_template(
        "catalog.html",
        products=products,
        cart_dict=cart_dict,
        user=user
    )


@app.route("/inc/<int:product_id>")
def inc(product_id):
    if not session.get('username'):
        return redirect("/login")

    conn = get_db_connection()
    username = session['username']
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    user_id = user['id']

    product = conn.execute('SELECT stock FROM products WHERE id = ?', (product_id,)).fetchone()

    if product and product['stock'] > 0:
        conn.execute('UPDATE products SET stock = stock - 1 WHERE id = ?', (product_id,))
        item = conn.execute('SELECT * FROM cart WHERE product_id = ? AND user_id = ?', (product_id, user_id)).fetchone()

        if item:
            conn.execute('UPDATE cart SET quantity = quantity + 1 WHERE product_id = ? AND user_id = ?',
                         (product_id, user_id))
        else:
            conn.execute('INSERT INTO cart (product_id, user_id, quantity) VALUES (?, ?, 1)', (product_id, user_id))

        conn.commit()
    conn.close()
    return redirect(request.referrer or "/")


@app.route("/dec/<int:product_id>")
def dec(product_id):
    if not session.get('username'):
        return redirect("/login")

    conn = get_db_connection()
    username = session['username']
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    user_id = user['id']

    item = conn.execute(
        'SELECT quantity FROM cart WHERE product_id = ? AND user_id = ?',
        (product_id, user_id)
    ).fetchone()

    if item and item['quantity'] > 0:
        conn.execute('UPDATE products SET stock = stock + 1 WHERE id = ?', (product_id,))
        if item['quantity'] > 1:
            conn.execute(
                'UPDATE cart SET quantity = quantity - 1 WHERE product_id = ? AND user_id = ?',
                (product_id, user_id)
            )
        else:
            conn.execute(
                'DELETE FROM cart WHERE product_id = ? AND user_id = ?',
                (product_id, user_id)
            )
        conn.commit()
    conn.close()
    return redirect(request.referrer or "/")


@app.route("/reg", methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        login = request.form.get('username')
        password = request.form.get('password')

        if not login or not password:
            flash("Please fill in all fields!")
            return redirect("/reg")

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (login, password))
            conn.commit()
            conn.close()
            return redirect("/login")
        except sqlite3.IntegrityError:
            conn.close()
            flash("This login is already taken. Try another one.")
            return redirect("/reg")

    return render_template("registration.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_val = request.form.get('username')
        pass_val = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (login_val, pass_val)).fetchone()
        conn.close()

        if user:
            session['username'] = user['username']
            return redirect("/")
        else:
            flash("Wrong username or password")
            return redirect("/login")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect("/")


@app.route("/add_product", methods=['GET', 'POST'])
def add_product():
    if session.get('username') != 'admin':
        return redirect("/")

    if request.method == 'POST':
        name = (request.form.get('name') or "").strip()
        price_raw = (request.form.get('price') or "").replace(",", ".").strip()
        stock_raw = (request.form.get('stock') or "").strip()
        try:
            price_cents = int(round(float(price_raw) * 100))
            stock = int(stock_raw)
        except ValueError:
            flash("Price must be a number (e.g. 19.99) and stock must be an integer.")
            return redirect("/add_product")

        if not name:
            flash("Name can't be empty.")
            return redirect("/add_product")

        if price_cents < 0:
            flash("Price can't be negative.")
            return redirect("/add_product")

        if stock < 0:
            flash("Stock can't be negative.")
            return redirect("/add_product")

        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, price, stock) VALUES (?, ?, ?)', (name, price_cents, stock))
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("add_product.html")


@app.route("/cart")
def cart():
    if not session.get('username'):
        return redirect("/login")
    conn = get_db_connection()
    username = session['username']
    user = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    user_id = user['id']
    items = conn.execute("""
        SELECT c.product_id, c.quantity, p.name, p.price
        FROM cart c
        JOIN products p ON p.id = c.product_id
        WHERE c.user_id = ?
        ORDER BY p.name
    """, (user_id,)).fetchall()
    total_cents = 0
    for it in items:
        total_cents += it['price'] * it['quantity']

    return render_template("cart.html", items=items, total=total_cents, user=username)


@app.route("/clear_cart", methods=["POST"])
def clear_cart():
    if not session.get("username"):
        return redirect("/login")
    conn = get_db_connection()
    username = session["username"]
    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    user_id = user["id"]
    items = conn.execute("SELECT product_id, quantity FROM cart WHERE user_id = ?", (user_id,)).fetchall()
    for it in items:
        conn.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (it["quantity"], it["product_id"]))
    conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    return redirect("/cart")


@app.route("/checkout", methods=["POST"])
def checkout():
    if not session.get("username"):
        return redirect("/login")

    conn = get_db_connection()
    username = session["username"]

    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    user_id = user["id"]
    cart_items = conn.execute("""
        SELECT c.product_id, c.quantity, p.name, p.price
        FROM cart c
        JOIN products p ON p.id = c.product_id
        WHERE c.user_id = ?
    """, (user_id,)).fetchall()

    if not cart_items:
        conn.close()
        return redirect("/cart")

    total_cents = 0
    for it in cart_items:
        total_cents += it["price"] * it["quantity"]

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur = conn.execute("INSERT INTO orders (user_id, total, created_at) VALUES (?, ?, ?)",
                       (user_id, total_cents, created_at))
    order_id = cur.lastrowid

    for it in cart_items:
        conn.execute("""
            INSERT INTO order_items (order_id, product_id, name, price, quantity)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, it["product_id"], it["name"], it["price"], it["quantity"]))

    conn.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    return redirect("/success")
    # return redirect(f"/orders/{order_id}")


@app.route("/orders")
def orders():
    if not session.get("username"):
        return redirect("/login")

    conn = get_db_connection()
    username = session["username"]

    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    user_id = user["id"]

    orders = conn.execute("""
        SELECT id, total, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    conn.close()
    return render_template("orders.html", orders=orders, user=username)


@app.route("/orders/<int:order_id>")
def order_detail(order_id):
    if not session.get("username"):
        return redirect("/login")

    conn = get_db_connection()
    username = session["username"]

    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    user_id = user["id"]

    order = conn.execute("""
        SELECT id, total, created_at
        FROM orders
        WHERE id = ? AND user_id = ?
    """, (order_id, user_id)).fetchone()

    if not order:
        conn.close()
        return redirect("/orders")

    items = conn.execute("""
        SELECT name, price, quantity
        FROM order_items
        WHERE order_id = ?
        ORDER BY id
    """, (order_id,)).fetchall()

    conn.close()
    return render_template("order_detail.html", order=order, items=items, user=username)


@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(debug=True)
