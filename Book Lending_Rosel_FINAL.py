import customtkinter as ctk
from tkinter import messagebox, simpledialog
from datetime import datetime
import os

def create_logout_button(parent, app):
    def logout():
        parent.destroy()
        app.deiconify()
    return ctk.CTkButton(parent, text="Logout", command=logout)

# === CONFIG ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

USER_DB = "users.txt"
MANAGER_DB = "managers.txt"
BOOK_DB = "library.txt"
ACTIVITY_LOG_FILE = "activity_log.txt"
REQUESTS_FILE = "requests.txt"

# === USER ACCOUNT FUNCTIONS ===
def load_users(filename):
    if not os.path.exists(filename):
        return {}
    users = {}
    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if "," in line:
                username, password = line.split(",", 1)
                users[username] = password
    return users

def save_user(username, password):
    with open(USER_DB, "a") as file:
        file.write(f"{username},{password}\n")

# === Book Class ===
class Book:
    def __init__(self, title, quantity=1, is_lent=0):
        self.title = title
        self.quantity = int(quantity)
        self.is_lent = int(is_lent)

    def __str__(self):
        return f"{self.title}|{self.quantity}|{self.is_lent}"

    def available(self):
        return self.quantity - self.is_lent

    @staticmethod
    def from_string(data_str):
        parts = data_str.strip().split("|")
        if len(parts) == 3:
            return Book(parts[0], parts[1], parts[2])
        return None

# === Library Class ===
class Library:
    def __init__(self):
        self.books = {}
        self.load_books()

    def load_books(self):
        if not os.path.exists(BOOK_DB):
            return
        with open(BOOK_DB, "r") as f:
            for line in f:
                book = Book.from_string(line)
                if book:
                    self.books[book.title] = book

    def save_books(self):
        with open(BOOK_DB, "w") as f:
            for book in self.books.values():
                f.write(str(book) + "\n")

    def add_book(self, title, quantity=1):
        if title in self.books:
            self.books[title].quantity += quantity
        else:
            self.books[title] = Book(title, quantity)
        self.save_books()
        return True

    def lend_book(self, title):
        if title in self.books:
            book = self.books[title]
            if book.is_lent < book.quantity:
                book.is_lent += 1
                self.save_books()
                return True
        return False

    def return_book(self, title):
        if title in self.books:
            book = self.books[title]
            if book.is_lent > 0:
                book.is_lent -= 1
                self.save_books()
                return True
        return False

    def get_books(self):
        return self.books.values()

