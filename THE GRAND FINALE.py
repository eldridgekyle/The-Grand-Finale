import customtkinter as ctk
from tkinter import messagebox, simpledialog
from datetime import datetime
import os

# === CONFIG ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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

    def init_functions_tab(self):
        main_frame = ctk.CTkFrame(self.functions_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        header_frame = ctk.CTkFrame(left_frame)
        header_frame.pack(fill="x")

        headers = ["No.", "Title", "Available", "Total"]
        for idx, text in enumerate(headers):
            label = ctk.CTkLabel(header_frame, text=text, font=ctk.CTkFont(weight="bold"), fg_color="gray30", corner_radius=5)
            label.grid(row=0, column=idx, padx=2, pady=5, sticky="nsew")
            header_frame.grid_columnconfigure(idx, weight=1)

        self.canvas = ctk.CTkCanvas(left_frame, bg="black", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = ctk.CTkFrame(self.canvas)
        self.scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.scrollable_window, width=e.width))

        self.scrollbar = ctk.CTkScrollbar(left_frame, orientation="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        button_frame = ctk.CTkFrame(main_frame, width=120)
        button_frame.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkButton(button_frame, text="Add Book", command=self.add_book).pack(pady=5, fill="x")
        ctk.CTkButton(button_frame, text="Lend Book", command=self.lend_book).pack(pady=5, fill="x")
        ctk.CTkButton(button_frame, text="Return Book", command=self.return_book).pack(pady=5, fill="x")

        self.refresh_books()

    def init_dashboard_tab(self):
        self.total_books_label = ctk.CTkLabel(self.dashboard_tab, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.total_books_label.pack(pady=10)

        self.log_box = ctk.CTkTextbox(self.dashboard_tab, height=300)
        self.log_box.pack(padx=10, pady=10, fill="both", expand=True)
        self.update_dashboard()

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

    def update_dashboard(self):
        total_books = sum(book.quantity - book.is_lent for book in self.library.get_books())
        self.total_books_label.configure(text=f"Total Available Books: {total_books}")

        self.log_box.delete("0.0", "end")
        for log in reversed(self.activity_log[-50:]):
            self.log_box.insert("end", log + "\n")

    def refresh_books(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for col in range(4):
            self.scrollable_frame.grid_columnconfigure(col, weight=1)

        for i, book in enumerate(self.library.get_books(), start=1):
            available = book.quantity - book.is_lent

            ctk.CTkLabel(self.scrollable_frame, text=str(i), fg_color="gray20", corner_radius=5).grid(row=i, column=0, padx=2, pady=1, sticky="nsew")
            ctk.CTkLabel(self.scrollable_frame, text=book.title, fg_color="gray25", corner_radius=5).grid(row=i, column=1, padx=2, pady=1, sticky="nsew")
            ctk.CTkLabel(self.scrollable_frame, text=str(available), fg_color="gray20", corner_radius=5).grid(row=i, column=2, padx=2, pady=1, sticky="nsew")
            ctk.CTkLabel(self.scrollable_frame, text=str(book.quantity), fg_color="gray25", corner_radius=5).grid(row=i, column=3, padx=2, pady=1, sticky="nsew")

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
        title = self.get_selected_book_title()
        if title:
            if self.library.lend_book(title):
                self.log_activity(f"'{title}' has been lent out.")
                messagebox.showinfo("Success", f"'{title}' has been lent out.")
            else:
                messagebox.showwarning("Unavailable", f"'{title}' is not available.")
            self.refresh_books()

    def return_book(self):
        title = self.get_selected_book_title()
        if title:
            if self.library.return_book(title):
                self.log_activity(f"'{title}' has been returned.")
                messagebox.showinfo("Success", f"'{title}' has been returned.")
            else:
                messagebox.showwarning("Error", f"'{title}' was not lent out.")
            self.refresh_books()

import customtkinter as ctk
from tkinter import messagebox, simpledialog
from datetime import datetime
import os

# === CONFIG ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
