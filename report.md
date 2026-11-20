# Library Management System — Phase 2 Verification Report

## A. Environment

**Live MySQL verification succeeded.** All seven operations worked in their normal workflows. Title searches containing `%` or `_` returned extra matches.

| Component | Result |
|---|---|
| Python | 3.12.10 |
| MySQL Server | 8.0.46 on the existing Windows service |
| MySQL Connector/Python | 26.10.0, installed for Python 3.12 |
| Disposable databases | `libraryverifye68636cd95c7a` for the main suite, `libraryverifye68636cd95c7b` for the empty catalogue, and `libraryverifye68636cd95c7c` and `libraryverifye68636cd95c7d` for incomplete setup |
| Isolation and cleanup | The temporary account had access only to the test schemas for application data. All four schemas and the account were removed. The SHA-256 hash of `main.py` matched before and after verification, and it remained the sole application file. |

## B. Test Results

Source inspection confirmed that startup prompts for credentials and uses `SHOW DATABASES` and `SHOW TABLES` to decide whether to initialize. Add, view, and search use parameterized lookups, an `INSERT`, and `LIKE`. Issue inserts the loan and updates availability. Return updates the loan and availability. The menu commits both writes together or rolls them back on a MySQL error. Borrowing history uses a join, and removal checks for history before `DELETE`. The input helpers validate IDs, required text, and calendar dates. A `finally` block closes the cursor and connection.

| Test category | Scenario | Result | Observation |
|---|---|---|---|
| Syntax only | Compile `main.py` under Python 3.12 | PASS | Compilation succeeded. |
| Live MySQL · Setup | Fresh database, schema, sample data, menu and exit | PASS | Both InnoDB tables, primary keys, unique title, and foreign key were present. All ten sample rows matched the source. |
| Live MySQL · Startup recovery | Restart, empty catalogue, and either table missing | PASS | Existing rows survived. The empty catalogue stayed empty. Each incomplete schema produced a setup error and preserved its surviving table and data. |
| Live MySQL · A. Add Book | Valid insert, duplicates, blanks, and invalid IDs | PASS | SQL confirmed the inserted row. Duplicate IDs and case-variant titles were rejected. Blank fields were re-prompted. Letters, zero, negative, and out-of-range IDs were handled. |
| Live MySQL · B. View All Books | Catalogue fields, availability, and empty output | PASS | Displayed details matched MySQL, including `Available` and `Issued` statuses. An empty catalogue produced the expected message. |
| Live MySQL · C. Search / Locate | ID, title, partial and case-insensitive searches, location, and missing results | PASS | The expected books, racks, and shelves were shown. Missing results produced a clear message. |
| Live MySQL · C. Search / Locate | Literal searches containing `%` or `_` | FAIL | `100%` also matched `1000 Atlas`, and `A_B` also matched `AXB Atlas`. |
| Live MySQL · D. Issue Book | Valid, repeated, and nonexistent issues, plus date validation | PASS | SQL confirmed the student, class, issue date, and `Issued` status. Invalid formats, impossible dates, and non-leap February dates were rejected. Valid leap days were accepted. |
| Live MySQL · E. Return Book | Same-day, earlier, invalid, repeated, and nonexistent returns | PASS | SQL confirmed the same-day return, restored availability, and preserved the borrowing record. Invalid attempts left the loan unchanged. |
| Live MySQL · F. View Issue Records | Active and returned loans | PASS | Each loan showed the correct book and student. Active loans showed `Not Returned`, and closed loans showed their return dates. |
| Live MySQL · G. Remove Book | Confirm, cancel, missing ID, and borrowing history | PASS | SQL confirmed deletion of an eligible book and preservation after cancellation. Both active and historical loans prevented deletion. |
| Live MySQL · Transactions | Force the second write to fail during issue and return | PASS | MySQL rejected each status update. Direct queries confirmed rollback of the preceding loan insert or return-date update. |
| Live MySQL · Persistence | Add, issue, restart, return, and restart again | PASS | Separate Python processes saw the saved book, open loan, completed return, and updated availability. |
| Live MySQL · Menu validation | Invalid menu and search choices | PASS | The program displayed guidance and continued without an unhandled exception. |

The database results above came from live MySQL. Earlier in-memory results were excluded from this assessment.

## C. Problems Found

**Literal title searches can return unrelated books.** In `search_book`, lines 162–164 place the entered text directly inside a `LIKE` pattern. MySQL interprets `%` and `_` as wildcards, which broadens the results when either character is meant literally. A small correction is to escape the chosen escape character, `%`, and `_` with `str.replace()`, then use an explicit `ESCAPE` clause while keeping the pattern parameterized. [Source at main.py line 164](D:/Tech/Library/main.py:164) · [MySQL `LIKE` documentation](https://dev.mysql.com/doc/refman/8.0/en/string-comparison-functions.html#operator_like)

## D. Database Integrity

Live tests confirmed safe initialization in the tested fresh, complete, and incomplete states. Catalogue records and borrowing history survived restarts. Issue and return each rolled back cleanly when the second write failed, and removal respected both active and historical loans.

## E. Final Assessment

**CONDITIONAL PASS — Minor corrections recommended.** The normal workflows and database integrity checks passed on live MySQL. The remaining finding is limited to literal title searches containing wildcard characters.
