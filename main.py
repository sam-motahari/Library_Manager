# This program is capable of managing library activities such as lending and returning books, checking
# the status of books or members, and adding new books or members to the database.

import tkinter as tk
import tkinter.ttk as ttk
import sqlite3
from datetime import date
from tkinter import BOTH, YES, NO, E, W
from tkinter import messagebox
import re
# connect to database, if it doesn't exist it will be created
conn = sqlite3.connect('library.db')
c = conn.cursor()

# create a table for books with columns: id, title, is_available
c.execute('''CREATE TABLE IF NOT EXISTS books
             (id INTEGER PRIMARY KEY,
             title TEXT,
             is_available BOOLEAN DEFAULT true)''')
# create a table for members with columns: id, name, phone number and email
c.execute('''CREATE TABLE IF NOT EXISTS members
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             fname TEXT NOT NULL,
             lname TEXT NOT NULL,
             phone TEXT,
             email TEXT NOT NULL UNIQUE)''')
# create a table to keep a record of books which are lent.
c.execute('''CREATE TABLE IF NOT EXISTS out_books
             (event_id INTEGER PRIMARY KEY AUTOINCREMENT,
              book_id INTEGER,
              member_id INTEGER,
              date_lended DATE,
              date_returned DATE DEFAULT NULL)''')
conn.commit()
conn.close()

# Create window
root = tk.Tk()
root.title('Kingston Library')
root.geometry("500x600")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

def print_message(message):
    new_messagebox = tk.Tk()
    new_messagebox.withdraw()
    messagebox.showinfo("Message", message)

# create Lending tab
def clear_entry(entrys):
    for entry in entrys:
        entry.delete(0, tk.END)

def lend_book(book_id, email, date_lended):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT id From books WHERE id=?", (book_id,))
    does_exist= c.fetchone()
    if does_exist is None:
        print_message("The book does not exist")
        conn.close()
        return

    c.execute("SELECT id From members WHERE email=?", (email,))
    member_id = c.fetchone()
    if member_id is None:
        print_message("The person does not exist")
        conn.close()
        return
    c.execute("SELECT is_available From books WHERE id=?", (book_id,))
    available= c.fetchone()
    #print (available)
    if available[0]==0:
        print_message("The book is not available now")
        conn.close()
        return
    try:
        c = conn.cursor()
        c.execute("INSERT INTO out_books (book_id, member_id, date_lended) VALUES (?, ?, ?)", (book_id, int(member_id[0]), date_lended))
        c.execute("UPDATE books SET is_available = false WHERE id = ?", (book_id,))
        conn.commit()
        print_message("Book is lent.")
    except sqlite3.Error as e:
        print_message(f"Error: , {e}")
        conn.rollback()
    finally:
        conn.close()


