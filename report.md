# Library Management System — Verification Report

## A. Application and environment

The simplified CBSE Class XII project is a 269-line Python program with six operations. It was verified against live MySQL using Python 3.12.10, MySQL Server 8.0.46, and MySQL Connector/Python 26.10.0.

Run the program with:

~~~powershell
py -3.12 main.py
~~~

Enter the username and password for your local MySQL server. First-run setup requires permission to create the database and table and insert the sample rows.

## B. Database design

The application uses the database `library_simple_db` and one InnoDB table named `books`.

| Column | MySQL definition |
|---|---|
| `book_id` | `INT PRIMARY KEY` |
| `title` | `VARCHAR(200)`, required and unique, with case-insensitive comparison |
| `author` | `VARCHAR(120)`, required |
| `category` | `VARCHAR(60)`, required |
| `status` | `VARCHAR(10)`, required |
| `issued_to` | `VARCHAR(120)`, nullable |

First-run setup creates the table and inserts ten sample books as `Available`, with a `NULL` borrower. Later launches preserve the existing rows and keep an intentionally empty catalogue empty. Unexpected tables or incompatible columns result in a setup error.

## C. Live MySQL test results

| Scenario | Result | Observation |
|---|---|---|
| First launch and restart | PASS | MySQL contained one table and exactly ten sample books. Restarting preserved the original rows without reseeding. |
| Add Book | PASS | Verified insertion and rejection of invalid IDs, blank fields, duplicate IDs, and case-variant duplicate titles. An oversized value produced a handled MySQL error and left the catalogue intact. |
| View All Books | PASS | Displayed catalogue details, availability, and the borrower for an issued book. An empty catalogue displayed a message. |
| Search Book | PASS | Found books by exact ID and by full or partial title, including case variations. Handled missing matches and invalid input. |
| Issue Book | PASS | Set the status to `Issued` and saved the borrower. Rejected blank borrower names, repeat issues, and missing books. The status and borrower survived a restart. |
| Return Book | PASS | Set the status to `Available` and cleared the borrower to SQL `NULL`. Rejected repeat returns and missing books. Both saved values survived a restart. |
| Remove Book | PASS | Blocked removal of an issued book. Cancellation preserved the row, and confirmation removed the available book. |
| Setup safeguards | PASS | An empty catalogue stayed empty. Unexpected tables and incompatible columns triggered setup errors and preserved the existing rows. |
| Menu and source checks | PASS | Invalid menu choices were handled, option 7 exited, and Python compilation succeeded. |

Title search uses standard SQL `LIKE` behaviour. The characters `%` and `_` act as wildcards.

## D. Isolation and assessment

Live tests ran against disposable schemas with a temporary account restricted to those schemas. The schemas and account were removed after verification. All test writes were confined to those schemas, so the original `library_db` and its borrowing history were safe.

**PASS — The six simplified workflows passed live MySQL verification.** The previous two-table implementation is recoverable at commit `7534726`.
