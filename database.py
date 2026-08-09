import psycopg2
import os


def get_connection():

    connection = psycopg2.connect(
        host="localhost",
        database="smart_expense_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        port="5432"
    )

    return connection


if __name__ == "__main__":

    connection = get_connection()

    print("Database connected successfully!")

    connection.close()