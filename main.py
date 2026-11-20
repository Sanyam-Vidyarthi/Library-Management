import mysql.connector


def setup_database(connection, cursor):
    cursor.execute("SHOW DATABASES")
    if ("library_simple_db",) not in cursor.fetchall():
        cursor.execute("CREATE DATABASE library_simple_db")
    cursor.execute("USE library_simple_db")

    cursor.execute("SHOW FULL TABLES")
    tables = cursor.fetchall()
    if tables:
        if tables != [("books", "BASE TABLE")]:
            print("Setup error: library_simple_db must contain only the books table.")
            return False

        cursor.execute("SHOW FULL COLUMNS FROM books")
        expected_columns = [
            ("book_id", "int", None, "NO", "PRI"),
            ("title", "varchar(200)", "utf8mb4_unicode_ci", "NO", "UNI"),
            ("author", "varchar(120)", "utf8mb4_unicode_ci", "NO", ""),
            ("category", "varchar(60)", "utf8mb4_unicode_ci", "NO", ""),
            ("status", "varchar(10)", "utf8mb4_unicode_ci", "NO", ""),
            ("issued_to", "varchar(120)", "utf8mb4_unicode_ci", "YES", ""),
        ]
        columns = []
        for row in cursor.fetchall():
            # The first five values give the name, type, collation, nullability and key.
            columns.append(row[:5])
        if columns != expected_columns:
            print("Setup error: the books table has a different structure.")
            return False
        return True

    cursor.execute("""
        CREATE TABLE books (
            book_id INT PRIMARY KEY,
            title VARCHAR(200) NOT NULL UNIQUE,
            author VARCHAR(120) NOT NULL,
            category VARCHAR(60) NOT NULL,
            status VARCHAR(10) NOT NULL,
            issued_to VARCHAR(120)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    sample_books = [
        (1, "Malgudi Days", "R. K. Narayan", "Fiction"),
        (2, "The Blue Umbrella", "Ruskin Bond", "Fiction"),
        (3, "The Diary of a Young Girl", "Anne Frank", "Memoir"),
        (4, "The Jungle Book", "Rudyard Kipling", "Fiction"),
        (5, "Wings of Fire", "A. P. J. Abdul Kalam and Arun Tiwari", "Memoir"),
        (6, "The Story of My Experiments with Truth", "M. K. Gandhi", "Memoir"),
        (7, "A Brief History of Time", "Stephen Hawking", "Science"),
        (8, "Cosmos", "Carl Sagan", "Science"),
        (9, "The Story of the World", "Susan Wise Bauer", "History"),
        (10, "Oxford School Dictionary", "Oxford Dictionaries", "Reference"),
    ]
    for book in sample_books:
        cursor.execute("""
            INSERT INTO books (book_id, title, author, category, status, issued_to)
            VALUES (%s, %s, %s, %s, 'Available', NULL)
        """, book)
    connection.commit()
    print("Library database set up with 10 sample books.")
    return True


def add_book(cursor):
    title = input("Title: ").strip()
    author = input("Author: ").strip()
    category = input("Category: ").strip()
    if not title or not author or not category:
        print("Title, author and category are required.")
        return

    cursor.execute("SELECT book_id FROM books WHERE title = %s", (title,))
    if cursor.fetchone() is not None:
        print("A book with that title already exists.")
        return

    cursor.execute("SELECT MAX(book_id) FROM books")
    highest_id = cursor.fetchone()[0]
    if highest_id is None:
        highest_id = 0
    if highest_id == 2147483647:
        print("The next Book ID is too large for MySQL.")
        return
    book_id = highest_id + 1

    cursor.execute("""
        INSERT INTO books (book_id, title, author, category, status, issued_to)
        VALUES (%s, %s, %s, %s, 'Available', NULL)
    """, (book_id, title, author, category))
    return "Book added successfully. Book ID: " + str(book_id)


def view_all_books(cursor):
    cursor.execute("SELECT * FROM books ORDER BY book_id")
    books = cursor.fetchall()
    if not books:
        print("The catalogue is empty.")
        return

    for book_id, title, author, category, status, issued_to in books:
        print(book_id, "|", title, "|", author, "|", category, "|", status)
        if status == "Issued":
            print("Issued to:", issued_to)


def search_book(cursor, highest_id):
    choice = input("Search by 1. Book ID or 2. Title: ").strip()
    if choice == "1":
        if highest_id == 0:
            print("The catalogue is empty.")
            return
        book_id = int(input("Book ID (1 to " + str(highest_id) + "): "))
        if not 1 <= book_id <= highest_id:
            print("Enter a Book ID from 1 to", highest_id)
            return
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
    elif choice == "2":
        title = input("Enter part of the title: ").strip()
        if not title:
            print("Enter a title to search for.")
            return
        cursor.execute("SELECT * FROM books WHERE title LIKE %s ORDER BY book_id", ("%" + title + "%",))
    else:
        print("Choose 1 for Book ID or 2 for title.")
        return

    books = cursor.fetchall()
    if not books:
        print("No matching books found.")
        return
    for book_id, title, author, category, status, issued_to in books:
        print(book_id, "|", title, "|", author, "|", category, "|", status)
        if status == "Issued":
            print("Issued to:", issued_to)


def issue_book(cursor, highest_id):
    book_id = int(input("Book ID (1 to " + str(highest_id) + "): "))
    if not 1 <= book_id <= highest_id:
        print("Enter a Book ID from 1 to", highest_id)
        return

    cursor.execute("SELECT status FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    if book is None:
        print("Book ID not found.")
        return
    if book[0] != "Available":
        print("This book is already issued.")
        return

    student_name = input("Student name: ").strip()
    if not student_name:
        print("Student name is required.")
        return

    cursor.execute("UPDATE books SET status = 'Issued', issued_to = %s WHERE book_id = %s", (student_name, book_id))
    return "Book issued successfully."


def return_book(cursor, highest_id):
    book_id = int(input("Book ID (1 to " + str(highest_id) + "): "))
    if not 1 <= book_id <= highest_id:
        print("Enter a Book ID from 1 to", highest_id)
        return

    cursor.execute("SELECT status FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    if book is None:
        print("Book ID not found.")
        return
    if book[0] != "Issued":
        print("This book is already available.")
        return

    cursor.execute("UPDATE books SET status = 'Available', issued_to = NULL WHERE book_id = %s", (book_id,))
    return "Book returned successfully."


def remove_book(cursor, highest_id):
    book_id = int(input("Book ID (1 to " + str(highest_id) + "): "))
    if not 1 <= book_id <= highest_id:
        print("Enter a Book ID from 1 to", highest_id)
        return

    cursor.execute("SELECT title, status FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    if book is None:
        print("Book ID not found.")
        return
    title, status = book
    if status != "Available":
        print("An issued book must be returned before it can be removed.")
        return

    answer = input("Remove " + title + "? (Y/N): ").strip().lower()
    if answer != "y":
        print("Removal cancelled.")
        return

    cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
    return "Book removed successfully."


def main():
    connection = None
    cursor = None
    try:
        username = input("MySQL username [root]: ").strip()
        if not username:
            username = "root"
        password = input("MySQL password: ")
        connection = mysql.connector.connect(
            host="127.0.0.1", port=3306, user=username, password=password
        )
        cursor = connection.cursor()
        if not setup_database(connection, cursor):
            return

        while True:
            print("""
LIBRARY MANAGEMENT SYSTEM
1. Add Book
2. View All Books
3. Search Book
4. Issue Book
5. Return Book
6. Remove Book
7. Exit""")
            choice = input("Enter your choice: ").strip()
            message = None
            try:
                if choice in ("3", "4", "5", "6"):
                    cursor.execute("SELECT MAX(book_id) FROM books")
                    highest_id = cursor.fetchone()[0]
                    if highest_id is None:
                        highest_id = 0

                if choice == "1":
                    message = add_book(cursor)
                elif choice == "2":
                    view_all_books(cursor)
                elif choice == "3":
                    search_book(cursor, highest_id)
                elif choice in ("4", "5", "6") and highest_id == 0:
                    print("The catalogue is empty.")
                elif choice == "4":
                    message = issue_book(cursor, highest_id)
                elif choice == "5":
                    message = return_book(cursor, highest_id)
                elif choice == "6":
                    message = remove_book(cursor, highest_id)
                elif choice == "7":
                    print("Goodbye.")
                    break
                else:
                    print("Enter a menu option from 1 to 7.")
                    continue

                # Save changes before printing a success message.
                connection.commit()
                if message is not None:
                    print(message)
            except ValueError:
                print("Enter a positive whole-number Book ID.")
                connection.rollback()
            except mysql.connector.Error as error:
                connection.rollback()
                print("MySQL error:", error)
    except mysql.connector.Error as error:
        print("Unable to continue with MySQL:", error)
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye.")
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
