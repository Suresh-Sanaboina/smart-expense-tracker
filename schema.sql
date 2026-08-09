CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    category VARCHAR(50) NOT NULL,
    description VARCHAR(255),
    expense_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    month VARCHAR(7) NOT NULL,
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, month)
);


CREATE TABLE IF NOT EXISTS income (
    id SERIAL PRIMARY KEY,
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    source VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    income_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_expenses_user_id
ON expenses(user_id);

CREATE INDEX IF NOT EXISTS idx_expenses_date
ON expenses(expense_date);

CREATE INDEX IF NOT EXISTS idx_income_user_id
ON income(user_id);

CREATE INDEX IF NOT EXISTS idx_income_date
ON income(income_date);

CREATE INDEX IF NOT EXISTS idx_budgets_user_month
ON budgets(user_id, month);