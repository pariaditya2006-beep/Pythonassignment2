import sqlite3
import random
import string
import os

# --- Configuration ---
DB_FILE = 'sqlite.db' 

# --- SQLite Setup ---
def init_db():
    """Initializes the SQLite database and the 'books' and 'borrowed' tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create the 'books' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            copies INTEGER NOT NULL
        )
    """)

    # Create the 'borrowed' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrowed (
            student_name TEXT PRIMARY KEY,
            book_id TEXT NOT NULL,
            FOREIGN KEY(book_id) REFERENCES books(book_id)
        )
    """)
    
    conn.commit()
    conn.close()

def generate_dummy_books(num=20):
    """Generates and inserts the requested 20 dummy books into the database if the DB is empty."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    print(f"Generating and adding {num} dummy books...")
    
    dummy_data = []
    
    for i in range(1, num + 1):
        book_id = f"DMBK{i:03d}"
        
        title_words = ['The', 'Amazing', 'Secret', 'Advanced', 'Fundamentals', 'Guide', 'Journey', 'Mystery']
        subject_words = ['Python', 'SQL', 'Data', 'Cyber', 'Networking', 'Cloud', 'Algorithms', 'Security']
        title = f"{random.choice(title_words)} of {random.choice(subject_words)}"
        
        author = ''.join(random.choices(string.ascii_uppercase, k=1)) + ". " + random.choice(['Smith', 'Jones', 'Kaushik', 'Kumar', 'Patel'])
        
        copies = random.randint(1, 10)
        
        dummy_data.append((book_id, title, author, copies))

    cursor.executemany(
        "INSERT INTO books (book_id, title, author, copies) VALUES (?, ?, ?, ?)",
        dummy_data
    )
    conn.commit()
    conn.close()
    print("Dummy data added successfully.")

# --- Task 1: Project Setup & Menu Screen ---
def display_menu():
    """Prints the welcome screen and menu options."""
    print("\n" + "="*40)
    print("=== 📚 Welcome to the Library Manager (SQLite) 📚 ===")
    print("="*40)
    print("\t1. Add Book")
    print("\t2. View Books")
    print("\t3. Search Book")
    print("\t4. Borrow Book")
    print("\t5. Return Book")
    print("\t6. Exit")
    print("-"*40)

# --- Task 2: Book Data Entry ---
def add_books():
    """Allows the user to input and store new book details in the DB."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print("\n-- Add New Book --")
    
    while True:
        try:
            book_id = input("Book ID: ").strip().upper()
            if not book_id:
                print("Book ID cannot be empty.")
                continue
            
            cursor.execute("SELECT book_id FROM books WHERE book_id = ?", (book_id,))
            if cursor.fetchone():
                print("Book ID already exists. Try a different ID.")
                continue
            
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            
            copies = int(input("Number of Copies: "))
            if copies < 0:
                 print("Copies must be non-negative.")
                 continue

            cursor.execute(
                "INSERT INTO books (book_id, title, author, copies) VALUES (?, ?, ?, ?)",
                (book_id, title, author, copies)
            )
            conn.commit()
            print(f"✅ Success: Book '{title}' added to the database.")
            
            more = input("Add another book? (y/n): ").lower()
            if more != "y":
                break
        
        except ValueError:
            print("❌ Invalid input for copies. Please enter a whole number.")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            break
            
    conn.close()

# --- Task 3: Display & Search Books (Unified) ---
def display_books():
    """Displays all books in a formatted tabular format from the DB."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT book_id, title, author, copies FROM books ORDER BY book_id")
    books = cursor.fetchall()
    conn.close()
    
    if not books:
        print("\nNo books in the library.")
        return
    
    print("\n--- Library Book List ---")
    print("{:<8} {:<30} {:<20} {:<7}".format("Book ID", "Title", "Author", "Copies"))
    print('-'*65)
    for bid, title, author, copies in books:
        print("{:<8} {:<30} {:<20} {:<7}".format(
            bid, title[:28], author[:18], copies
        ))
    print('-'*65)

