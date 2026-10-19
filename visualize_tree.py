"""
Vertical Tree Visualization for MCTS Agent
Generates a compact, easy-to-explain hierarchical tree visualization.
"""

import time
import os
from datetime import datetime
from pathlib import Path
from pyvis.network import Network
from game_engine.state import GameState
from agents.advanced import MCTSAgent, MCTSNode


def run_visualization():
    """
    Run MCTS agent and generate vertical tree visualization.
    """
    print("=" * 60)
    print("MCTS Vertical Tree Visualization")
    print("=" * 60)
    
    # Initialize game with a fresh board
    print("\n1. Initializing game state...")
    game_state = GameState(num_players=2)
    
    # Create MCTS agent
    print("2. Creating MCTS agent...")
    mcts_agent = MCTSAgent(player_id=0, time_limit=3.0)
    
    # Build MCTS tree (3 seconds)
    print("3. Running MCTS for 3 seconds...")
    root = MCTSNode(game_state.get_state_copy())
    
    start_time = time.time()
    simulations = 0
    while time.time() - start_time < 3.0:
        node = mcts_agent._select(root, mcts_agent.player_id)
        result = mcts_agent._simulate(node.state)
        node.backpropagate(result)
        simulations += 1
    
    elapsed = time.time() - start_time
    print(f"   [OK] Completed {simulations} simulations in {elapsed:.2f}s")
    
    # Export tree structure
    print("4. Exporting tree structure...")
    tree_data = mcts_agent.export_tree_structure(
        root_node=root,
        max_depth=3,
        top_k=3
    )
    
    print(f"   [OK] Nodes: {len(tree_data['nodes'])}")
    print(f"   [OK] Edges: {len(tree_data['edges'])}")
    
    # Create PyVis network with hierarchical layout
    print("5. Creating visualization...")
    net = Network(
        height='900px',
        width='100%',
        bgcolor='#222222',
        font_color='white',
        directed=True
    )
    
    # Aggressive "Squishy" Layout Configuration
    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 250,
          "nodeSpacing": 10,
          "treeSpacing": 10,
          "blockShifting": false,
          "edgeMinimization": false,
          "parentCentralization": true
        }
      },
      "physics": {
        "enabled": false,
        "hierarchicalRepulsion": {
          "nodeDistance": 0,
          "centralGravity": 0.0,
          "springLength": 0,
          "damping": 1
        }
      },
      "edges": {
        "smooth": {
          "type": "cubicBezier",
          "forceDirection": "vertical",
          "roundness": 0.5
        },
        "color": {
          "color": "#848484",
          "highlight": "#848484"
        }
      }
    }
    """)
    
    # Add nodes
    for node in tree_data['nodes']:
        net.add_node(
            node['id'],
            label=node['label'],
            color=node['color'],
            size=node['size'],
            title=f"Visits: {node['visits']}<br>Win Rate: {node['win_rate']*100:.1f}%"
        )
    
    # Add edges
    for edge in tree_data['edges']:
        net.add_edge(edge['from'], edge['to'])
    
    # Save to data folder in timestamped game directory
    print("6. Saving visualization...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create game folder structure
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    game_folder = data_dir / f"game_{timestamp}"
    game_folder.mkdir(exist_ok=True)
    
    # Save HTML file
    html_filename = f"mcts_tree_vertical.html"
    html_filepath = game_folder / html_filename
    
    net.save_graph(str(html_filepath))
    
    print(f"\n[OK] Visualization saved to: {html_filepath}")
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print(f"\nOpen the file in your browser to view the interactive tree:")
    print(f"  {html_filepath.absolute()}")
    
    return str(html_filepath)


if __name__ == "__main__":
    run_visualization()