# === Manager View ===
class LibraryGUI(ctk.CTkToplevel):
    def __init__(self, master=None, username=None):
        self.selected_return_book_title = None
        self.selected_book_title = None
        super().__init__(master)
        self.title("Book Lending System")
        self.geometry("700x500")
        self.username = username
        self.library = Library()
        self.activity_log = []

        self.load_activity_log()

        self.tabview = ctk.CTkTabview(self, width=680, height=460)
        self.tabview.pack(padx=10, pady=10, expand=True, fill="both")

        self.dashboard_tab = self.tabview.add("Dashboard")
        self.functions_tab = self.tabview.add("Functions")

        self.tabview.set("Dashboard")

        self.init_dashboard_tab()
        self.init_functions_tab()


    def logout(self):
        self.destroy()
        self.master.deiconify()  # show login screen again
    def init_functions_tab(self):
        self.search_var = ctk.StringVar()
        search_frame = ctk.CTkFrame(self.functions_tab)
        search_frame.pack(fill='x', padx=10, pady=(10, 0))
        ctk.CTkLabel(search_frame, text='Search Book:').pack(side='left', padx=5, pady=5)
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=300)
        search_entry.pack(side='left', fill='x', expand=True, padx=(0,5), pady=5)
        self.search_var.trace_add('write', lambda *args: self.refresh_books())

        self.scrollable_frame = ctk.CTkScrollableFrame(self.functions_tab)
        self.scrollable_frame.pack(fill='both', expand=True, padx=10, pady=10, side='left')

        header_frame = ctk.CTkFrame(self.scrollable_frame)
        header_frame.pack(fill='x', pady=(0, 10))
        ctk.CTkLabel(header_frame, text='No.', width=50).pack(side='left', padx=(10,5))
        ctk.CTkLabel(header_frame, text='Title', width=300).pack(side='left', padx=5)
        ctk.CTkLabel(header_frame, text='Available', width=80).pack(side='left', padx=5)
        ctk.CTkLabel(header_frame, text='Total', width=80).pack(side='left', padx=5)

        button_frame = ctk.CTkFrame(self.functions_tab)
        button_frame.pack(side='right', fill='y', padx=10, pady=10)

        button_width = 140
        button_height = 40
        button_padding = 10

        ctk.CTkButton(button_frame, text='Add Book', command=self.add_book, width=button_width, height=button_height).pack(pady=(0, button_padding))
        ctk.CTkButton(button_frame, text='Lend Book', command=self.lend_book, width=button_width, height=button_height).pack(pady=(0, button_padding))
        ctk.CTkButton(button_frame, text='Return Book', command=self.return_book, width=button_width, height=button_height).pack(pady=(0, button_padding))
        ctk.CTkButton(button_frame, text='Logout', command=self.logout, width=button_width, height=button_height).pack(pady=(0, 0))

        self.refresh_books()
    def init_dashboard_tab(self):
        self.total_books_label = ctk.CTkLabel(self.dashboard_tab, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.total_books_label.pack(pady=10)
        self.reload_btn = ctk.CTkButton(self.dashboard_tab, text="Reload Logs", command=self.update_dashboard)
        self.reload_btn.pack(pady=(0, 10))
        log_frame = ctk.CTkFrame(self.dashboard_tab)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_label = ctk.CTkLabel(log_frame, text='Activity Log', font=ctk.CTkFont(size=16, weight='bold'))
        left_label.pack(side='left', fill='x', padx=(0, 5), pady=(0, 5))
        right_label = ctk.CTkLabel(log_frame, text='Customer Requests', font=ctk.CTkFont(size=16, weight='bold'))
        right_label.pack(side='right', fill='x', padx=(5, 0), pady=(0, 5))
        self.log_box = ctk.CTkTextbox(log_frame)
        self.log_box.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self.request_box = ctk.CTkTextbox(log_frame)
        self.request_box.pack(side="right", fill="both", expand=True, padx=(5, 0))

    def load_activity_log(self):
        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, "r") as f:
                self.activity_log = [line.strip() for line in f.readlines()]

    def save_activity_log(self):
        with open(ACTIVITY_LOG_FILE, "w") as f:
            for entry in self.activity_log:
                f.write(entry + "\n")

    def log_activity(self, action_text):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_info = f"{self.username}" if self.username else "Unknown"
        log_entry = f"[{timestamp}] ({user_info}) {action_text}"
        self.activity_log.append(log_entry)
        self.save_activity_log()
        self.update_dashboard()


    def lend_book_with_quantity(self):
        title = self.selected_book_title
        if not title:
            messagebox.showerror('Error', 'Please select a book to lend.')
            return
        book = self.library.books.get(title)
        if not book:
            messagebox.showerror('Error', 'Book not found.')
            return
        qty = simpledialog.askinteger('Quantity', 'Enter number of copies to lend:', parent=self, minvalue=1)
        if qty is None:
            return
        if qty > book.available():
            messagebox.showerror('Error', f'Only {book.available()} copies available.')
        else:
            book.is_lent += qty
            self.library.save_books()
            self.log_activity(f'Lent {qty} copies of "{title}".')
            messagebox.showinfo('Success', f'{qty} copies lent.')
            self.refresh_books()
    def view_customer_requests(self):
        if not os.path.exists(REQUESTS_FILE):
            messagebox.showinfo("No Requests", "No customer requests found.")
            return
        with open(REQUESTS_FILE, "r") as f:
            requests = f.readlines()
        if not requests:
            messagebox.showinfo("No Requests", "No customer requests found.")
            return
        msg = "\n".join(requests)
        messagebox.showinfo("Customer Requests", msg)

    def update_dashboard(self):
        total_books = sum(book.quantity - book.is_lent for book in self.library.get_books())
        self.total_books_label.configure(text=f"Total Available Books: {total_books}")

        if hasattr(self, 'log_box'):
            self.log_box.delete("0.0", "end")
            if self.activity_log:
                for log in reversed(self.activity_log[-50:]):
                    self.log_box.insert("end", log + "\n")
            else:
                self.log_box.insert("end", "No recent activity.")

        if hasattr(self, 'request_box'):
            self.request_box.delete("0.0", "end")
            if os.path.exists(REQUESTS_FILE):
                with open(REQUESTS_FILE, "r") as f:
                    requests = f.readlines()
                if requests:
                    for req in reversed(requests[-50:]):
                        self.request_box.insert("end", req.strip() + "\n")
                else:
                    self.request_box.insert("end", "No customer requests.")
            else:
                self.request_box.insert("end", "requests.txt not found.")

    def highlight_selected_book(self):
        for i, child in enumerate(self.scrollable_frame.winfo_children(), start=1):
            if isinstance(child, ctk.CTkFrame):
                bg = 'gray20' if child.grid_info()['row'] % 2 == 0 else 'gray15'
                child.configure(fg_color=bg)
                labels = [w for w in child.winfo_children() if isinstance(w, ctk.CTkLabel)]
                if labels and labels[1].cget('text') == self.selected_book_title:
                    child.configure(fg_color='blue')

    def refresh_books(self):
        filter_text = self.search_var.get().lower() if hasattr(self, 'search_var') else ''
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for col in range(4):
            self.scrollable_frame.grid_columnconfigure(col, weight=1)

        for i, book in enumerate(self.library.get_books(), start=1):
            if filter_text and filter_text not in book.title.lower():
                continue
            available = book.quantity - book.is_lent
            row_frame = ctk.CTkFrame(self.scrollable_frame, fg_color='gray15', corner_radius=5)
            row_frame.grid(row=i, column=0, columnspan=4, sticky='nsew', padx=2, pady=1)

            ctk.CTkLabel(row_frame, text=str(i), width=30).grid(row=0, column=0, sticky='w')
            ctk.CTkLabel(row_frame, text=book.title, width=200).grid(row=0, column=1, sticky='w')
            ctk.CTkLabel(row_frame, text=str(available), width=60).grid(row=0, column=2, sticky='w')
            ctk.CTkLabel(row_frame, text=str(book.quantity), width=60).grid(row=0, column=3, sticky='w')

            def on_select(event, title=book.title):
                self.selected_book_title = title
                self.highlight_selected_book()
            row_frame.bind('<Button-1>', on_select)
            for child in row_frame.winfo_children():
                child.bind('<Button-1>', on_select)

        self.highlight_selected_book()
    def get_selected_book_title(self):
        return simpledialog.askstring("Book", "Enter exact book title:")

    def add_book(self):
        title = simpledialog.askstring("Add Book", "Enter book title:")
        if title:
            try:
                quantity = int(simpledialog.askstring("Quantity", "Enter quantity:"))
                if self.library.add_book(title.strip(), quantity):
                    self.log_activity(f"Added {quantity} copies of '{title}'.")
                    messagebox.showinfo("Success", f"{quantity} copies added.")
            except:
                messagebox.showerror("Error", "Quantity must be a number.")
        self.refresh_books()

    def lend_book(self):
        title = self.selected_book_title
        if not title:
            messagebox.showerror('Error', 'Please select a book to lend.')
            return
        book = self.library.books.get(title)
        if not book:
            messagebox.showerror('Error', 'Book not found.')
            return
        qty = simpledialog.askinteger('Quantity', f'Enter number of copies to lend for "{title}":', parent=self, minvalue=1)
        if qty is None:
            return
        available = book.quantity - book.is_lent
        if qty > available:
            messagebox.showerror('Error', f'Only {available} copies available.')
            return
        book.is_lent += qty
        self.library.save_books()
        self.log_activity(f'Lent {qty} copies of "{title}".')
        messagebox.showinfo('Success', f'{qty} copies lent.')
        self.refresh_books()
    def return_book(self):
        title = self.selected_book_title
        if not title:
            messagebox.showerror('Error', 'Please select a book to return.')
            return
        book = self.library.books.get(title)
        if not book:
            messagebox.showerror('Error', 'Book not found.')
            return
        qty = simpledialog.askinteger('Quantity', f'Enter number of copies to return for "{title}":', parent=self, minvalue=1)
        if qty is None:
            return
        if qty > book.is_lent:
            messagebox.showerror('Error', f'Only {book.is_lent} copies can be returned.')
            return
        book.is_lent -= qty
        self.library.save_books()
        self.log_activity(f'Returned {qty} copies of "{title}".')
        messagebox.showinfo('Success', f'{qty} copies returned.')
        self.refresh_books()
    def refresh_return_books(self):
        filter_text = self.return_search_var.get().lower() if hasattr(self, 'return_search_var') else ''
        for widget in self.return_scrollable_frame.winfo_children():
            widget.destroy()

        for col in range(4):
            self.return_scrollable_frame.grid_columnconfigure(col, weight=1)

        for i, book in enumerate(self.library.get_books(), start=1):
            available = book.is_lent
            if available <= 0:
                continue
            if filter_text and filter_text not in book.title.lower():
                continue
            row_frame = ctk.CTkFrame(self.return_scrollable_frame, fg_color='gray15', corner_radius=5)
            row_frame.grid(row=i, column=0, columnspan=4, sticky='nsew', padx=2, pady=1)

            ctk.CTkLabel(row_frame, text=str(i), width=30).grid(row=0, column=0, sticky='w')
            ctk.CTkLabel(row_frame, text=book.title, width=200).grid(row=0, column=1, sticky='w')
            ctk.CTkLabel(row_frame, text=str(available), width=60).grid(row=0, column=2, sticky='w')
            ctk.CTkLabel(row_frame, text=str(book.quantity), width=60).grid(row=0, column=3, sticky='w')

            def on_select(event, title=book.title):
                self.selected_return_book_title = title
                self.highlight_selected_return_book()
            row_frame.bind('<Button-1>', on_select)
            for child in row_frame.winfo_children():
                child.bind('<Button-1>', on_select)

        self.highlight_selected_return_book()

    def highlight_selected_return_book(self):
        for i, child in enumerate(self.return_scrollable_frame.winfo_children(), start=1):
            if isinstance(child, ctk.CTkFrame):
                bg = 'gray20' if child.grid_info()['row'] % 2 == 0 else 'gray15'
                child.configure(fg_color=bg)
                labels = [w for w in child.winfo_children() if isinstance(w, ctk.CTkLabel)]
                if labels and labels[1].cget('text') == self.selected_return_book_title:
                    child.configure(fg_color='blue')
