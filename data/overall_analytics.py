import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def load_data():
    master_file = Path("games.json")
    if not master_file.exists():
        master_file = Path("data/games.json")
        
    if not master_file.exists():
        return []
        
    with open(master_file, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🧠 Splendor MCTS Learning Dashboard")
        self.geometry("1000x800")
        
        # --- Top Frame for Metrics ---
        self.top_frame = tk.Frame(self, bg="#2c3e50", pady=15)
        self.top_frame.pack(fill=tk.X)
        
        tk.Label(self.top_frame, text="🧠 Splendor MCTS Learning Dashboard", font=("Helvetica", 16, "bold"), fg="white", bg="#2c3e50").pack()
        
        self.metrics_frame = tk.Frame(self.top_frame, bg="#2c3e50")
        self.metrics_frame.pack(pady=10)
        
        self.metrics_label = tk.Label(self.metrics_frame, text="Loading...", font=("Helvetica", 12), fg="#ecf0f1", bg="#2c3e50")
        self.metrics_label.pack()
        
        # --- Matplotlib Figures ---
        self.fig = plt.Figure(figsize=(10, 6), dpi=100)
        self.fig.patch.set_facecolor('#f5f6fa')
        
        self.ax1 = self.fig.add_subplot(221)
        self.ax2 = self.fig.add_subplot(222)
        self.ax3 = self.fig.add_subplot(212)
        
        # --- Embed in Tkinter ---
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Data tracking
        self.last_game_count = -1
        
        # Start auto-update loop
        self.update_dashboard()

    def update_dashboard(self):
        games = load_data()
        
        # Only redraw if there are new games
        if len(games) > self.last_game_count:
            self.last_game_count = len(games)
            self.refresh_plots(games)
            
        # Schedule next update in 5000ms (5 seconds)
        self.after(5000, self.update_dashboard)

    def refresh_plots(self, games):
        if not games:
            self.metrics_label.config(text="No games simulated yet! Run `python simulate_batch.py` to start generating data.")
            return
            
        mcts_wins = 0
        basic_wins = 0
        
        game_numbers = []
        mcts_win_flags = []
        kb_sizes = []
        total_turns = []
        
        for i, g in enumerate(games):
            metadata = g.get('metadata', {})
            winner = metadata.get('winner', -1)
            
            # MCTS is Player 1 (index 1), Basic is Player 0 (index 0)
            if winner == 1:
                mcts_wins += 1
                mcts_won = True
            else:
                basic_wins += 1
                mcts_won = False
                
            mcts_kb_size = g.get('mcts_kb_size')
            if not mcts_kb_size:  # handles None or 0
                if len(kb_sizes) > 0:
                    mcts_kb_size = kb_sizes[-1]
                else:
                    mcts_kb_size = 0
            
            game_numbers.append(i + 1)
            mcts_win_flags.append(1 if mcts_won else 0)
            kb_sizes.append(mcts_kb_size)
            total_turns.append(metadata.get('total_turns', 0))
        
        # Calculate rolling win rate
        window = min(10, len(mcts_win_flags))
        if window == 0:
            window = 1
            
        rolling_win_rate = []
        for i in range(len(mcts_win_flags)):
            start_idx = max(0, i - window + 1)
            window_slice = mcts_win_flags[start_idx:i+1]
            rolling_win_rate.append((sum(window_slice) / len(window_slice)) * 100)
            
        # Update text
        overall_win_rate = (mcts_wins / len(games)) * 100 if len(games) > 0 else 0
        latest_kb = kb_sizes[-1] if kb_sizes else 0
        
        metrics_text = (
            f"Total Games: {len(games)}  |  "
            f"MCTS Wins: {mcts_wins} - Normal AI Wins: {basic_wins}  |  "
            f"Overall Win Rate: {overall_win_rate:.1f}%  |  "
            f"Total States Memorized: {latest_kb}"
        )
        self.metrics_label.config(text=metrics_text)

        # Clear existing axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()

        # 1. Win Rate Subplot
        self.ax1.plot(game_numbers, rolling_win_rate, color='#e74c3c', marker='o', markersize=4, linestyle='-', linewidth=2)
        self.ax1.set_title("📈 MCTS Win Rate Over Time (Rolling Avg)", fontsize=10, fontweight='bold')
        self.ax1.set_xlabel("Game Number")
        self.ax1.set_ylabel("Win Rate (%)")
        self.ax1.set_ylim(-5, 105)
        self.ax1.grid(True, alpha=0.3)
        
        # 2. Knowledge Base Growth Subplot
        self.ax2.plot(game_numbers, kb_sizes, color='#3498db', marker='s', markersize=4, linestyle='-', linewidth=2)
        self.ax2.set_title("🧠 Knowledge Base Growth", fontsize=10, fontweight='bold')
        self.ax2.set_xlabel("Game Number")
        self.ax2.set_ylabel("States Memorized")
        self.ax2.grid(True, alpha=0.3)
        
        # 3. Turns to Win/Loss Subplot
        mcts_x = [game_numbers[i] for i in range(len(mcts_win_flags)) if mcts_win_flags[i] == 1]
        mcts_y = [total_turns[i] for i in range(len(mcts_win_flags)) if mcts_win_flags[i] == 1]
        
        basic_x = [game_numbers[i] for i in range(len(mcts_win_flags)) if mcts_win_flags[i] == 0]
        basic_y = [total_turns[i] for i in range(len(mcts_win_flags)) if mcts_win_flags[i] == 0]
        
        self.ax3.scatter(mcts_x, mcts_y, color='#e74c3c', label='MCTS Win', alpha=0.7, s=50)
        self.ax3.scatter(basic_x, basic_y, color='#3498db', label='Basic Win', alpha=0.7, s=50)
        self.ax3.set_title("⏱️ Game Efficiency (Total Turns per Game)", fontsize=10, fontweight='bold')
        self.ax3.set_xlabel("Game Number")
        self.ax3.set_ylabel("Total Turns")
        self.ax3.legend()
        self.ax3.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.canvas.draw()

def main():
    app = Dashboard()
    app.mainloop()

if __name__ == "__main__":
    main()