def return_book(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT id From books WHERE id=?", (book_id,))
    does_exist = c.fetchone()
    if does_exist is None:
        print_message("The book does not exist")
        conn.close()
        return
    c.execute("SELECT is_available From books WHERE id=?", (book_id,))
    available = c.fetchone()
    if available[0] == 1:
        print_message("The book is already in the libray!")
        conn.close()
        return
    try:
        c = conn.cursor()

        c.execute("UPDATE books SET is_available = true WHERE id = ?", (book_id,))
        c.execute("UPDATE out_books SET date_returned= date('now') WHERE book_id = ?", (book_id,))
        conn.commit()
        print_message("Book is returned")
    except sqlite3.Error as e:
        print_message(f"Error: , {e}")
        conn.rollback()
    finally:
        conn.close()


lend_tab = ttk.Frame(notebook)
notebook.add(lend_tab, text="Lending")

lend_frame = ttk.LabelFrame(lend_tab, text="Lending Books")
lend_frame.grid(row=0, column=0, padx=50, pady=50, sticky="w")

book_id_label = ttk.Label(lend_frame, text="Enter book ID:")
book_id_label.grid(row=0, column=0, padx=5, pady=5)
book_id_entry = ttk.Entry(lend_frame, width=20)
book_id_entry.grid(row=0, column=1, padx=5, pady=5)

borrower_email_label = ttk.Label(lend_frame, text="Enter borrower email:")
borrower_email_label.grid(row=1, column=0, padx=5, pady=5)
borrower_email_entry = ttk.Entry(lend_frame, width=20)
borrower_email_entry.grid(row=1, column=1, padx=5, pady=5)

lend_button = ttk.Button(lend_frame, text="Lend", width=10, command=lambda: lend_book(book_id_entry.get(),borrower_email_entry.get(),date.today()))
lend_button.grid(row=2, column=0, padx=5, pady=5)
cancel_button = ttk.Button(lend_frame, text="Cancel", width=10, command=lambda: clear_entry([borrower_email_entry,book_id_entry]))
cancel_button.grid(row=2, column=1, padx=5, pady=5)

return_frame = ttk.LabelFrame(lend_tab, text="Returning Books")
return_frame.grid(row=1, column=0, padx=50, pady=50, sticky="w")

return_id_label = ttk.Label(return_frame, text="Enter book ID:")
return_id_label.grid(row=0, column=0, padx=5, pady=5)
return_id_entry = ttk.Entry(return_frame, width=20)
return_id_entry.grid(row=0, column=1, padx=5, pady=5)

return_button = ttk.Button(return_frame, text="Return", width=10, command=lambda: return_book(return_id_entry.get()))
return_button.grid(row=1, column=0, padx=5, pady=5)
return_cancel_button = ttk.Button(return_frame, text="Cancel", width=10, command=lambda: clear_entry([return_id_entry]))
return_cancel_button.grid(row=1, column=1, padx=5, pady=5)

# create Checking status tab
def check_status(book_id):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT * From books WHERE id=?", (book_id,))
    my_book = c.fetchone()
    if my_book is None:
        print_message("The book does not exist")
        conn.close()
        return
    if my_book[2]:          # means the book is in the library
        print_message(str (my_book[0])+"    "+my_book[1]+" is available.")
    else :
        c.execute("SELECT out_books.date_lended, members.fname, members.lname FROM out_books JOIN members "
                  "ON out_books.member_id = members.id WHERE out_books.book_id=? AND out_books.date_returned IS NULL",
                  (book_id,))
        date_person = c.fetchone()
        print_message(str (my_book[0])+"    "+my_book[1]+" has been borrowed by "+date_person[1]+" "+date_person[2]+" on "+str(date_person[0]))
    conn.close()
    return

def check_member_status(email):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT id, fname, lname From members WHERE email=?", (email,))
    my_member = c.fetchone()

    if my_member is None:
        print_message("There is no one with this ID")
    else:
        member_id = my_member[0]
        c.execute(
            "SELECT books.title, out_books.date_lended FROM books JOIN out_books ON books.id = out_books.book_id "
            "WHERE out_books.member_id = ? AND out_books.date_returned IS NULL", (member_id,))
        books_titles = c.fetchall()
        msg = f"{my_member[1]} {my_member[2]} has borrowed:\n"
        if books_titles:
            for book_title in books_titles:
                msg = msg + f"{book_title[0]} on {book_title[1]}\n"
        else:
            msg = msg + " No books"
        print_message(msg)
    conn.close()


def search_book(title):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT id, title, is_available FROM books WHERE title LIKE ?", ('%'+title+'%',))
    books = c.fetchall()
    message = ""
    if books:
        for book in books:
            if book[2]:
                yes_no = "Yes"
            else:
                yes_no = "No"
            message = message + f"Book ID: {book[0]}, Title: {book[1]}, Available: {yes_no}\n"
        print_message(message)
    else:
        print_message("No books found with that title.")
    conn.close()


def check_member_status_by_lname(lastname):
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT members.fname, members.lname, members.phone, members.email FROM members "
              "WHERE members.lname LIKE ? ",('%'+lastname+'%',),)
    full_names = c.fetchall()
    full_names = set(full_names)
    if not full_names:
        print_message("The person is not found!")
        conn.close()
        return
    message = ""
    for full_name in full_names:
        c.execute("SELECT books.title, out_books.date_lended "
                  "FROM books "
                   "JOIN out_books ON books.id = out_books.book_id "
                   "JOIN members ON members.id = out_books.member_id "
                   "WHERE members.email= ? AND out_books.date_returned IS NULL", (full_name[3],))

        results = c.fetchall()
        if not results:
            message = message + f"{full_name[0]} {full_name[1]} ({full_name[2]}" \
                                f" , {full_name[3]}) has borrowed: No books.\n"
        else:
            message = message + f"{full_name[0]} {full_name[1]} ({full_name[2]}" \
                                f" , {full_name[3]}) has borrowed:\n"
            for result in results:
                message = message + f"{result[0]} on {result[1]}\n"
    print_message(message)

    conn.close()


status_tab = ttk.Frame(notebook)
notebook.add(status_tab, text="Checking Status")

status_frame = ttk.LabelFrame(status_tab, text="Checking Book Status")
status_frame.grid(row=0, column=0, padx=50, pady=50, sticky="w")

