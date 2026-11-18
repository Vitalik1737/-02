from __future__ import annotations
import os, sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from flask import Flask, g, jsonify, redirect, render_template, request, url_for, flash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-development-key")
app.config["DATABASE"] = os.environ.get("DATABASE_PATH", os.path.join(app.instance_path, "fintrack.sqlite3"))
os.makedirs(app.instance_path, exist_ok=True)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None: db.close()

def init_db():
    db=get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, kind TEXT NOT NULL CHECK(kind IN ('income','expense')));
    CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, amount TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('income','expense')), category_id INTEGER NOT NULL REFERENCES categories(id), operation_date TEXT NOT NULL, comment TEXT NOT NULL DEFAULT '');
    """)
    if db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        db.executemany("INSERT INTO categories(name,kind) VALUES (?,?)", [("Зарплата","income"),("Подарки","income"),("Продукты","expense"),("Транспорт","expense")])
    db.commit()

@app.before_request
def ensure_db(): init_db()

def validate_transaction(data):
    try: amount=Decimal(str(data.get("amount", "")))
    except (InvalidOperation, ValueError): return None, "Сумма должна быть числом"
    if not amount.is_finite() or amount <= 0: return None, "Сумма должна быть больше нуля"
    kind=data.get("kind")
    if kind not in ("income","expense"): return None, "Неизвестный тип операции"
    try: category_id=int(data.get("category_id"))
    except (TypeError, ValueError): return None, "Выберите категорию"
    category=get_db().execute("SELECT id,kind FROM categories WHERE id=?",(category_id,)).fetchone()
    if category is None or category["kind"] != kind: return None, "Категория не соответствует типу операции"
    op_date=data.get("operation_date") or date.today().isoformat()
    try: date.fromisoformat(op_date)
    except ValueError: return None, "Дата должна быть в формате ГГГГ-ММ-ДД"
    return {"amount": str(amount.quantize(Decimal("0.01"))), "kind":kind, "category_id":category_id, "operation_date":op_date, "comment":str(data.get("comment", "")).strip()[:250]}, None

@app.get("/")
def index():
    db=get_db()
    rows=db.execute("SELECT t.*, c.name category_name FROM transactions t JOIN categories c ON c.id=t.category_id ORDER BY t.operation_date DESC,t.id DESC").fetchall()
    categories=db.execute("SELECT * FROM categories ORDER BY kind,name").fetchall()
    return render_template("index.html", transactions=rows, categories=categories)

@app.post("/transactions")
def create_transaction():
    item,error=validate_transaction(request.form)
    if error: flash(error,"error"); return redirect(url_for("index"))
    db=get_db(); db.execute("INSERT INTO transactions(amount,kind,category_id,operation_date,comment) VALUES (?,?,?,?,?)",(item["amount"],item["kind"],item["category_id"],item["operation_date"],item["comment"]))
    db.commit(); flash("Операция сохранена","success"); return redirect(url_for("index"))

@app.post("/transactions/<int:transaction_id>/delete")
def delete_transaction(transaction_id):
    db=get_db(); db.execute("DELETE FROM transactions WHERE id=?",(transaction_id,)); db.commit(); return redirect(url_for("index"))

@app.get("/api/categories")
def api_categories():
    rows=get_db().execute("SELECT id,name,kind FROM categories ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.get("/api/transactions")
def api_transactions():
    rows=get_db().execute("SELECT t.id,t.amount,t.kind,t.operation_date,t.comment,c.name category FROM transactions t JOIN categories c ON c.id=t.category_id ORDER BY t.id").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/transactions")
def api_create_transaction():
    item,error=validate_transaction(request.get_json(silent=True) or {})
    if error: return jsonify({"error":error}),400
    db=get_db(); cur=db.execute("INSERT INTO transactions(amount,kind,category_id,operation_date,comment) VALUES (?,?,?,?,?)",(item["amount"],item["kind"],item["category_id"],item["operation_date"],item["comment"]))
    db.commit(); return jsonify({"id":cur.lastrowid, **item}),201

@app.get("/api/reports/summary")
def api_summary():
    rows=get_db().execute("SELECT kind,COALESCE(SUM(CAST(amount AS REAL)),0) total FROM transactions GROUP BY kind").fetchall()
    totals={"income":0.0,"expense":0.0}
    for row in rows: totals[row["kind"]]=round(row["total"],2)
    totals["balance"]=round(totals["income"]-totals["expense"],2)
    return jsonify(totals)

if __name__ == "__main__": app.run(debug=True)
