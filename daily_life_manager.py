import datetime
import random
import tkinter as tk
from tkinter import messagebox, ttk
import pickle
import threading
import time

# Importing NLP libraries
from transformers import pipeline
import torch

# Importing ttkbootstrap for enhanced UI
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class DailyLifeManager:
    def __init__(self):
        self.schedule = {}
        self.study_paths = [
            "Advanced Math", "Physics", "Machine Learning", "Network Security", "Cryptography",
            "Software Engineering", "Data Analysis", "Quantum Computing"
        ]
        self.daily_tasks = [
            "Exercise", "Meal Prep", "Relax", "Meditation", "Grocery Shopping", "House Chores",
            "Reading", "Creative Writing", "Project Work"
        ]
        self.breaks = ["Short Break", "Long Break"]
        self.sleep_schedule = "Sleep"
        self.targets = {}
        self.yearly_tasks = {}
        self.complex_tasks = {}
        self.user_preferences = {
            "productive_hours": (9, 17),  # Default productive hours from 9 AM to 5 PM
            "preferred_tasks": [],
            "stress_level": "normal"  # Can be "low", "normal", "high"
        }
        self.task_completion_history = []  # Track task completion for behavior learning
        self.achievements = []  # Track achievements for motivation

        # Load sentiment analysis model
        self.sentiment_analyzer = pipeline("sentiment-analysis")

        # Load NLP model for task parsing
        self.nlp_model = pipeline("fill-mask", model="distilbert-base-uncased")

        # Load user preferences
        self.load_user_preferences()

        # Initialize the GUI elements after the main window is created
        self.root = tb.Window(themename="flatly")  # Minimalistic theme
        self.setup_ui()

        # Start the notification thread
        self.start_notification_thread()

    def save_user_preferences(self):
        with open("user_preferences.pkl", "wb") as f:
            pickle.dump(self.user_preferences, f)

    def load_user_preferences(self):
        try:
            with open("user_preferences.pkl", "rb") as f:
                self.user_preferences = pickle.load(f)
        except FileNotFoundError:
            pass

    def add_task(self, time, task):
        self.schedule[time] = task
        self.refresh_schedule_display()

    def add_target(self, target, deadline):
        self.targets[target] = deadline
        self.break_down_target(target)

    def add_yearly_task(self, yearly_task, deadline):
        self.yearly_tasks[yearly_task] = deadline
        self.break_down_yearly_task(yearly_task)

    def add_complex_task(self, complex_task, deadline):
        self.complex_tasks[complex_task] = deadline
        self.break_down_complex_task(complex_task)

    def break_down_target(self, target):
        # Break down a target into smaller tasks
        tasks = [f"{target} - Step {i+1}" for i in range(5)]
        for task in tasks:
            self.daily_tasks.append(task)

    def break_down_yearly_task(self, yearly_task):
        # Break down a yearly task into monthly tasks
        for month in range(1, 13):
            task = f"{yearly_task} - Month {month}"
            self.daily_tasks.append(task)

    def break_down_complex_task(self, complex_task):
        # Break down a complex task into weekly tasks
        for week in range(1, 5):
            task = f"{complex_task} - Week {week}"
            self.daily_tasks.append(task)

    def generate_daily_schedule(self):
        self.schedule.clear()
        # Set the current time to the start of the day you want (e.g., 5:45 AM)
        current_time = datetime.datetime.now().replace(hour=5, minute=45, second=0, microsecond=0)
        # Define end time (for example, 11:00 PM)
        end_time = current_time.replace(hour=23)

        productive_start, productive_end = self.user_preferences["productive_hours"]

        # Define timetable segments
        timetable = [
            ("MORNING ROUTINE", "5:45 AM", "8:00 AM", [
                ("5:45 AM - 6:00 AM", "Wake up & Hydrate"),
                ("6:00 AM - 7:00 AM", "Exercise (Physical/Stretching)"),
                ("7:00 AM - 8:00 AM", "Breakfast")
            ]),
            ("PLANNING AND JOURNALING", "8:00 AM", "9:00 AM", [
                ("8:00 AM - 9:00 AM", "Plan the day and journal thoughts")
            ]),
            ("WORK SLOT: BUSINESS", "9:00 AM", "12:30 PM", [
                ("9:00 AM - 12:30 PM", "Focused work on business strategy, research, or other business-related tasks")
            ]),
            ("MIDDAY BREAK", "12:30 PM", "1:30 PM", [
                ("12:30 PM - 1:30 PM", "Lunch and relaxation")
            ]),
            ("PERSONAL DEVELOPMENT: READING", "1:30 PM", "3:00 PM", [
                ("1:30 PM - 3:00 PM", "Reading for personal growth or skill development")
            ]),
            ("WORK SLOT: LEARNING", "3:00 PM", "8:00 PM", [
                ("3:00 PM - 5:30 PM", "Learning courses or skills development"),
                ("5:45 PM - 8:00 PM", "Focused work on projects or assignments")
            ]),
            ("EVENING ROUTINE", "8:00 PM", "11:00 PM", [
                ("8:00 PM - 9:00 PM", "Networking or community engagement"),
                ("9:00 PM - 10:00 PM", "Dinner & Relaxation"),
                ("10:00 PM - 11:00 PM", "Review the day and plan for tomorrow")
            ])
        ]

        # Populate timetable
        for segment in timetable:
            segment_name, start_time_str, end_time_str, tasks = segment
            for task_time_str, task in tasks:
                self.add_task(task_time_str, task)

        # Fill remaining slots with dynamic tasks
        while current_time < end_time:
            time_str = current_time.strftime("%I:%M %p")
            if time_str not in self.schedule:
                if current_time.hour < 8:
                    task = "Morning Exercise - Start your day with some physical activity!"
                elif current_time.hour >= 21:
                    task = f"{self.sleep_schedule} - Time to rest and recharge for tomorrow."
                else:
                    task = self.choose_task()
                self.add_task(time_str, task)
            current_time += datetime.timedelta(minutes=60)

    def get_advice(self, topic):
        # Simple advice-generating function
        advice_list = [
            f"Focus on consistency when working on {topic}.",
            f"Break {topic} into smaller, manageable steps.",
            f"Stay motivated by setting achievable goals for {topic}.",
            f"Take regular breaks to maintain productivity while working on {topic}."
        ]
        return random.choice(advice_list)

    def adjust_task(self, time, new_task):
        if time in self.schedule:
            advice = self.get_advice(new_task)
            self.schedule[time] = f"{new_task} - {advice}"
            self.refresh_and_generate_schedule()
        else:
            messagebox.showerror("Error", "Time slot not found in the schedule.")

    def choose_task(self):
        # Enhanced task recommendation system
        if not self.task_completion_history:
            return random.choice(self.daily_tasks)

        # Simulate preference learning
        preferred_tasks = self.user_preferences.get("preferred_tasks", [])
        stress_level = self.user_preferences.get("stress_level", "normal")

        # Adjust task selection based on stress level
        if stress_level == "high":
            tasks_pool = [task for task in self.daily_tasks if task in self.breaks + ["Meditation", "Relax"]]
        else:
            tasks_pool = self.daily_tasks

        if preferred_tasks:
            task = random.choice(preferred_tasks)
            if task in tasks_pool:
                return task

        selected_task = random.choice(tasks_pool)
        return f"{selected_task} - {self.get_advice(selected_task)}"

    def log_mood(self):
        mood_window = tk.Toplevel()
        mood_window.title("Log Mood")
        mood_window.geometry("400x250")
        mood_window.resizable(False, False)

        ttk.Label(mood_window, text="How are you feeling today?", font=("Helvetica", 12)).grid(row=0, column=0, padx=10, pady=10)
        mood_entry = ttk.Entry(mood_window, width=40, font=("Helvetica", 12))
        mood_entry.grid(row=0, column=1, padx=10, pady=10)

        feedback_label = ttk.Label(mood_window, text="", font=("Helvetica", 10))
        feedback_label.grid(row=2, column=0, columnspan=2, pady=10)

        def save_mood():
            mood_text = mood_entry.get()
            if not mood_text.strip():
                messagebox.showerror("Input Error", "Please enter your mood.")
                return
            result = self.sentiment_analyzer(mood_text)[0]
            label = result['label']
            if label == 'NEGATIVE':
                self.user_preferences["stress_level"] = "high"
            elif label == 'POSITIVE':
                self.user_preferences["stress_level"] = "low"
            else:
                self.user_preferences["stress_level"] = "normal"
            self.save_user_preferences()
            mood_window.destroy()
            messagebox.showinfo("Mood Logged", f"Your mood has been logged as {self.user_preferences['stress_level']} stress.")
            self.refresh_and_generate_schedule()

        save_button = ttk.Button(mood_window, text="Save", command=save_mood, style="Success.TButton")
        save_button.grid(row=1, column=0, columnspan=2, pady=20)

    def display_schedule(self):
        self.generate_daily_schedule()
        self.refresh_schedule_display()

    def setup_ui(self):
        root = self.root
        root.title("Daily Life Manager")
        root.geometry("1200x800")
        root.resizable(True, True)

        # Navigation bar
        nav_frame = ttk.Frame(root, width=200)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Main content frame
        content_frame = ttk.Frame(root)
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Navigation buttons
        buttons = [
            ("Generate Schedule", self.generate_and_display_schedule),
            ("Adjust Task", self.adjust_task_ui),
            ("Add Target", self.add_target_ui),
            ("Add Yearly Task", self.add_yearly_task_ui),
            ("Add Complex Task", self.add_complex_task_ui),
            ("Natural Language Input", self.natural_language_input_ui),
            ("Log Mood", self.log_mood)
        ]

        for idx, (text, command) in enumerate(buttons):
            btn = ttk.Button(nav_frame, text=text, command=command, width=25)
            btn.pack(pady=10, padx=10)

        # Welcome and motivational section
        welcome_label = ttk.Label(
            content_frame, text="Welcome to Your Daily Life Manager!", font=("Helvetica", 24, "bold")
        )
        welcome_label.pack(pady=10)

        motivational_quotes = [
            "Believe you can and you're halfway there.",
            "Every day is a second chance.",
            "You are capable of amazing things.",
            "Start where you are. Use what you have. Do what you can."
        ]
        motivational_label = ttk.Label(
            content_frame, text=random.choice(motivational_quotes), font=("Helvetica", 14)
        )
        motivational_label.pack(pady=5)

        # Schedule display
        schedule_frame = ttk.Frame(content_frame)
        schedule_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        self.schedule_tree = ttk.Treeview(schedule_frame, columns=("Time", "Task"), show='headings', height=20)
        self.schedule_tree.heading("Time", text="Time")
        self.schedule_tree.heading("Task", text="Task")
        self.schedule_tree.column("Time", width=150, anchor='center')
        self.schedule_tree.column("Task", width=800, anchor='w')
        self.schedule_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar to the schedule_tree
        scrollbar = ttk.Scrollbar(schedule_frame, orient=tk.VERTICAL, command=self.schedule_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.schedule_tree.configure(yscrollcommand=scrollbar.set)

        # Initial Schedule Generation
        self.generate_and_display_schedule()

    def generate_and_display_schedule(self):
        self.generate_daily_schedule()
        self.refresh_schedule_display()

    def refresh_schedule_display(self):
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)

        # Sort the schedule based on time
        sorted_schedule = sorted(
            self.schedule.items(),
            key=lambda x: datetime.datetime.strptime(x[0].split(" - ")[0], '%I:%M %p')
        )

        # Insert sorted schedule into the treeview
        for time_str, task in sorted_schedule:
            self.schedule_tree.insert('', tk.END, values=(time_str, task))

    def adjust_task_ui(self):
        adjust_window = tk.Toplevel()
        adjust_window.title("Adjust Task")
        adjust_window.geometry("400x300")
        adjust_window.resizable(False, False)

        ttk.Label(adjust_window, text="Adjust Task", font=("Helvetica", 16, "bold")).pack(pady=10)

        form_frame = ttk.Frame(adjust_window)
        form_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Select Time:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        time_combobox = ttk.Combobox(form_frame, values=sorted(self.schedule.keys()), state="readonly", width=25)
        time_combobox.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="New Task:", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        task_entry = ttk.Entry(form_frame, width=28, font=("Helvetica", 12))
        task_entry.grid(row=1, column=1, padx=5, pady=5)

        def save_adjusted_task():
            time = time_combobox.get()
            new_task = task_entry.get().strip()
            if not time or not new_task:
                messagebox.showerror("Input Error", "Please select a time and enter a new task.")
                return
            try:
                datetime.datetime.strptime(time.split(" - ")[0], '%I:%M %p')
                self.adjust_task(time, new_task)
                adjust_window.destroy()
                messagebox.showinfo("Task Adjusted", f"Task at {time} has been adjusted.")
            except ValueError:
                messagebox.showerror("Invalid Time", "Please select a valid time slot.")

        save_button = ttk.Button(adjust_window, text="Save", command=save_adjusted_task, style="Success.TButton")
        save_button.pack(pady=20)

    def add_target_ui(self):
        target_window = tk.Toplevel()
        target_window.title("Add Target")
        target_window.geometry("500x300")
        target_window.resizable(False, False)

        ttk.Label(target_window, text="Add Target", font=("Helvetica", 16, "bold")).pack(pady=10)

        form_frame = ttk.Frame(target_window)
        form_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Target:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        target_entry = ttk.Entry(form_frame, width=35, font=("Helvetica", 12))
        target_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Deadline (YYYY-MM-DD):", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        deadline_entry = ttk.Entry(form_frame, width=35, font=("Helvetica", 12))
        deadline_entry.grid(row=1, column=1, padx=5, pady=5)

        def save_target():
            target = target_entry.get().strip()
            deadline = deadline_entry.get().strip()
            if not target or not deadline:
                messagebox.showerror("Input Error", "Please enter both target and deadline.")
                return
            try:
                datetime.datetime.strptime(deadline, '%Y-%m-%d')
                self.add_target(target, deadline)
                target_window.destroy()
                messagebox.showinfo("Target Added", f"Target '{target}' has been added.")
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
        
        save_button = ttk.Button(target_window, text="Save", command=save_target, style="Success.TButton")
        save_button.pack(pady=20)

    def add_yearly_task_ui(self):
        yearly_task_window = tk.Toplevel()
        yearly_task_window.title("Add Yearly Task")
        yearly_task_window.geometry("500x300")
        yearly_task_window.resizable(False, False)

        ttk.Label(yearly_task_window, text="Add Yearly Task", font=("Helvetica", 16, "bold")).pack(pady=10)

        form_frame = ttk.Frame(yearly_task_window)
        form_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Yearly Task:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        yearly_task_entry = ttk.Entry(form_frame, width=35, font=("Helvetica", 12))
        yearly_task_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Deadline (YYYY-MM-DD):", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        deadline_entry = ttk.Entry(form_frame, width=35, font=("Helvetica", 12))
        deadline_entry.grid(row=1, column=1, padx=5, pady=5)

        def save_yearly_task():
            yearly_task = yearly_task_entry.get().strip()
            deadline = deadline_entry.get().strip()
            if not yearly_task or not deadline:
                messagebox.showerror("Input Error", "Please enter both yearly task and deadline.")
                return
            try:
                datetime.datetime.strptime(deadline, '%Y-%m-%d')
                self.add_yearly_task(yearly_task, deadline)
                yearly_task_window.destroy()
                messagebox.showinfo("Yearly Task Added", f"Yearly task '{yearly_task}' has been added.")
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
        
        save_button = ttk.Button(yearly_task_window, text="Save", command=save_yearly_task, style="Success.TButton")
        save_button.pack(pady=20)

    def add_complex_task_ui(self):
        complex_task_window = tk.Toplevel()
        complex_task_window.title("Add Complex Task")
        complex_task_window.geometry("500x300")
        complex_task_window.resizable(False, False)

        ttk.Label(complex_task_window, text="Add Complex Task", font=("Helvetica", 16, "bold")).pack(pady=10)

        form_frame = ttk.Frame(complex_task_window)
        form_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Complex Task:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        complex_task_entry = ttk.Entry(form_frame, width=35, font=("Helvetica", 12))
        complex_task_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="Deadline (YYYY-MM-DD):", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        deadline_entry = ttk.Entry(form_frame, width=35, font=("Helvetica", 12))
        deadline_entry.grid(row=1, column=1, padx=5, pady=5)

        def save_complex_task():
            complex_task = complex_task_entry.get().strip()
            deadline = deadline_entry.get().strip()
            if not complex_task or not deadline:
                messagebox.showerror("Input Error", "Please enter both complex task and deadline.")
                return
            try:
                datetime.datetime.strptime(deadline, '%Y-%m-%d')
                self.add_complex_task(complex_task, deadline)
                complex_task_window.destroy()
                messagebox.showinfo("Complex Task Added", f"Complex task '{complex_task}' has been added.")
            except ValueError:
                messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
        
        save_button = ttk.Button(complex_task_window, text="Save", command=save_complex_task, style="Success.TButton")
        save_button.pack(pady=20)

    def natural_language_input_ui(self):
        nl_window = tk.Toplevel()
        nl_window.title("Natural Language Input")
        nl_window.geometry("600x400")
        nl_window.resizable(False, False)

        ttk.Label(nl_window, text="Natural Language Input", font=("Helvetica", 16, "bold")).pack(pady=10)

        form_frame = ttk.Frame(nl_window)
        form_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        ttk.Label(form_frame, text="Enter your request or command:", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        command_entry = ttk.Entry(form_frame, width=40, font=("Helvetica", 12))
        command_entry.grid(row=0, column=1, padx=5, pady=5)

        process_button = ttk.Button(form_frame, text="Process", command=lambda: self.process_nlp_command(command_entry, output_text), style="Primary.TButton")
        process_button.grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Label(form_frame, text="Output:", font=("Helvetica", 12)).grid(row=2, column=0, padx=5, pady=5, sticky='ne')
        output_text = tk.Text(form_frame, height=5, width=40, state='disabled', wrap='word', font=("Helvetica", 12))
        output_text.grid(row=2, column=1, padx=5, pady=5)

    def process_nlp_command(self, command_entry, output_text):
        command = command_entry.get().strip()
        if not command:
            messagebox.showerror("Input Error", "Please enter a command.")
            return

        # Use NLP model to parse the command
        # For simplicity, we'll use simple keyword-based parsing enhanced by the model
        feedback = ""
        if "add task" in command.lower():
            task = command.lower().replace("add task", "").strip()
            if task:
                self.daily_tasks.append(task.capitalize())
                feedback = f"Task '{task.capitalize()}' has been added to your daily tasks."
                self.refresh_and_generate_schedule()
            else:
                feedback = "No task specified to add."
        elif "add target" in command.lower():
            parts = command.lower().split("add target")
            if len(parts) > 1:
                target_info = parts[1].strip().split(" by ")
                if len(target_info) == 2:
                    target, deadline = target_info
                    try:
                        datetime.datetime.strptime(deadline.strip(), '%Y-%m-%d')
                        self.add_target(target.strip().capitalize(), deadline.strip())
                        feedback = f"Target '{target.strip().capitalize()}' added with deadline {deadline.strip()}."
                        self.refresh_and_generate_schedule()
                    except ValueError:
                        feedback = "Invalid date format. Use YYYY-MM-DD."
                else:
                    feedback = "Please specify target and deadline using 'by'. Example: Add target Finish report by 2024-12-31."
            else:
                feedback = "Invalid command format."
        elif "add yearly task" in command.lower():
            parts = command.lower().split("add yearly task")
            if len(parts) > 1:
                task_info = parts[1].strip().split(" by ")
                if len(task_info) == 2:
                    task, deadline = task_info
                    try:
                        datetime.datetime.strptime(deadline.strip(), '%Y-%m-%d')
                        self.add_yearly_task(task.strip().capitalize(), deadline.strip())
                        feedback = f"Yearly task '{task.strip().capitalize()}' added with deadline {deadline.strip()}."
                        self.refresh_and_generate_schedule()
                    except ValueError:
                        feedback = "Invalid date format. Use YYYY-MM-DD."
                else:
                    feedback = "Please specify yearly task and deadline using 'by'. Example: Add yearly task Complete certification by 2025-06-30."
            else:
                feedback = "Invalid command format."
        elif "add complex task" in command.lower():
            parts = command.lower().split("add complex task")
            if len(parts) > 1:
                task_info = parts[1].strip().split(" by ")
                if len(task_info) == 2:
                    task, deadline = task_info
                    try:
                        datetime.datetime.strptime(deadline.strip(), '%Y-%m-%d')
                        self.add_complex_task(task.strip().capitalize(), deadline.strip())
                        feedback = f"Complex task '{task.strip().capitalize()}' added with deadline {deadline.strip()}."
                        self.refresh_and_generate_schedule()
                    except ValueError:
                        feedback = "Invalid date format. Use YYYY-MM-DD."
                else:
                    feedback = "Please specify complex task and deadline using 'by'. Example: Add complex task Launch project by 2024-11-15."
            else:
                feedback = "Invalid command format."
        else:
            feedback = "Command not recognized. Try 'add task [task name]', 'add target [target] by [YYYY-MM-DD]', 'add yearly task [task] by [YYYY-MM-DD]', or 'add complex task [task] by [YYYY-MM-DD]'."

        # Display feedback
        output_text.config(state='normal')
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, feedback)
        output_text.config(state='disabled')

        # Clear the command entry
        command_entry.delete(0, tk.END)

    def start_notification_thread(self):
        notification_thread = threading.Thread(target=self.notification_loop, daemon=True)
        notification_thread.start()

    def notification_loop(self):
        while True:
            now = datetime.datetime.now().strftime("%I:%M %p")
            if now in self.schedule:
                task_info = self.schedule[now]
                # Show notification (use a separate thread to avoid blocking)
                threading.Thread(target=lambda: messagebox.showinfo("Task Reminder", f"It's time for: {task_info}"), daemon=True).start()
            time.sleep(60)  # Check every minute

    # Ensure the schedule refreshes and regenerates after adjustments
    def refresh_and_generate_schedule(self):
        self.generate_daily_schedule()
        self.refresh_schedule_display()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    daily_manager = DailyLifeManager()
    daily_manager.run()