status_book_id_label = ttk.Label(status_frame, text="Enter book ID:")
status_book_id_label.grid(row=0, column=0, padx=5, pady=5)
status_book_id_entry = ttk.Entry(status_frame, width=20)
status_book_id_entry.grid(row=0, column=1, padx=5, pady=5)

status_go_button = ttk.Button(status_frame, text="Go", width=10, command=lambda:check_status(status_book_id_entry.get()))
status_go_button.grid(row=1, column=0, padx=5, pady=5)

status_clear_button = ttk.Button(status_frame, text="Clear", width=10, command=lambda : clear_entry([status_book_id_entry]))
status_clear_button.grid(row=1, column=1, padx=5, pady=5)

search_label = ttk.Label(status_frame, text="Search books by any word in title:")
search_label.grid(row=2, column=0, padx=5, pady=5)
title_label = ttk.Label(status_frame, text="Enter book title:")
title_label.grid(row=3, column=0, padx=5, pady=5)
title_entry = ttk.Entry(status_frame, width=20)
title_entry.grid(row=3, column=1, padx=5, pady=5)
search_books_button = ttk.Button(status_frame, text="Go", width=10, command=lambda: search_book(title_entry.get()))
search_books_button.grid(row=4, column=0, padx=5, pady=5)
clear_search_button = ttk.Button(status_frame, text="Clear" , width=10 , command=lambda: clear_entry([title_entry]))
clear_search_button.grid(row=4, column=1, padx=5, pady=5)
status_member_frame = ttk.LabelFrame(status_tab, text="Checking Member Status")
status_member_frame.grid(row=1, column=0, padx=50, pady=50, sticky="w")

status_member_email_label = ttk.Label(status_member_frame, text="Enter member email:")
status_member_email_label.grid(row=0, column=0, padx=5, pady=5)
status_member_email_entry = ttk.Entry(status_member_frame, width=20)
status_member_email_entry.grid(row=0, column=1, padx=5, pady=5)
status_member_go_button = ttk.Button(status_member_frame, text="Go", width=10, command=lambda: check_member_status(status_member_email_entry.get()))
status_member_go_button.grid(row=1, column=0, padx=5, pady=5)
status_member_clear_button = ttk.Button(status_member_frame, text="Clear", width=10, command=lambda: clear_entry([status_member_email_entry]))
status_member_clear_button.grid(row=1, column=1, padx=5, pady=5)

status_member_lname_label = ttk.Label(status_member_frame, text=" OR enter member last name:")
status_member_lname_label.grid(row=2, column=0, padx=5, pady=5)
status_member_lname_entry = ttk.Entry(status_member_frame, width=20)
status_member_lname_entry.grid(row=2, column=1, padx=5, pady=5)
status_member_by_lname_go_button = ttk.Button(status_member_frame, text="Go", width=10, command=lambda :check_member_status_by_lname(status_member_lname_entry.get()))
status_member_by_lname_go_button.grid(row=3, column=0, padx=5, pady=5)
status_member_by_lname_clear_button = ttk.Button(status_member_frame, text="Clear", width=10, command=lambda :clear_entry([status_member_lname_entry]))
status_member_by_lname_clear_button.grid(row=3, column=1, padx=5, pady=5)



# create Adding tab to Add new book or member

def add_book(book_id, title):
    if not book_id.isnumeric():
        print_message("Book ID must be an integer and unique value!")
        return
    if not title:
        print_message("Book title can not be blank!")
        return
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO books (id,title) VALUES (?, ?)", (book_id, title))
        conn.commit()
        conn.close()
        print_message("Book added successfully!")
    except:         #    sqlite3.Error as e:
                    #    print("Error: ", e)
        print_message(f"Failed to add the book because a book with the ID {book_id} is already existed in the database.")
        conn.rollback()
    finally:
        conn.close()


def add_member(fname, lname, phone, email):
    if not all([fname, lname, email]):
        print_message("Failed to add: First name, last name and email can not be blank!")
        return
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    if not re.match(pattern, email):
        print_message("Invalid email address")
        return
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    c.execute("SELECT members.email FROM members WHERE members.email = ?", (email,))
    person_email = c.fetchone()
    if person_email:
        print_message(f"{email} is already existed in the database!")
        conn.close()
        return
    c.execute("INSERT INTO members (fname, lname, phone, email) VALUES (?, ?,? ,?)", (fname, lname, phone, email))
    conn.commit()
    conn.close()
    print_message(fname + " "+lname +" is added successfully!")

add_tab = ttk.Frame(notebook)
notebook.add(add_tab, text="Adding New Books or Members")

