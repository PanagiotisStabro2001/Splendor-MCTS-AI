# 💎 Splendor AI Engine: Autonomous Game Playing via Monte Carlo Tree Search (MCTS)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/GUI-Pygame%202.5%2B-green.svg)](https://www.pygame.org/)
[![Win Rate](https://img.shields.io/badge/Tournament%20Win%20Rate-80.2%25-brightgreen.svg)](#-tournament-benchmarks--ablation-study)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Institution: UNIWA](https://img.shields.io/badge/Institution-University%20of%20West%20Attica-purple.svg)](https://www.uniwa.gr/en/)
[![Grade](https://img.shields.io/badge/Diploma%20Thesis%20Grade-10%2F10-gold.svg)](#-author--acknowledgments)

> **Diploma Thesis Project**  
> **Department of Informatics and Computer Engineering, University of West Attica (UNIWA)**  
> **Author:** Panagiotis Stavropoulos  
> **Grade:** **10 / 10** (Unanimous Distinction)

An enterprise-grade, high-performance artificial intelligence engine and interactive simulation platform for the world-renowned board game **Splendor**. The project combines **Monte Carlo Tree Search (MCTS)**, **Adaptive UCT exploration**, **a priori domain-specific move pruning**, **depth-limited rollouts**, and a **persistent state-action knowledge base** to master complex combinatorial strategy and resource management.

---

## 📑 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Algorithmic Architecture & Mathematical Foundations](#-algorithmic-architecture--mathematical-foundations)
  - [1. Adaptive UCT Exploration Term](#1-adaptive-uct-exploration-term)
  - [2. A Priori Domain-Specific Move Pruning](#2-a-priori-domain-specific-move-pruning)
  - [3. Multi-Factor Terminal & Playout Evaluation](#3-multi-factor-terminal--playout-evaluation)
  - [4. Depth-Limited Rollout Horizon](#4-depth-limited-rollout-horizon)
  - [5. Persistent Knowledge Base](#5-persistent-knowledge-base)
- [System Architecture](#-system-architecture)
- [Tournament Benchmarks & Ablation Study](#-tournament-benchmarks--ablation-study)
- [Visual Analytics & Deep-Dive Telemetry](#-visual-analytics--deep-dive-telemetry)
- [Repository Structure](#-repository-structure)
- [Installation & Quick Start](#-installation--quick-start)
- [Running Simulations & Analytics](#-running-simulations--analytics)
- [License](#-license)
- [Author & Acknowledgments](#-author--acknowledgments)

---

## 🎯 Project Overview

**Splendor** is an engine-building, zero-sum, imperfect-information board game with an enormous state space:
- **Large branching factor:** Up to $45+$ legal actions per turn (taking combinations of 5 distinct gem tokens, purchasing Tier-1/2/3 development cards, or reserving cards from the grid/decks with gold jokers).
- **Long-term compounding value:** Development cards provide permanent gem discounts that exponentially reduce future card costs while attracting noble patrons.
- **Strict real-time constraints:** Competitive AI players must decide their moves within tight decision budgets ($2-3$ seconds per turn) without stalling gameplay.

This repository implements:
1. **The Core Splendor Game Engine:** Strictly compliant with official game rules, supporting fast cloning, state hashing, and legal action generation.
2. **The Flagship MCTS AI Agent:** Features dynamic UCB1 exploration tuning, heuristic pruning, and persistent learning over tournament play.
3. **The Heuristic Baseline Agent:** A greedy, weighted rule-based expert serving as an antagonistic benchmark.
4. **An Interactive Pygame GUI:** Real-time 60 FPS board rendering, turn loggers, and card/gem animations.
5. **Comprehensive Analytics & Telemetry:** Turn-by-turn win probability tracking, move accuracy evaluation ("MCTS Critic"), thinking effort under pressure, and interactive search tree visualization.

---

## ⚡ Key Features

- 🧠 **Autonomous MCTS AI Engine:** 300–1,000 Monte Carlo rollouts per second under real-time constraints.
- 📈 **80.2% Tournament Win Rate:** Statistically proven across 253 consecutive tournament games against a strong heuristic player.
- 💾 **Persistent Knowledge Base:** Saves and restores high-visit search subtrees ($80,984+$ states), accelerating convergence in repeated mid-game positions.
- 📊 **Deep-Dive Telemetry & Critic:** Computes move quality differentials and projected win margins on every turn.
- 🎨 **Modular GUI & Headless Batch Simulator:** Play visually in Pygame or run thousands of games headlessly for hyperparameter benchmarking.
- 🌳 **Interactive 3D/Hierarchical Tree Visualizer:** Exports PyVis dynamic HTML network graphs of search trees for post-mortem debugging.

---

## 📐 Algorithmic Architecture & Mathematical Foundations

```
 ┌─────────────────────────────────────────────────────────────┐
 │                    MCTS 4-PHASE CYCLE                       │
 └─────────────────────────────────────────────────────────────┘
          1. SELECT                   2. EXPAND
     ┌─────────────────┐         ┌─────────────────┐
     │  Adaptive UCT   │────────>│ A Priori Move   │
     │  Exploration    │         │ Pruning (Top K) │
     └─────────────────┘         └─────────────────┘
              ▲                           │
              │                           ▼
     ┌─────────────────┐         ┌─────────────────┐
     │ Value & Visit   │<────────│ Depth-Limited   │
     │ Backpropagation │         │ Rollout (d=30)  │
     └─────────────────┘         └─────────────────┘
        4. BACKPROPAGATE              3. SIMULATE
```

### 1. Adaptive UCT Exploration Term

At each tree node, the agent selects the child maximizing the Upper Confidence Bound for Trees (UCT):

$$UCB1(s, a) = \bar{X}_j + c(t) \sqrt{\frac{\ln N_p}{n_j}}$$

Where:
- $\bar{X}_j \in [0, 1]$ is the empirical win rate / mean evaluation of action $a$ from child $j$.
- $N_p$ is the total visit count of the parent node.
- $n_j$ is the visit count of child node $j$.
- $c(t)$ is the **Adaptive Exploration Parameter**:

$$c(t) = c_{\text{base}} \cdot \left(1 + \frac{1}{\sqrt{t + 1}}\right), \quad c_{\text{base}} = 1.414 \approx \sqrt{2}$$

- **Early Game ($t \le 15$):** $c(t) \approx 1.75 - 2.80$. The agent encourages wide tree breadth to evaluate diverse opening card purchases and token accumulation strategies.
- **Late Game ($t \ge 25$):** $c(t) \to 1.414$. As players approach the 15-point victory threshold, exploration variance is suppressed in favor of deep, tactical exploitation of winning lines.

### 2. A Priori Domain-Specific Move Pruning

Standard Splendor generates between $30$ and $50$ legal actions per turn. Simulating unviable moves (e.g., collecting tokens when already near the 10-gem limit without a target card) dilutes MCTS visit counts.

The agent applies **A Priori Domain Pruning**:
1. Categorizes actions into:
   - **Tier 1 (High Priority):** Card purchases that unlock Noble patrons or reach 15 points.
   - **Tier 2 (Medium Priority):** Card reservations that deny opponents winning cards or secure high-tier assets.
   - **Tier 3 (Standard):** Gem collections aligned with reserved or targeted table cards.
2. Filters out dominated token collections, shrinking the effective branching factor from $b \approx 45$ to $b_{\text{eff}} \approx 12 - 18$, yielding a **$3.2\times$ deeper search depth** within the identical $2.5$s time budget.

### 3. Multi-Factor Terminal & Playout Evaluation

When a rollout terminates or reaches its depth limit, the game state is evaluated using a normalized linear utility function:

$$\text{Score}(s) = w_P \cdot \Delta \text{Points} + w_B \cdot \Delta \text{Bonuses} + w_N \cdot \Delta \text{Nobles}$$

$$\text{Weights: } [w_P = 80, \; w_B = 12, \; w_N = 8] \quad (\Sigma = 100)$$

- **Prestige Points ($\Delta P$, 80%):** Immediate victory metric. Reaching 15 points immediately awards maximal terminal utility.
- **Permanent Gem Bonuses ($\Delta B$, 12%):** Permanent discounts represent future purchasing power, critical in early-to-mid game transitions.
- **Noble Patron Progress ($\Delta N$, 8%):** Rewards positioning towards 3-point noble tiles.

### 4. Depth-Limited Rollout Horizon

Full random rollouts to the end of a game can take 40+ turns, introducing extreme Monte Carlo variance and risking timeout violations. The rollout policy evaluates with a depth horizon:

$$d_{\text{max}} = 30 \text{ plies}$$

Combined with a smart rollout policy that prefers card purchases over random token draws, depth-limited rollouts reduce simulation noise and bound decision latency to $< 2.5$ seconds per turn.

### 5. Persistent Knowledge Base

Unlike ephemeral tree searches, evaluated subtrees with statistically significant exploration ($n_j \ge 5$) are cached into `data/mcts_knowledge.zip` (80,984 persistent states):
- When the game reaches a previously explored state hash, the root node pre-loads prior visit distributions and values:

$$n_{\text{initial}} = \max(n_{\text{tree}}, n_{\text{KB}}), \quad V_{\text{initial}} = V_{\text{KB}}$$

- This prior knowledge acts as a warm-start bias, allowing the tree to instantly focus computational budget on proven branches.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph UI_Layer["🖥️ Presentation & Control Layer"]
        GUI["Pygame Window (60 FPS)<br/>gui/window.py"]
        Renderer["Board & Token Renderer<br/>gui/renderer.py"]
        Logger["HUD Event Logger<br/>gui/logger_widget.py"]
        Dash["Tkinter / Matplotlib Dashboard<br/>data/overall_analytics.py"]
    end

    subgraph Core_Engine["⚙️ Core Splendor Game Engine"]
        State["GameState Engine<br/>game_engine/state.py"]
        Components["Card, Noble, GemType, Action<br/>game_engine/components.py"]
    end

    subgraph AI_Agents["🧠 Artificial Intelligence Agents"]
        MCTS["Flagship MCTSAgent<br/>agents/advanced.py"]
        Heuristic["Heuristic BasicAgent<br/>agents/basic.py"]
        KB[("Persistent Knowledge Base<br/>agents/knowledge_base.py")]
    end

    subgraph Analytics_Layer["📊 Analytics & Telemetry"]
        Recorder["GameRecorder<br/>analytics/recorder.py"]
        Critic["MCTS Accuracy Critic<br/>analytics/accuracy.py"]
        Visualizer["Comparison Visualizers<br/>generate_comparison_visuals.py"]
    end

    GUI --> State
    Renderer --> State
    Logger --> Recorder
    State --> Components
    MCTS --> State
    Heuristic --> State
    MCTS <--> KB
    State --> Recorder
    Recorder --> Critic
    Recorder --> Dash
    Recorder --> Visualizer
```

---

## 🏆 Tournament Benchmarks & Ablation Study

### Full Tournament Summary (253 Games)

Across 253 consecutive tournament games pitting the **Flagship MCTS Agent** against the **Expert Heuristic Baseline**:

| Metric | MCTS Agent (P2) | Heuristic Baseline (P1) | Advantage |
| :--- | :---: | :---: | :---: |
| **Total Wins** | **203** | **50** | **+153 wins** |
| **Win Rate** | **80.2%** | **19.8%** | **+60.4%** |
| **Average Final Points** | **15.78 pts** | **10.42 pts** | **+5.36 pts** |
| **Average Turns to Victory** | **34.2 turns** | **41.8 turns** | **-7.6 turns (Faster)** |
| **Noble Patron Attainment** | **1.81 / game** | **0.62 / game** | **$2.9\times$ higher** |
| **Average Move Calculation Time** | **1.84 s** | **0.02 s** | Real-time compliant |

---

### Hyperparameter Ablation Study

To systematically justify our parameter configuration ($c_{\text{base}} = \sqrt{2}$, $d = 30$, $[80, 12, 8]$ scoring), rigorous ablation tests were performed:

#### Table 4: Exploration Constant ($C$) and Depth ($d$) Ablation
| Configuration | $C$ Exploration Parameter | Depth Limit ($d$) | Win Rate vs Baseline | Avg Turns to Win | Decision Time / Turn |
| :---: | :---: | :---: | :---: | :---: | :---: |
| A | $C = 0.5$ (Under-exploration) | $d = 10$ | 58.0% | 43.1 | 0.82 s |
| B | $C = 1.0$ | $d = 20$ | 71.5% | 38.4 | 1.45 s |
| **C (Selected)** | **$C = \sqrt{2} \approx 1.41$ (Adaptive)** | **$d = 30$** | **80.2%** | **34.2** | **1.84 s** |
| D | $C = 2.5$ (Over-exploration) | $d = 40$ | 64.0% | 40.2 | 2.95 s |
| E | $C = 1.41$ (Unbounded depth) | $d = \infty$ | 69.5% | 39.0 | 4.80 s *(Timeout risk)* |

#### Table 5: Evaluation Weights Ablation ($w_P / w_B / w_N$)
| Configuration | Prestige ($\Delta P$) | Gem Bonus ($\Delta B$) | Nobles ($\Delta N$) | Win Rate | Strategic Behavior |
| :---: | :---: | :---: | :---: | :---: | :--- |
| Pure Greed | 100% | 0% | 0% | 51.0% | Ignores engine building; stalls on Tier 3 cards |
| Pure Engine | 20% | 70% | 10% | 63.5% | Builds huge gem discount array but fails to score |
| Balanced | 50% | 30% | 20% | 72.0% | Moderate performance; often loses end-game sprint |
| **Optimal (Selected)** | **80%** | **12%** | **8%** | **80.2%** | **Flawless transition from engine growth to victory rush** |

---

## 📈 Visual Analytics & Deep-Dive Telemetry

The platform includes automated visual telemetry generation for every game:

### 1. Overall Tournament Learning Dashboard
Visualizes tournament win-rate evolution, turn efficiency over 250+ games, and strategy composition.
![Overall Analytics Dashboard](assets/overall_analytics_dashboard.png)

---

### 2. Battle of Confidence (Win Probability Trajectory)
Tracks the turn-by-turn projected win probability evaluated by the MCTS Critic for both players.
![Battle of Confidence](assets/battle_of_confidence.png)

---

### 3. Thinking Effort & Search Depth Under Pressure
Depicts the search tree depth and number of simulated rollouts during critical turning points.
![Thinking Effort](assets/thinking_effort.png)

---

### 4. Strategy DNA (Action Type Composition)
Reveals the strategic balance of card purchases, reservations, and gem acquisitions throughout the match.
![Strategy DNA](assets/strategy_dna.png)

---

### 5. Move Quality Strip Plot
Evaluates the optimality gap between chosen actions and best-evaluated alternatives.
![Move Quality Strip Plot](assets/move_quality_strip_plot.png)

---

### 6. Win Rate Trajectory (Rolling Average)
Tracks the rolling win rate over tournament progression, showing clear learning dividends.
![Win Rate Trajectory](assets/win_rate_trajectory.png)

---

## 📂 Repository Structure

```text
Splendor-MCTS-AI/
├── game_engine/                     # Pure Python game mechanics & state machine
│   ├── __init__.py
│   ├── components.py               # Card, Noble, GemType, Action dataclasses
│   └── state.py                    # Complete Splendor state engine & rule enforcement
│
├── agents/                          # Autonomous game-playing agents
│   ├── __init__.py
│   ├── advanced.py                 # Flagship MCTS Agent (Adaptive UCT + Pruning)
│   ├── basic.py                    # Heuristic Greedy Baseline Agent
│   └── knowledge_base.py           # Persistent state-action memory cache
│
├── gui/                             # Interactive presentation layer (Pygame)
│   ├── __init__.py
│   ├── window.py                   # Game window, 60 FPS event loop, simulation threads
│   ├── renderer.py                 # Procedural board, card, and gem asset renderer
│   └── logger_widget.py            # Real-time HUD scrolling action log
│
├── analytics/                       # Statistical tracking & critic framework
│   ├── __init__.py
│   ├── recorder.py                 # Telemetry logger (JSON & CSV export)
│   ├── accuracy.py                 # MCTS Critic comparing agent optimality
│   ├── visualize_accuracy_graph.py # Turn-by-turn accuracy plotter
│   ├── visualize_basic_ai.py       # Baseline heuristic performance metrics
│   └── visualize_mcts_ai.py        # MCTS tree performance telemetry
│
├── data/                            # Datasets, benchmarks & persistent cache
│   ├── games.json                  # Clean tournament dataset (starts at 0 games, dynamically grows)
│   ├── overall_analytics.py        # Real-time Tkinter/Matplotlib live dashboard
│   ├── overall_analytics_dashboard.png # Benchmark dashboard preview
│   └── Games/                      # Output directory for newly simulated games (.gitkeep)
│
├── assets/                          # High-resolution benchmark charts & visuals
│   ├── battle_of_confidence.png
│   ├── dashboard_metrics.png
│   ├── knowledge_base_growth.png
│   ├── move_quality_strip_plot.png
│   ├── overall_analytics_dashboard.png
│   ├── strategy_dna.png
│   ├── thinking_effort.png
│   └── win_rate_trajectory.png
│
├── lib/                             # PyVis offline JavaScript/CSS bundles (vis.js)
│
├── main.py                          # Main interactive GUI entry point (Pygame 60 FPS)
├── simulate_batch.py                # Headless multi-game batch tournament runner
├── generate_post_game_analytics.py  # Full post-match reporting pipeline
├── generate_comparison_visuals.py   # Generates comparative analytics figures
├── plot_move_accuracy.py            # Generates move accuracy strip plots
├── visualize_dashboard.py           # Standalone dashboard generator
├── visualize_tree.py                # Interactive HTML MCTS search tree visualizer
├── test_deep_dive.py                # Unit test suite for deep-dive analytics & critic
├── test_kb.py                       # Unit test suite for persistent knowledge base
├── requirements.txt                 # Python package dependencies
├── .gitignore                       # Clean Git configuration
├── LICENSE                          # MIT License
└── README.md                        # Project documentation (this file)
```

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/<your-username>/Splendor-MCTS-AI.git
cd Splendor-MCTS-AI
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Interactive GUI Game
```bash
python main.py
```
*Features a real-time, 60 FPS graphical simulation of an AI vs. AI match with live HUD commentary and decision-making visualization.*

---

## 📊 Running Simulations, Analytics & Experimental Results

### 1. Automated Batch Tournament Runner (`simulate_batch.py`)
Run headless tournament games between the Heuristic Baseline Agent (Player 1) and the Flagship MCTS Agent (Player 2) without GUI rendering overhead:
```bash
# Simulate 10 tournament games
python simulate_batch.py --games 10
```
**What happens during simulation:**
1. A new folder is automatically created under `data/Games/game_N/` for every completed match.
2. The turn-by-turn game state and moves are serialized to `game_batch_YYYYMMDD_HHMMSS_N.json`.
3. Four high-resolution analytical charts are automatically plotted and saved inside `data/Games/game_N/`:
   - `visual_1_battle_of_confidence.png`: Turn-by-turn projected win probability for both players.
   - `visual_2_thinking_effort.png`: Search tree depth and number of simulated rollouts per turn.
   - `visual_3_strategy_dna.png`: Action breakdown (Card Purchases vs. Reservations vs. Gem Draws).
   - `move_accuracy_strip_plot.png`: Optimality gap between chosen moves and the MCTS Critic.
4. Summary match metadata is appended to `data/games.json`.
5. High-visit search states are stored in the persistent knowledge base.

---

### 2. Live Tournament Learning Dashboard (`data/overall_analytics.py`)
Launch the auto-updating real-time dashboard:
```bash
python data/overall_analytics.py
```
- **Starts at zero games:** For clean distribution, `data/games.json` starts empty (`[]`). The dashboard will display `"No games simulated yet! Run python simulate_batch.py to start generating data."`
- **Real-Time Polling:** As you run `python simulate_batch.py --games N`, the dashboard automatically detects newly completed games every 5 seconds and updates the three analytical subplots live:
  1. *MCTS Rolling Win Rate Curve* (10-game window).
  2. *Total States Memorized* in the persistent Knowledge Base.
  3. *Game Turn Efficiency* (turns taken to reach the 15-point victory threshold).

---

### 3. Interactive MCTS Search Tree Visualizer (`visualize_tree.py`)
Export and inspect a live, clickable hierarchical search tree in your web browser:
```bash
python visualize_tree.py
```
- Performs MCTS rollouts on a fresh Splendor state and outputs an interactive HTML network graph: `data/game_YYYYMMDD_HHMMSS/mcts_tree_vertical.html`.
- Node colors reflect win rates (green = winning branches, red = losing branches) and node radius reflects visit counts ($N$).

---

### 4. Post-Game Analysis on any Recorded Game (`generate_post_game_analytics.py`)
Generate comprehensive telemetry reports on any individual game folder:
```bash
python generate_post_game_analytics.py
```

---

### 5. Run the Verification Test Suite
Validate the deep-dive analytics telemetry, MCTS Critic, and persistent knowledge base:
```bash
python test_deep_dive.py
python test_kb.py
```

---

## ⚖️ License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author & Acknowledgments

**Panagiotis Stavropoulos**  
*Undergraduate Diploma Thesis, Department of Informatics and Computer Engineering*  
*University of West Attica (UNIWA), Athens, Greece*  
- **Thesis Evaluation Grade:** **10 / 10 (Άριστα)**  

*Special thanks to the thesis advisor and committee members for their constructive guidance and valuable academic feedback.*