class Book:
    def __init__(self, title, quantity=1, is_lent=0):
        self.title = title
        self.quantity = int(quantity)
        self.is_lent = int(is_lent)

    def __str__(self):
        return f"{self.title}|{self.quantity}|{self.is_lent}"

    def available(self):
        return self.quantity - self.is_lent

    @staticmethod
    def from_string(data_str):
        parts = data_str.strip().split("|")
        if len(parts) == 3:
            return Book(parts[0], parts[1], parts[2])
        return None

# === Library Class ===
class Library:
    def __init__(self):
        self.books = {}
        self.load_books()

    def load_books(self):
        if not os.path.exists(BOOK_DB):
            return
        with open(BOOK_DB, "r") as f:
            for line in f:
                book = Book.from_string(line)
                if book:
                    self.books[book.title] = book

    def save_books(self):
        with open(BOOK_DB, "w") as f:
            for book in self.books.values():
                f.write(str(book) + "\n")

    def add_book(self, title, quantity=1):
        if title in self.books:
            self.books[title].quantity += quantity
        else:
            self.books[title] = Book(title, quantity)
        self.save_books()
        return True

    def lend_book(self, title):
        if title in self.books:
            book = self.books[title]
            if book.is_lent < book.quantity:
                book.is_lent += 1
                self.save_books()
                return True
        return False

    def return_book(self, title):
        if title in self.books:
            book = self.books[title]
            if book.is_lent > 0:
                book.is_lent -= 1
                self.save_books()
                return True
        return False

    def get_books(self):
        return self.books.values()