def search_books():
    """
    Handles unified searching by Book ID (exact) or Title (substring, case-insensitive).
    This function replaces the previous choice prompt (1 or 2).
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print("\n-- Unified Search --")
    
    search_term = input("Enter Book ID (full) or Title keyword (partial): ").strip()
    if not search_term:
        print("Search term cannot be empty.")
        conn.close()
        return

    # SQL query to check both fields
    search_pattern = f'%{search_term}%'
    
    cursor.execute("""
        SELECT book_id, title, author, copies 
        FROM books 
        WHERE book_id = ? OR title LIKE ? COLLATE NOCASE
    """, (search_term.upper(), search_pattern))

    results = cursor.fetchall()
    conn.close()

    if results:
        print("\n📚 Books Found:")
        print("{:<8} {:<30} {:<20} {:<7}".format("Book ID", "Title", "Author", "Copies"))
        print('-'*65)
        for bid, title, author, copies in results:
            print("{:<8} {:<30} {:<20} {:<7}".format(
                bid, title[:28], author[:18], copies
            ))
        print('-'*65)
    else:
        print("❌ No matching books found.")

# --- Task 4: Borrowing System ---
def borrow_book():
    """Handles the book borrowing process using SQL transactions."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("\n-- Borrow Book --")
    student = input("Student Name: ").strip().title()
    book_id = input("Book ID: ").strip().upper()
    
    # 1. Check if the book exists and has copies
    cursor.execute(
        "SELECT title, copies FROM books WHERE book_id = ?", 
        (book_id,)
    )
    book_info = cursor.fetchone()

    if not book_info:
        print("❌ Error: Book ID not found.")
        conn.close()
        return

    title, copies = book_info

    # 2. Check if student has already borrowed a book
    cursor.execute(
        "SELECT book_id FROM borrowed WHERE student_name = ?", 
        (student,)
    )
    if cursor.fetchone():
        print(f"❌ Error: {student} has already borrowed a book. Must return first.")
        conn.close()
        return

    # 3. Check for available copies
    if copies < 1:
        print("❌ Error: No copies available right now.")
        conn.close()
        return
        
    try:
        # TRANSACTION START
        # Reduce available copies
        cursor.execute(
            "UPDATE books SET copies = copies - 1 WHERE book_id = ?", 
            (book_id,)
        )
        # Store borrowing info
        cursor.execute(
            "INSERT INTO borrowed (student_name, book_id) VALUES (?, ?)", 
            (student, book_id)
        )
        conn.commit()
        print(f"✅ Success: Book '{title}' borrowed successfully by {student}.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Transaction failed: {e}")
    finally:
        conn.close()


# --- Task 5: Return Book + List Comprehension ---
def return_book():
    """Handles the book return process and displays borrowed list."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("\n-- Return Book --")
    student = input("Student Name: ").strip().title()
    book_id = input("Book ID: ").strip().upper()

    # Check if the correct student/book record exists
    cursor.execute(
        "SELECT book_id FROM borrowed WHERE student_name = ? AND book_id = ?", 
        (student, book_id)
    )
    if not cursor.fetchone():
        print("❌ Error: No matching borrowing record found for that student and Book ID.")
        conn.close()
        return
    
    try:
        # TRANSACTION START
        # Increase copies
        cursor.execute(
            "UPDATE books SET copies = copies + 1 WHERE book_id = ?", 
            (book_id,)
        )
        # Remove borrowing entry
        cursor.execute(
            "DELETE FROM borrowed WHERE student_name = ?", 
            (student,)
        )
        conn.commit()
        print(f"✅ Success: Book returned successfully by {student}.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Transaction failed: {e}")
    
    # List all currently borrowed books using list comprehension
    cursor.execute("""
        SELECT 
            b.student_name, b.book_id, k.title 
        FROM borrowed b
        JOIN books k ON b.book_id = k.book_id
    """)
    borrowed_records = cursor.fetchall()
    conn.close()
    
    # List comprehension to display borrowed books (Task 5 requirement)
    borrowed_list = [
        f"{stud} -> {bkid} (Book: {title})" 
        for stud, bkid, title in borrowed_records
    ]
    
    print("\n--- Current Borrowed Books ---")
    if borrowed_list:
        print('\n'.join(borrowed_list))
    else:
        print("No books have been borrowed.")
    print("-" * 30)

# --- Task 6: User Loop & Exit ---
def main():
    """Main function to run the library manager application."""
    
    # Setup the database
    init_db()
    
    # Add 20 dummy books if the DB is empty
    generate_dummy_books(20)
    
    # Main program loop
    while True:
        display_menu()
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == "1":
            add_books()
        elif choice == "2":
            display_books()
        elif choice == "3":
            search_books()
        elif choice == "4":
            borrow_book()
        elif choice == "5":
            return_book()
        elif choice == "6":
            print("\nExiting the Library Manager. Goodbye! 👋\n")
            break
        else:
            print("❌ Invalid choice, please enter a number from 1 to 6.")

if __name__ == "__main__":
    main()