Add_book_frame = ttk.LabelFrame(add_tab, text="Adding new book to library")
Add_book_frame.grid(row=0, column=0, padx=50, pady=50, sticky="w")
Add_member_frame = ttk.LabelFrame(add_tab, text="Adding new member to library")
Add_member_frame.grid(row=1, column=0, padx=50, pady=(0, 50), sticky="w")

label20 = ttk.Label(Add_book_frame, text="Enter book ID: ")
label21 = ttk.Label(Add_book_frame, text="Enter book title: ")
Book_ID_Entry = ttk.Entry(Add_book_frame, width=10)
Book_Title_Entry = ttk.Entry(Add_book_frame, width=25)

label20.grid(row=0, column=0)
label21.grid(row=1, column=0)
Book_ID_Entry.grid(row=0, column=1)
Book_Title_Entry.grid(row=1, column=1)

button_Add_book = tk.Button(Add_book_frame, text="Add", width=10, padx=5, pady=5, command=lambda:add_book(Book_ID_Entry.get(), Book_Title_Entry.get()))
button_Add_book.grid(row=2, column=0)
button_Clear_book = tk.Button(Add_book_frame, text="Clear", width=10, padx=5, pady=5, command=lambda :clear_entry([Book_ID_Entry,Book_Title_Entry]))
button_Clear_book.grid(row=2, column=1)

label30 = ttk.Label(Add_member_frame, text="First name: ")
label31 = ttk.Label(Add_member_frame, text="Last name: ")
label33 = ttk.Label(Add_member_frame, text="Phone number: ")
label32 = ttk.Label(Add_member_frame, text="Email: ")
Firstname_Entry = ttk.Entry(Add_member_frame, width=10)
Lastname_Entry = ttk.Entry(Add_member_frame, width=10)
Phonenumber_Entry = ttk.Entry(Add_member_frame, width=10)
email_Entry = ttk.Entry(Add_member_frame, width=25)

label30.grid(row=0, column=0)
label31.grid(row=1, column=0)
label33.grid(row=2, column=0)
label32.grid(row=3, column=0)
Firstname_Entry.grid(row=0, column=1)
Lastname_Entry.grid(row=1, column=1)
Phonenumber_Entry.grid(row=2, column=1)
email_Entry.grid(row=3, column=1)

button_Add_member = tk.Button(Add_member_frame, text="Add", width=10, padx=5, pady=5, command=lambda:add_member(Firstname_Entry.get(),Lastname_Entry.get(),Phonenumber_Entry.get(),email_Entry.get()))
button_Add_member.grid(row=4, column=0)
button_Clear_member = tk.Button(Add_member_frame, text="Clear", width=10, padx=5, pady=5, command=lambda :clear_entry([Firstname_Entry,Lastname_Entry,Phonenumber_Entry,email_Entry]))
button_Clear_member.grid(row=4, column=1)

# create reporting tab

report_tab = ttk.Frame(notebook)
notebook.add(report_tab, text="Reporting")

report_frame = ttk.LabelFrame(report_tab, text="Reports")
report_frame.grid(row=0, column=0,padx=50, pady=50, sticky="w")

selected_report = tk.StringVar()

# Create the radio buttons
overdue_books_radio = ttk.Radiobutton(report_frame, text="Overdue Books",
                                       variable=selected_report, value="overdue")
most_borrowed_radio = ttk.Radiobutton(report_frame, text="Most Borrowed Books",
                                       variable=selected_report, value="most_borrowed")
lent_books_radio = ttk.Radiobutton(report_frame, text="Lent Books",
                                       variable=selected_report, value="lent")

overdue_books_radio.grid(row=0, column=0, padx=10, pady=10, sticky="w")
most_borrowed_radio.grid(row=1, column=0, padx=10, pady=10, sticky="w")
lent_books_radio.grid(row=2, column=0, padx=10, pady=10, sticky="w")

generate_report_button = ttk.Button(report_frame, text="Generate Report",
                                     command=lambda: generate_report(selected_report.get()))
generate_report_button.grid(row=3, column=0, padx=10, pady=10, sticky="w")

