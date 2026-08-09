from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
    Response
)

from database import get_connection

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from functools import wraps
from datetime import datetime
from decimal import Decimal
import csv
import io
import os


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "smart-expense-tracker-secret-key-change-this"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# =========================================================
# DATABASE SETUP
# =========================================================

def initialize_database():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # -------------------------------------------------
        # INCOME TABLE
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS income (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount NUMERIC(10,2) NOT NULL,
                source VARCHAR(100) NOT NULL,
                description VARCHAR(255),
                income_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # -------------------------------------------------
        # BUDGET UNIQUE INDEX
        #
        # IMPORTANT:
        # We use budgets.month only.
        # No budget_month column.
        # -------------------------------------------------

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            budgets_user_month_unique_index
            ON budgets(user_id, month)
            """
        )

        connection.commit()

        print("Database tables verified successfully.")

    except Exception as error:

        if connection:
            connection.rollback()

        print("DATABASE INITIALIZATION ERROR:", error)

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# LOGIN CHECK
# =========================================================

def login_required():

    return "user_id" in session


def require_login(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return jsonify({
                "error": "Please login first"
            }), 401

        return function(*args, **kwargs)

    return wrapper


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template(
        "index.html",
        username=session.get("username")
    )


# =========================================================
# LOGIN PAGE
# =========================================================

@app.route("/login")
def login():

    if "user_id" in session:

        return redirect(url_for("home"))

    return render_template("login.html")


# =========================================================
# PROFILE PAGE
# =========================================================

@app.route("/profile")
def profile():

    if "user_id" not in session:

        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        username=session.get("username")
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json() or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not username or not password:

        return jsonify({
            "error": "Username and password are required"
        }), 400

    if len(username) < 3:

        return jsonify({
            "error": "Username must contain at least 3 characters"
        }), 400

    if len(username) > 50:

        return jsonify({
            "error": "Username cannot exceed 50 characters"
        }), 400

    if len(password) < 6:

        return jsonify({
            "error": "Password must contain at least 6 characters"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        if cursor.fetchone():

            return jsonify({
                "error": "Username already exists"
            }), 409

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                password_hash
            )
            VALUES (%s, %s)
            RETURNING id
            """,
            (
                username,
                password_hash
            )
        )

        user_id = cursor.fetchone()[0]

        connection.commit()

        return jsonify({
            "message": "Registration successful",
            "user_id": user_id
        }), 201

    except Exception as error:

        if connection:
            connection.rollback()

        print("REGISTER ERROR:", error)

        return jsonify({
            "error": "Registration failed"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# LOGIN API
# =========================================================

@app.route("/api/login", methods=["POST"])
def login_user():

    data = request.get_json() or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not username or not password:

        return jsonify({
            "error": "Username and password are required"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                username,
                password_hash
            FROM users
            WHERE username = %s
            """,
            (username,)
        )

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "error": "Invalid username or password"
            }), 401

        user_id = user[0]
        stored_username = user[1]
        password_hash = user[2]

        if not check_password_hash(
            password_hash,
            password
        ):

            return jsonify({
                "error": "Invalid username or password"
            }), 401

        session.clear()

        session["user_id"] = user_id
        session["username"] = stored_username

        return jsonify({
            "message": "Login successful"
        }), 200

    except Exception as error:

        print("LOGIN ERROR:", error)

        return jsonify({
            "error": "Login server error"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# CURRENT USER
# =========================================================

@app.route("/api/current-user", methods=["GET"])
def current_user():

    if "user_id" not in session:

        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "user_id": session["user_id"],
        "username": session["username"]
    })


# =========================================================
# DASHBOARD FINANCIAL SUMMARY
# =========================================================

@app.route("/api/dashboard-summary", methods=["GET"])
@require_login
def dashboard_summary():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # TOTAL INCOME

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM income
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        total_income = float(
            cursor.fetchone()[0]
        )

        # TOTAL EXPENSES

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        total_expenses = float(
            cursor.fetchone()[0]
        )

        # RECORD COUNT

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM expenses
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        total_records = cursor.fetchone()[0]

        balance = (
            total_income -
            total_expenses
        )

        return jsonify({

            "total_income": round(
                total_income,
                2
            ),

            "total_expenses": round(
                total_expenses,
                2
            ),

            "balance": round(
                balance,
                2
            ),

            "total_records": total_records

        })

    except Exception as error:

        print(
            "DASHBOARD SUMMARY ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET INCOME
# =========================================================

@app.route("/api/income", methods=["GET"])
@require_login
def get_income():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                amount,
                source,
                description,
                income_date
            FROM income
            WHERE user_id = %s
            ORDER BY income_date DESC, id DESC
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        income_list = []

        for row in rows:

            income_list.append({

                "id": row[0],

                "amount": float(
                    row[1]
                ),

                "source": row[2],

                "description": row[3] or "",

                "income_date": str(
                    row[4]
                )

            })

        return jsonify(
            income_list
        ), 200

    except Exception as error:

        print(
            "GET INCOME ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET TOTAL INCOME
# =========================================================

@app.route("/api/income/summary", methods=["GET"])
@require_login
def income_summary():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM income
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        total = float(
            cursor.fetchone()[0]
        )

        return jsonify({

            "total_income": round(
                total,
                2
            )

        })

    except Exception as error:

        print(
            "INCOME SUMMARY ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADD INCOME
# =========================================================

@app.route("/api/income", methods=["POST"])
@require_login
def add_income():

    data = request.get_json() or {}

    amount = data.get("amount")
    source = str(
        data.get("source", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    income_date = data.get(
        "income_date"
    )

    if amount is None:
        return jsonify({
            "error": "Income amount is required"
        }), 400

    if not source:
        return jsonify({
            "error": "Income source is required"
        }), 400

    if not income_date:
        return jsonify({
            "error": "Income date is required"
        }), 400

    try:

        amount = float(amount)

        if amount <= 0:

            return jsonify({
                "error": "Income amount must be greater than zero"
            }), 400

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "error": "Income amount must be a valid number"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO income
            (
                user_id,
                amount,
                source,
                description,
                income_date
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                session["user_id"],
                amount,
                source,
                description,
                income_date
            )
        )

        income_id = cursor.fetchone()[0]

        connection.commit()

        return jsonify({

            "message":
                "Income added successfully",

            "income_id":
                income_id

        }), 201

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "ADD INCOME ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE INCOME
# =========================================================

@app.route(
    "/api/income/<int:income_id>",
    methods=["DELETE"]
)
@require_login
def delete_income(income_id):

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM income
            WHERE
                id = %s
                AND user_id = %s
            """,
            (
                income_id,
                session["user_id"]
            )
        )

        if cursor.rowcount == 0:

            return jsonify({
                "error": "Income record not found"
            }), 404

        connection.commit()

        return jsonify({
            "message":
                "Income deleted successfully"
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "DELETE INCOME ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET EXPENSES
# =========================================================

@app.route("/api/expenses", methods=["GET"])
@require_login
def get_expenses():

    month = request.args.get("month")

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        if month:

            cursor.execute(
                """
                SELECT
                    id,
                    amount,
                    category,
                    description,
                    expense_date
                FROM expenses
                WHERE
                    user_id = %s
                    AND TO_CHAR(
                        expense_date,
                        'YYYY-MM'
                    ) = %s
                ORDER BY
                    expense_date DESC,
                    id DESC
                """,
                (
                    session["user_id"],
                    month
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    id,
                    amount,
                    category,
                    description,
                    expense_date
                FROM expenses
                WHERE user_id = %s
                ORDER BY
                    expense_date DESC,
                    id DESC
                """,
                (session["user_id"],)
            )

        rows = cursor.fetchall()

        expenses = []

        for row in rows:

            expenses.append({

                "id": row[0],

                "amount": float(
                    row[1]
                ),

                "category": row[2],

                "description": row[3] or "",

                "expense_date": str(
                    row[4]
                )

            })

        return jsonify(expenses)

    except Exception as error:

        print(
            "GET EXPENSE ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# ADD EXPENSE
# =========================================================

@app.route("/api/expenses", methods=["POST"])
@require_login
def add_expense():

    data = request.get_json() or {}

    amount = data.get("amount")

    category = str(
        data.get("category", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    expense_date = data.get(
        "expense_date"
    )

    if amount is None:

        return jsonify({
            "error":
                "Amount is required"
        }), 400

    if not category:

        return jsonify({
            "error":
                "Category is required"
        }), 400

    if not expense_date:

        return jsonify({
            "error":
                "Expense date is required"
        }), 400

    try:

        amount = float(amount)

        if amount <= 0:

            return jsonify({
                "error":
                    "Amount must be greater than zero"
            }), 400

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "error":
                "Amount must be a valid number"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO expenses
            (
                amount,
                category,
                description,
                expense_date,
                user_id
            )
            VALUES
            (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                amount,
                category,
                description,
                expense_date,
                session["user_id"]
            )
        )

        expense_id = cursor.fetchone()[0]

        connection.commit()

        return jsonify({

            "message":
                "Expense added successfully",

            "expense_id":
                expense_id

        }), 201

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "ADD EXPENSE ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# UPDATE EXPENSE
# =========================================================

@app.route(
    "/api/expenses/<int:expense_id>",
    methods=["PUT"]
)
@require_login
def update_expense(expense_id):

    data = request.get_json() or {}

    amount = data.get("amount")

    category = str(
        data.get("category", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    expense_date = data.get(
        "expense_date"
    )

    if amount is None:
        return jsonify({
            "error":
                "Amount is required"
        }), 400

    if not category:
        return jsonify({
            "error":
                "Category is required"
        }), 400

    if not expense_date:
        return jsonify({
            "error":
                "Expense date is required"
        }), 400

    try:

        amount = float(amount)

        if amount <= 0:

            return jsonify({
                "error":
                    "Amount must be greater than zero"
            }), 400

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "error":
                "Amount must be a valid number"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE expenses
            SET
                amount = %s,
                category = %s,
                description = %s,
                expense_date = %s
            WHERE
                id = %s
                AND user_id = %s
            """,
            (
                amount,
                category,
                description,
                expense_date,
                expense_id,
                session["user_id"]
            )
        )

        if cursor.rowcount == 0:

            return jsonify({
                "error":
                    "Expense not found"
            }), 404

        connection.commit()

        return jsonify({
            "message":
                "Expense updated successfully"
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "UPDATE EXPENSE ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# DELETE EXPENSE
# =========================================================

@app.route(
    "/api/expenses/<int:expense_id>",
    methods=["DELETE"]
)
@require_login
def delete_expense(expense_id):

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM expenses
            WHERE
                id = %s
                AND user_id = %s
            """,
            (
                expense_id,
                session["user_id"]
            )
        )

        if cursor.rowcount == 0:

            return jsonify({
                "error":
                    "Expense not found"
            }), 404

        connection.commit()

        return jsonify({
            "message":
                "Expense deleted successfully"
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "DELETE EXPENSE ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# CATEGORY SUMMARY
# =========================================================

@app.route("/api/summary", methods=["GET"])
@require_login
def get_summary():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                category,
                SUM(amount)
            FROM expenses
            WHERE user_id = %s
            GROUP BY category
            ORDER BY SUM(amount) DESC
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        summary = []

        for row in rows:

            summary.append({

                "category": row[0],

                "total": float(
                    row[1]
                )

            })

        return jsonify(summary)

    except Exception as error:

        print(
            "SUMMARY ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# MONTHLY EXPENSE SUMMARY
# =========================================================

@app.route(
    "/api/monthly-summary",
    methods=["GET"]
)
@require_login
def get_monthly_summary():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                TO_CHAR(
                    expense_date,
                    'YYYY-MM'
                ) AS month,
                SUM(amount)
            FROM expenses
            WHERE user_id = %s
            GROUP BY month
            ORDER BY month
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        monthly_data = []

        for row in rows:

            monthly_data.append({

                "month": row[0],

                "total": float(
                    row[1]
                )

            })

        return jsonify(
            monthly_data
        )

    except Exception as error:

        print(
            "MONTHLY SUMMARY ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# EXPENSE STATISTICS
# =========================================================

@app.route(
    "/api/statistics",
    methods=["GET"]
)
@require_login
def expense_statistics():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Average and largest expense

        cursor.execute(
            """
            SELECT
                COALESCE(AVG(amount), 0),
                COALESCE(MAX(amount), 0),
                COUNT(*)
            FROM expenses
            WHERE user_id = %s
            """,
            (session["user_id"],)
        )

        row = cursor.fetchone()

        average_expense = float(
            row[0]
        )

        largest_expense = float(
            row[1]
        )

        total_records = int(
            row[2]
        )

        # Top category

        cursor.execute(
            """
            SELECT
                category,
                SUM(amount)
            FROM expenses
            WHERE user_id = %s
            GROUP BY category
            ORDER BY SUM(amount) DESC
            LIMIT 1
            """,
            (session["user_id"],)
        )

        top_row = cursor.fetchone()

        if top_row:

            top_category = top_row[0]

        else:

            top_category = "-"

        return jsonify({

            "average_expense":
                round(
                    average_expense,
                    2
                ),

            "largest_expense":
                round(
                    largest_expense,
                    2
                ),

            "top_category":
                top_category,

            "total_records":
                total_records

        })

    except Exception as error:

        print(
            "STATISTICS ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# SAVE / UPDATE BUDGET
#
# IMPORTANT:
# ONLY budgets.month IS USED
# =========================================================

@app.route(
    "/api/budget",
    methods=["POST"]
)
@require_login
def save_budget():

    data = request.get_json() or {}

    month = str(
        data.get("month", "")
    ).strip()

    amount = data.get("amount")

    if not month:

        return jsonify({
            "error":
                "Month is required"
        }), 400

    if amount is None:

        return jsonify({
            "error":
                "Budget amount is required"
        }), 400

    try:

        amount = float(amount)

        if amount <= 0:

            return jsonify({
                "error":
                    "Budget must be greater than zero"
            }), 400

    except (
        ValueError,
        TypeError
    ):

        return jsonify({
            "error":
                "Budget amount must be a valid number"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # First check whether budget already exists.

        cursor.execute(
            """
            SELECT id
            FROM budgets
            WHERE
                user_id = %s
                AND month = %s
            """,
            (
                session["user_id"],
                month
            )
        )

        existing = cursor.fetchone()

        if existing:

            cursor.execute(
                """
                UPDATE budgets
                SET amount = %s
                WHERE
                    user_id = %s
                    AND month = %s
                """,
                (
                    amount,
                    session["user_id"],
                    month
                )
            )

            message = (
                "Budget updated successfully"
            )

        else:

            cursor.execute(
                """
                INSERT INTO budgets
                (
                    user_id,
                    month,
                    amount
                )
                VALUES
                (%s, %s, %s)
                """,
                (
                    session["user_id"],
                    month,
                    amount
                )
            )

            message = (
                "Budget saved successfully"
            )

        connection.commit()

        return jsonify({
            "message": message
        }), 200

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "SAVE BUDGET ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET BUDGET STATUS
# =========================================================

@app.route(
    "/api/budget-status",
    methods=["GET"]
)
@require_login
def budget_status():

    month = request.args.get(
        "month"
    )

    if not month:

        return jsonify({
            "error":
                "Month is required"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # -------------------------------------------------
        # GET BUDGET
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT amount
            FROM budgets
            WHERE
                user_id = %s
                AND month = %s
            """,
            (
                session["user_id"],
                month
            )
        )

        budget_row = cursor.fetchone()

        if budget_row:

            budget = float(
                budget_row[0]
            )

        else:

            budget = 0.0

        # -------------------------------------------------
        # GET MONTHLY EXPENSES
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE
                user_id = %s
                AND TO_CHAR(
                    expense_date,
                    'YYYY-MM'
                ) = %s
            """,
            (
                session["user_id"],
                month
            )
        )

        spent = float(
            cursor.fetchone()[0]
        )

        remaining = (
            budget - spent
        )

        if budget > 0:

            percentage = (
                spent / budget
            ) * 100

        else:

            percentage = 0

        # -------------------------------------------------
        # WARNING LEVEL
        # -------------------------------------------------

        if budget <= 0:

            warning = "none"

        elif percentage >= 100:

            warning = "exceeded"

        elif percentage >= 80:

            warning = "danger"

        elif percentage >= 60:

            warning = "warning"

        else:

            warning = "safe"

        return jsonify({

            "month": month,

            "budget": round(
                budget,
                2
            ),

            "spent": round(
                spent,
                2
            ),

            "remaining": round(
                remaining,
                2
            ),

            "percentage": round(
                percentage,
                2
            ),

            "warning": warning

        })

    except Exception as error:

        print(
            "BUDGET STATUS ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# PROFILE INFORMATION
# =========================================================

@app.route(
    "/api/profile",
    methods=["GET"]
)
@require_login
def get_profile():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                username,
                created_at
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "error":
                    "User not found"
            }), 404

        return jsonify({

            "id": user[0],

            "username": user[1],

            "created_at": str(
                user[2]
            )

        })

    except Exception as error:

        print(
            "PROFILE ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# CHANGE PASSWORD
# =========================================================

@app.route(
    "/api/change-password",
    methods=["POST"]
)
@require_login
def change_password():

    data = request.get_json() or {}

    current_password = data.get(
        "current_password",
        ""
    )

    new_password = data.get(
        "new_password",
        ""
    )

    if not current_password:

        return jsonify({
            "error":
                "Current password is required"
        }), 400

    if not new_password:

        return jsonify({
            "error":
                "New password is required"
        }), 400

    if len(new_password) < 6:

        return jsonify({
            "error":
                "New password must contain at least 6 characters"
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = %s
            """,
            (session["user_id"],)
        )

        row = cursor.fetchone()

        if not row:

            return jsonify({
                "error":
                    "User not found"
            }), 404

        if not check_password_hash(
            row[0],
            current_password
        ):

            return jsonify({
                "error":
                    "Current password is incorrect"
            }), 401

        new_hash = generate_password_hash(
            new_password
        )

        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
            """,
            (
                new_hash,
                session["user_id"]
            )
        )

        connection.commit()

        return jsonify({
            "message":
                "Password changed successfully"
        })

    except Exception as error:

        if connection:
            connection.rollback()

        print(
            "CHANGE PASSWORD ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# EXPORT EXPENSES TO CSV
# =========================================================

@app.route(
    "/api/export/csv",
    methods=["GET"]
)
@require_login
def export_csv():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                amount,
                category,
                description,
                expense_date
            FROM expenses
            WHERE user_id = %s
            ORDER BY expense_date DESC
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        output = io.StringIO()

        writer = csv.writer(
            output
        )

        writer.writerow([
            "ID",
            "Amount",
            "Category",
            "Description",
            "Date"
        ])

        for row in rows:

            writer.writerow([
                row[0],
                row[1],
                row[2],
                row[3] or "",
                row[4]
            ])

        csv_data = output.getvalue()

        return Response(

            csv_data,

            mimetype="text/csv",

            headers={
                "Content-Disposition":
                    "attachment; filename=expenses.csv"
            }

        )

    except Exception as error:

        print(
            "CSV EXPORT ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# EXPORT EXPENSES TO PDF
# =========================================================

@app.route(
    "/api/export/pdf",
    methods=["GET"]
)
@require_login
def export_pdf():

    try:

        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer
        )
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet

    except ImportError:

        return jsonify({
            "error":
                "PDF library not installed. Run: pip install reportlab"
        }), 500

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                amount,
                category,
                description,
                expense_date
            FROM expenses
            WHERE user_id = %s
            ORDER BY expense_date DESC
            """,
            (session["user_id"],)
        )

        rows = cursor.fetchall()

        buffer = io.BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4
        )

        styles = getSampleStyleSheet()

        story = []

        story.append(
            Paragraph(
                "Smart Expense Tracker",
                styles["Title"]
            )
        )

        story.append(
            Spacer(1, 12)
        )

        story.append(
            Paragraph(
                f"User: {session['username']}",
                styles["Normal"]
            )
        )

        story.append(
            Spacer(1, 12)
        )

        table_data = [
            [
                "ID",
                "Amount",
                "Category",
                "Description",
                "Date"
            ]
        ]

        for row in rows:

            table_data.append([
                str(row[0]),
                f"Rs. {float(row[1]):.2f}",
                row[2],
                row[3] or "",
                str(row[4])
            ])

        table = Table(
            table_data,
            repeatRows=1
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.grey
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.black
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                )
            ])
        )

        story.append(table)

        document.build(
            story
        )

        buffer.seek(0)

        return Response(

            buffer.getvalue(),

            mimetype="application/pdf",

            headers={
                "Content-Disposition":
                    "attachment; filename=expense_report.pdf"
            }

        )

    except Exception as error:

        print(
            "PDF EXPORT ERROR:",
            error
        )

        return jsonify({
            "error": str(error)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "ok",
        "application":
            "Smart Expense Tracker"
    })


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    if request.path.startswith("/api/"):

        return jsonify({
            "error":
                "API endpoint not found"
        }), 404

    return (
        "Page not found",
        404
    )


@app.errorhandler(500)
def internal_server_error(error):

    if request.path.startswith("/api/"):

        return jsonify({
            "error":
                "Internal server error"
        }), 500

    return (
        "Internal server error",
        500
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    initialize_database()

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )