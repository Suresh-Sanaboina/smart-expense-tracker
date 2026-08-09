import psycopg2
import os


def get_connection():

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    # Local development only
    return psycopg2.connect(
        host="localhost",
        database="smart_expense_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        port="5432"
    )


if __name__ == "__main__":

    connection = get_connection()

    print("Database connected successfully!")

    connection.close()