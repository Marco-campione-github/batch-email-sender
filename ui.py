import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path
import threading

from auth import authenticate, is_authenticated, get_authenticated_user_email
from email_service import send_email

TOKEN_FILE = "token.pickle"


class BulkMailerUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk Gmail Sender")
        self.root.geometry("800x600")

        self.service = None

        self.auth_frame = None
        self.email_frame = None
        self.send_button = None
        self.account_label = None

        if is_authenticated():
            self.init_email_frame(auto_auth=True)
        else:
            self.init_auth_frame()

    # ---------- AUTH FRAME ----------
    def init_auth_frame(self):
        self.auth_frame = tk.Frame(self.root)
        self.auth_frame.pack(expand=True)

        tk.Label(
            self.auth_frame,
            text="Login with Google",
            font=("Helvetica", 18)
        ).pack(pady=20)

        tk.Button(
            self.auth_frame,
            text="Authenticate Google",
            width=30,
            height=2,
            command=self.handle_auth
        ).pack()

    def handle_auth(self):
        try:
            self.service = authenticate()
            messagebox.showinfo("Success", "Authenticated successfully!")
            self.auth_frame.destroy()
            self.init_email_frame()
        except Exception as e:
            messagebox.showerror("Authentication Error", str(e))

    # ---------- EMAIL FRAME ----------
    def init_email_frame(self, auto_auth=False):
        if auto_auth:
            self.service = authenticate()

        self.email_frame = tk.Frame(self.root)
        self.email_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Logout button at the top-right
        tk.Button(
            self.email_frame,
            text="Logout",
            command=self.handle_logout,
            fg="white",
            bg="red",
            width=10
        ).pack(anchor="ne", pady=5)

        # Account email display
        account_email = get_authenticated_user_email(self.service)
        self.account_label = tk.Label(
            self.email_frame,
            text=f"Logged in as: {account_email}",
            font=("Helvetica", 12, "italic"),
            fg="blue"
        )
        self.account_label.pack(anchor="nw", pady=(0, 10))

        # Subject
        tk.Label(self.email_frame, text="Subject").pack(anchor="w")
        self.subject_entry = tk.Entry(self.email_frame)
        self.subject_entry.pack(fill="x")

        # Body
        tk.Label(self.email_frame, text="Email Body (HTML allowed)").pack(anchor="w", pady=(10, 0))
        self.body_text = scrolledtext.ScrolledText(self.email_frame, height=10)
        self.body_text.pack(fill="both")

        # Recipients
        tk.Label(self.email_frame, text="Recipients (one per line)").pack(anchor="w", pady=(10, 0))
        self.recipients_text = scrolledtext.ScrolledText(self.email_frame, height=8)
        self.recipients_text.pack(fill="both")

        # Send button
        self.send_button = tk.Button(
            self.email_frame,
            text="Send Emails",
            height=2,
            command=self.confirm_send
        )
        self.send_button.pack(pady=15)

        # Progress label
        self.progress_label = tk.Label(self.email_frame, text="", font=("Helvetica", 10))
        self.progress_label.pack(pady=(5, 0))

        # Progress bar
        self.progress_bar = ttk.Progressbar(self.email_frame, length=400, mode="determinate")
        self.progress_bar.pack(pady=(5, 10))

    # ---------- LOGOUT ----------
    def handle_logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if confirm:
            # Delete token
            if Path(TOKEN_FILE).exists():
                Path(TOKEN_FILE).unlink()
            self.service = None
            self.email_frame.destroy()
            self.init_auth_frame()
            messagebox.showinfo("Logged out", "You have been logged out successfully.")

    # ---------- SEND LOGIC ----------
    def confirm_send(self):
        subject = self.subject_entry.get().strip()
        body = self.body_text.get("1.0", tk.END).strip()
        recipients = self.get_recipients()

        if not subject or not body or not recipients:
            messagebox.showwarning("Missing data", "Subject, body, and recipients are required.")
            return

        confirm = messagebox.askyesno(
            "Confirm Send",
            f"Send email to {len(recipients)} recipients?"
        )

        if confirm:
            self.send_emails(subject, body, recipients)

    def send_emails(self, subject, body, recipients):
        def task():
            total = len(recipients)
            sent = 0

            # Reset progress bar
            self.progress_bar["maximum"] = total
            self.progress_bar["value"] = 0
            self.progress_label.config(text="")
            self.send_button.config(state="disabled")
            self.root.update_idletasks()

            for i, email in enumerate(recipients, start=1):
                try:
                    # Call the email_service function
                    from email_service import send_email
                    send_email(self.service, email, subject, body)
                    sent += 1
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to send to {email}\n{e}")
                finally:
                    # Update progress
                    self.progress_bar["value"] = i
                    self.progress_label.config(text=f"Sending email {i} / {total}")
                    self.root.update_idletasks()

            self.send_button.config(state="normal")
            self.progress_label.config(text=f"Done! Sent {sent}/{total} emails.")

        threading.Thread(target=task).start()


    def get_recipients(self):
        raw = self.recipients_text.get("1.0", tk.END)
        return [line.strip() for line in raw.splitlines() if line.strip()]

    # ---------- HELPER ----------
    def get_logged_in_email(self):
        """Return the Gmail account currently authenticated."""
        return get_authenticated_user_email(self.service)