# === Customer View ===
class CustomerView(ctk.CTkToplevel):
    def __init__(self, master=None, username=None):
        super().__init__(master)

        self.title("Customer View - Book Lending System")
        self.geometry("700x500")
        self.username = username

        self.books = []
        self.load_books()

        self.build_ui()
        self.show_books()

    def load_books(self):
        self.books = []
        if os.path.exists(BOOK_DB):
            with open(BOOK_DB, "r") as f:
                for line in f:
                    book = Book.from_string(line)
                    if book:
                        self.books.append(book)

    def build_ui(self):
        self.label = ctk.CTkLabel(self, text=f"Welcome, {self.username}!", font=ctk.CTkFont(size=16, weight="bold"))
        self.label.pack(pady=10)

        search_row = ctk.CTkFrame(self)
        search_row.pack(padx=50, pady=(5, 10), fill="x")

        icon = ctk.CTkLabel(search_row, text="🔍", width=30)
        icon.pack(side="left")

        self.search_entry = ctk.CTkEntry(
            search_row,
            placeholder_text="Type to search available books...",
            height=36,
            corner_radius=10,
            font=ctk.CTkFont(size=13)
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda event: self.show_books())

        # === Scrollable Book List ===
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = ctk.CTkCanvas(container, bg="black", highlightthickness=0)
        self.scrollable_frame = ctk.CTkFrame(self.canvas)

        self.scrollbar = ctk.CTkScrollbar(container, orientation="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.scrollable_window, width=e.width))

        self.canvas.pack(side="left", fill="both", expand=True)

        self.request_button = ctk.CTkButton(self, text="Request a Book", command=self.request_book)
        self.request_button.pack(pady=5)

        self.history_button = ctk.CTkButton(self, text="View My Requests", command=self.view_requests)
        self.history_button.pack(pady=5)
        create_logout_button(self, self.master).pack(pady=10)

    def show_books(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        query = self.search_entry.get().lower()
        filtered = [b for b in self.books if query in b.title.lower()]

        headers = ["Title", "Available", "Total"]
        for i, text in enumerate(headers):
            ctk.CTkLabel(self.scrollable_frame, text=text, font=ctk.CTkFont(weight="bold"),
                         fg_color="gray30", corner_radius=5).grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            self.scrollable_frame.grid_columnconfigure(i, weight=1)

        for idx, book in enumerate(filtered, start=1):
            ctk.CTkLabel(self.scrollable_frame, text=book.title).grid(row=idx, column=0, padx=5, pady=2, sticky="nsew")
            ctk.CTkLabel(self.scrollable_frame, text=str(book.available())).grid(row=idx, column=1, padx=5, pady=2,
                                                                                 sticky="nsew")
            ctk.CTkLabel(self.scrollable_frame, text=str(book.quantity)).grid(row=idx, column=2, padx=5, pady=2,
                                                                              sticky="nsew")
    def request_book(self):
        title = simpledialog.askstring("Request Book", "Enter the exact title of the book:")
        if not title:
            return

        book = next((b for b in self.books if b.title.lower() == title.strip().lower()), None)
        if not book:
            messagebox.showerror("Error", "Book not found.")
            return

        if book.available() <= 0:
            messagebox.showwarning("Unavailable", "This book is currently not available.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(REQUESTS_FILE, "a") as f:
            f.write(f"{self.username}|{book.title}|{timestamp}\n")

        messagebox.showinfo("Requested", f"You have requested '{book.title}'. Please wait for manager approval.")

    def view_requests(self):
        if not os.path.exists(REQUESTS_FILE):
            messagebox.showinfo("No Requests", "You haven't made any requests yet.")
            return

        requests = []
        with open(REQUESTS_FILE, "r") as f:
            for line in f:
                user, title, time = line.strip().split("|")
                if user == self.username:
                    requests.append((title, time))

        if not requests:
            messagebox.showinfo("No Requests", "You haven't made any requests yet.")
            return

        msg = "\n".join([f"{title} ({time})" for title, time in requests])
        messagebox.showinfo("My Requests", msg)

# === Login App ===
class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Eldridge's Book Lending System")
        self.geometry("400x400")
        self.resizable(False, False)

        self.frame = ctk.CTkFrame(self, width=350, height=300, corner_radius=15)
        self.frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.tabview = ctk.CTkTabview(self.frame, width=350, height=300)
        self.tabview.pack(padx=10, pady=10)

        self.login_tab = self.tabview.add("Login")
        self.signup_tab = self.tabview.add("Sign Up")

        self.init_login_tab()
        self.init_signup_tab()

        self.username_entry.bind("<Return>", self.login)
        self.password_entry.bind("<Return>", self.login)
        self.signup_username_entry.bind("<Return>", self.signup)
        self.signup_password_entry.bind("<Return>", self.signup)

    def init_login_tab(self):
        self.title_label = ctk.CTkLabel(self.login_tab, text="Log In to Your Account", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        self.username_entry = ctk.CTkEntry(self.login_tab, placeholder_text="Email or Username", width=250)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self.login_tab, placeholder_text="Password", show="*", width=250)
        self.password_entry.pack(pady=10)

        self.login_btn = ctk.CTkButton(self.login_tab, text="Log In", command=self.login)
        self.login_btn.pack(pady=15)

    def init_signup_tab(self):
        self.signup_title_label = ctk.CTkLabel(self.signup_tab, text="Create a New Account", font=ctk.CTkFont(size=18, weight="bold"))
        self.signup_title_label.pack(pady=(20, 10))

        self.signup_username_entry = ctk.CTkEntry(self.signup_tab, placeholder_text="Email or Username", width=250)
        self.signup_username_entry.pack(pady=10)

        self.signup_password_entry = ctk.CTkEntry(self.signup_tab, placeholder_text="Password", show="*", width=250)
        self.signup_password_entry.pack(pady=10)

        self.signup_btn = ctk.CTkButton(self.signup_tab, text="Sign Up", command=self.signup)
        self.signup_btn.pack(pady=15)

    def login(self, event=None):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        managers = load_users(MANAGER_DB)
        users = load_users(USER_DB)

        if not username or not password:
            messagebox.showerror("Error", "Please enter all fields.")
        elif username in managers and managers[username] == password:
            messagebox.showinfo("Success", f"Welcome Manager, {username}!")
            self.withdraw()
            LibraryGUI(self, username=username)
        elif username in users and users[username] == password:
            messagebox.showinfo("Success", f"Welcome, {username}!")
            self.withdraw()
            CustomerView(self, username=username)
        else:
            messagebox.showerror("Error", "Invalid credentials.")

    def signup(self, event=None):
        username = self.signup_username_entry.get().strip()
        password = self.signup_password_entry.get().strip()
        users = load_users(USER_DB)

        if not username or not password:
            messagebox.showerror("Error", "Please enter all fields.")
        elif username in users:
            messagebox.showwarning("Warning", "Username already exists.")
        elif len(password) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters long.")
        elif username.lower() == password.lower():
            messagebox.showwarning("Weak Password", "Password cannot be the same as the username.")
        else:
            save_user(username, password)
            messagebox.showinfo("Success", "Account created!")

# === Run ===
if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()