def generate_report(report_type):

    if report_type == "overdue":
        # Create a new window
        results_window = tk.Toplevel()
        results_window.title("Overdue Books")

        # Create a Treeview to display the results
        results_treeview = ttk.Treeview(results_window)

        # Define the columns
        results_treeview["columns"] = ("First Name", "Last Name", "Email", "Title", "Date Lent", "Days Overdue")
        # Set column headings
        results_treeview.column("#0", width=0, stretch=tk.NO)
        results_treeview.column("First Name", width=100, anchor=tk.CENTER)
        results_treeview.column("Last Name", width=100, anchor=tk.CENTER)
        results_treeview.column("Email", width=200, anchor=tk.CENTER)
        results_treeview.column("Title", width=200, anchor=tk.CENTER)
        results_treeview.column("Date Lent", width=100, anchor=tk.CENTER)
        results_treeview.column("Days Overdue", width=100, anchor=tk.CENTER)

        # Add headings to treeview
        results_treeview.heading("#0", text="", anchor=tk.CENTER)
        results_treeview.heading("First Name", text="First Name", anchor=tk.CENTER)
        results_treeview.heading("Last Name", text="Last Name", anchor=tk.CENTER)
        results_treeview.heading("Email", text="Email", anchor=tk.CENTER)
        results_treeview.heading("Title", text="Title", anchor=tk.CENTER)
        results_treeview.heading("Date Lent", text="Date Lent", anchor=tk.CENTER)
        results_treeview.heading("Days Overdue", text="Days Overdue", anchor=tk.CENTER)

        # Fetch data from the database
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute("SELECT members.fname, members.lname, members.email, books.title, out_books.date_lended, "
                  "julianday('now') - julianday(out_books.date_lended) - 14 AS days_overdue "
                  "FROM books "
                  "JOIN out_books ON books.id = out_books.book_id "
                  "JOIN members ON members.id = out_books.member_id "
                  "WHERE out_books.date_returned IS NULL "
                  "AND out_books.date_lended <= date('now', '-14 days')")
        rows = c.fetchall()
        for row in rows:
            results_treeview.insert("", tk.END, text="", values=row)
        results_treeview.pack(fill=tk.BOTH, expand=1)
        conn.close()

    elif report_type == "most_borrowed":
        # Generate most borrowed books report
        # create a new window
        result_window = tk.Toplevel()
        result_window.title("Number of times books borrowed")

        # create a Treeview
        result_tree = ttk.Treeview(result_window)
        result_tree.pack(fill=BOTH, expand=YES)

        # add columns to the Treeview
        result_tree["columns"] = ("Title", "Number of times borrowed")
        result_tree.column("#0", width=0, stretch=NO)
        result_tree.column("Title", anchor=W, width=200)
        result_tree.column("Number of times borrowed", anchor=E, width=100)

        # add column headings
        result_tree.heading("#0", text="", anchor=W)
        result_tree.heading("Title", text="Title", anchor=W)
        result_tree.heading("Number of times borrowed", text="Number of times borrowed", anchor=E)
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute("SELECT books.title, COUNT(*) as count FROM books JOIN out_books ON books.id = out_books.book_id "
                  "GROUP BY books.title "
                  "ORDER BY count DESC")
        rows = c.fetchall()
        for row in rows:
            result_tree.insert("", "end", text="", values=row)

        result_window.geometry("400x300")
        result_window.resizable(True, True)

    elif report_type == "lent":
        # Generate lent books report
        # create a new window to display the query results
        result_window = tk.Toplevel(root)
        result_window.title("Lent Books")

        # create a Treeview to display the results
        result_tree = ttk.Treeview(result_window,
                                   columns=["Book Title", "Borrower Name", "Date Lent"], show="headings")
        result_tree.pack(fill="both", expand=True)

        # add column headings to the Treeview
        result_tree.column("Book Title", anchor="w", width=200)
        result_tree.column("Borrower Name", anchor="w", width=200)
        result_tree.column("Date Lent", anchor="w", width=100)

        result_tree.heading("Book Title", text="Book Title", anchor="w")
        result_tree.heading("Borrower Name", text="Borrower Name", anchor="w")
        result_tree.heading("Date Lent", text="Date Lent", anchor="w")
        conn = sqlite3.connect('library.db')
        c = conn.cursor()
        c.execute("SELECT books.title, members.fname || ' ' || members.lname, out_books.date_lended "
                  "FROM books "
                   "JOIN out_books ON books.id = out_books.book_id "
                   "JOIN members ON members.id = out_books.member_id "
                   "WHERE out_books.date_returned IS NULL ORDER BY out_books.date_lended DESC")

        results = c.fetchall()

        # insert the results into the Treeview
        for i, row in enumerate(results):
            result_tree.insert(parent="", index=i, iid=str(i), values=(row[0], row[1], row[2]))

        conn.close()

def close_program():
    root.quit()
    root.destroy()
root.protocol("WM_DELETE_WINDOW", close_program)


root.mainloop()


