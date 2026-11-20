import mysql.connector


MENU = """
LIBRARY MANAGEMENT SYSTEM
1. Add Book
2. View All Books
3. Search / Locate Book
4. Issue Book
5. Return Book
6. View Issue Records
7. Remove Book
8. Exit"""


def initialise_database(connection, cursor):
    cursor.execute("SHOW DATABASES")
    if ("library_db",) not in cursor.fetchall():
        cursor.execute("CREATE DATABASE library_db")
    cursor.execute("USE library_db")

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    if ("books",) in tables and ("issue_records",) in tables:
        return True
    if tables:
        print("Setup error: the database must contain both books and issue_records, or be empty.")
        return False

    cursor.execute("""
        CREATE TABLE books (
            book_id INT PRIMARY KEY,
            title VARCHAR(200) NOT NULL UNIQUE,
            author VARCHAR(120) NOT NULL,
            category VARCHAR(60) NOT NULL,
            rack VARCHAR(20) NOT NULL,
            shelf VARCHAR(20) NOT NULL,
            status VARCHAR(10) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    sample_books = [
        (1, "Malgudi Days", "R. K. Narayan", "Fiction", "A", "1"),
        (2, "The Blue Umbrella", "Ruskin Bond", "Fiction", "A", "1"),
        (3, "The Diary of a Young Girl", "Anne Frank", "Memoir", "A", "2"),
        (4, "The Jungle Book", "Rudyard Kipling", "Fiction", "A", "2"),
        (5, "Wings of Fire", "A. P. J. Abdul Kalam and Arun Tiwari", "Memoir", "B", "1"),
        (6, "The Story of My Experiments with Truth", "M. K. Gandhi", "Memoir", "B", "1"),
        (7, "A Brief History of Time", "Stephen Hawking", "Science", "B", "2"),
        (8, "Cosmos", "Carl Sagan", "Science", "B", "2"),
        (9, "The Story of the World", "Susan Wise Bauer", "History", "C", "1"),
        (10, "Oxford School Dictionary", "Oxford Dictionaries", "Reference", "C", "2"),
    ]
    for book in sample_books:
        cursor.execute("""
            INSERT INTO books (book_id, title, author, category, rack, shelf, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Available')
        """, book)
    connection.commit()

    # Create the second table last so interrupted setup can be detected.
    cursor.execute("""
        CREATE TABLE issue_records (
            issue_id INT AUTO_INCREMENT PRIMARY KEY,
            book_id INT NOT NULL,
            student_name VARCHAR(120) NOT NULL,
            class_section VARCHAR(20) NOT NULL,
            issue_date DATE NOT NULL,
            return_date DATE,
            FOREIGN KEY (book_id) REFERENCES books (book_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("Library database set up with 10 sample books.")
    return True


def read_book_id():
    try:
        book_id = int(input("Book ID: "))
        if 1 <= book_id <= 2147483647:
            return book_id
    except ValueError:
        pass
    print("Enter a whole-number Book ID between 1 and 2147483647.")
    return None


def read_text(prompt, max_length):
    while True:
        value = input(prompt).strip()
        if value and len(value) <= max_length:
            return value
        print("Enter between 1 and", max_length, "characters.")


def valid_date(value):
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        return False
    digits = value[:4] + value[5:7] + value[8:]
    for digit in digits:
        if digit not in "0123456789":
            return False

    year = int(value[:4])
    month = int(value[5:7])
    day = int(value[8:])
    if year < 1000 or month < 1 or month > 12:
        return False

    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if year % 400 == 0 or (year % 4 == 0 and year % 100 != 0):
        month_lengths[1] = 29
    return 1 <= day <= month_lengths[month - 1]


def show_books(books):
    for book in books:
        book_id, title, author, category, rack, shelf, status = book
        print("\nBook ID:", book_id, "| Title:", title, "| Author:", author)
        print("Category:", category, "| Rack:", rack, "| Shelf:", shelf, "| Status:", status)


def add_book(cursor):
    book_id = read_book_id()
    if book_id is None:
        return
    title = read_text("Title: ", 200)

    cursor.execute("SELECT book_id FROM books WHERE book_id = %s OR title = %s", (book_id, title))
    if cursor.fetchall():
        print("A book with that ID or title already exists.")
        return

    author = read_text("Author: ", 120)
    category = read_text("Category: ", 60)
    rack = read_text("Rack number: ", 20)
    shelf = read_text("Shelf number: ", 20)
    cursor.execute("""
        INSERT INTO books (book_id, title, author, category, rack, shelf, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'Available')
    """, (book_id, title, author, category, rack, shelf))
    return "Book added successfully."


def view_all_books(cursor):
    cursor.execute("SELECT * FROM books ORDER BY book_id")
    books = cursor.fetchall()
    if books:
        show_books(books)
    else:
        print("The catalogue is empty.")


def search_book(cursor):
    choice = input("Search by 1. Book ID or 2. Title: ").strip()
    if choice == "1":
        book_id = read_book_id()
        if book_id is None:
            return
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
    elif choice == "2":
        title = read_text("Enter part of the title: ", 200)
        cursor.execute("SELECT * FROM books WHERE title LIKE %s ORDER BY book_id", ("%" + title + "%",))
    else:
        print("Choose 1 for Book ID or 2 for title.")
        return

    books = cursor.fetchall()
    if books:
        show_books(books)
    else:
        print("No matching books found.")


def issue_book(cursor):
    book_id = read_book_id()
    if book_id is None:
        return
    cursor.execute("SELECT status FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    if book is None:
        print("Book ID not found.")
        return
    if book[0] != "Available":
        print("This book is unavailable for issue. Current status:", book[0])
        return

    student_name = read_text("Student name: ", 120)
    class_section = read_text("Class and section: ", 20)
    issue_date = input("Issue date (YYYY-MM-DD): ").strip()
    if not valid_date(issue_date):
        print("Enter a valid issue date in YYYY-MM-DD format.")
        return

    cursor.execute("""
        INSERT INTO issue_records (book_id, student_name, class_section, issue_date)
        VALUES (%s, %s, %s, %s)
    """, (book_id, student_name, class_section, issue_date))
    cursor.execute("UPDATE books SET status = 'Issued' WHERE book_id = %s", (book_id,))
    return "Book issued successfully."


def return_book(cursor):
    book_id = read_book_id()
    if book_id is None:
        return
    cursor.execute("SELECT status FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    if book is None:
        print("Book ID not found.")
        return
    if book[0] != "Issued":
        print("Only an issued book can be returned. Current status:", book[0])
        return

    cursor.execute("""
        SELECT issue_id, issue_date FROM issue_records
        WHERE book_id = %s AND return_date IS NULL
    """, (book_id,))
    records = cursor.fetchall()
    if len(records) != 1:
        print("The book must have exactly one active issue record before it can be returned.")
        return
    issue_id, issue_date = records[0]

    return_date = input("Return date (YYYY-MM-DD): ").strip()
    if not valid_date(return_date):
        print("Enter a valid return date in YYYY-MM-DD format.")
        return
    # Dates in YYYY-MM-DD order can be compared as strings.
    if return_date < str(issue_date):
        print("The return date cannot be earlier than the issue date.")
        return

    cursor.execute("UPDATE issue_records SET return_date = %s WHERE issue_id = %s", (return_date, issue_id))
    cursor.execute("UPDATE books SET status = 'Available' WHERE book_id = %s", (book_id,))
    return "Book returned successfully."


def view_issue_records(cursor):
    cursor.execute("""
        SELECT issue_id, books.title, student_name, class_section, issue_date, return_date
        FROM issue_records JOIN books ON issue_records.book_id = books.book_id
        ORDER BY issue_id
    """)
    records = cursor.fetchall()
    if not records:
        print("There are no issue records.")
        return

    for record in records:
        issue_id, title, student_name, class_section, issue_date, return_date = record
        if return_date is None:
            return_date = "Not Returned"
        print("\nIssue ID:", issue_id, "| Book:", title)
        print("Student:", student_name, "| Class and section:", class_section)
        print("Issued:", issue_date, "| Returned:", return_date)


def remove_book(cursor):
    book_id = read_book_id()
    if book_id is None:
        return
    cursor.execute("SELECT title FROM books WHERE book_id = %s", (book_id,))
    book = cursor.fetchone()
    if book is None:
        print("Book ID not found.")
        return

    cursor.execute("SELECT COUNT(*) FROM issue_records WHERE book_id = %s", (book_id,))
    if cursor.fetchone()[0] > 0:
        print("This book cannot be removed because it has borrowing records.")
        return

    answer = input("Remove " + book[0] + "? (y/n): ").strip().lower()
    if answer != "y":
        print("Removal cancelled.")
        return
    cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
    return "Book removed successfully."


def run_menu(connection, cursor):
    while True:
        print(MENU)
        choice = input("Enter your choice: ").strip()
        message = None
        try:
            if choice == "1":
                message = add_book(cursor)
            elif choice == "2":
                view_all_books(cursor)
            elif choice == "3":
                search_book(cursor)
            elif choice == "4":
                message = issue_book(cursor)
            elif choice == "5":
                message = return_book(cursor)
            elif choice == "6":
                view_issue_records(cursor)
            elif choice == "7":
                message = remove_book(cursor)
            elif choice == "8":
                print("Goodbye.")
                break
            else:
                print("Enter a menu option from 1 to 8.")
                continue

            # Commit both writes for an issue or return before confirming success.
            connection.commit()
            if message is not None:
                print(message)
        except mysql.connector.Error as error:
            print("MySQL error:", error)
            connection.rollback()


def main():
    connection = None
    cursor = None
    try:
        username = input("MySQL username [root]: ").strip()
        if username == "":
            username = "root"
        password = input("MySQL password: ")
        connection = mysql.connector.connect(
            host="127.0.0.1", port=3306, user=username, password=password
        )
        cursor = connection.cursor()
        if initialise_database(connection, cursor):
            run_menu(connection, cursor)
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
