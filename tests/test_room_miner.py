import pytest
from agents.brain.room_miner import RoomMinerRoutine

def test_room_miner_default_initialization():
    routine = RoomMinerRoutine()
    assert routine.selected_ores == ["fer"]

def test_room_miner_custom_ores():
    routine = RoomMinerRoutine(["fer", "Bronze", "COPPER_ORE"])
    assert "fer" in routine.selected_ores
    assert "bronze" in routine.selected_ores
    assert "cuivre" in routine.selected_ores

def test_sort_nodes_by_proximity():
    routine = RoomMinerRoutine()
    start = (0, 0)
    nodes = [
        {"x": 100, "y": 100},
        {"x": 10, "y": 10},
        {"x": 50, "y": 50}
    ]
    sorted_nodes = routine.sort_nodes_by_proximity(nodes, start_pos=start)
    assert sorted_nodes[0]["x"] == 10
    assert sorted_nodes[1]["x"] == 50
    assert sorted_nodes[2]["x"] == 100

def test_execute_room_mining_mines_only_selected_available():
    routine = RoomMinerRoutine(default_selected_ores=["fer"])
    
    nodes = [
        {"x": 100, "y": 200, "ore_type": "fer"},
        {"x": 300, "y": 400, "ore_type": "bronze"},
        {"x": 500, "y": 600, "ore_type": "fer"}
    ]
    
    moves = []
    clicks = []
    
    def fake_move(x, y):
        moves.append((x, y))
        
    def fake_click():
        clicks.append(True)
        
    # Tooltip simule le premier fer disponible, le bronze disponible mais non sélectionné, le 2e fer épuisé
    tooltip_responses = [
        {"resource_name": "Fer", "status": "available"},
        {"resource_name": "Bronze", "status": "available"},
        {"resource_name": "Fer", "status": "depleted"}
    ]
    tooltip_idx = [0]
    
    def fake_tooltip():
        idx = tooltip_idx[0]
        tooltip_idx[0] += 1
        return tooltip_responses[idx]

    result = routine.execute_room_mining(
        detected_nodes=nodes,
        selected_ores=["fer"],
        move_cursor_fn=fake_move,
        read_tooltip_fn=fake_tooltip,
        click_fn=fake_click,
        sleep_fn=lambda t: None
    )

    assert result["success"] is True
    assert result["inspected_count"] == 3
    assert result["mined_count"] == 1 # Seul le 1er fer est miné
    assert result["skipped_count"] == 2 # 1 bronze ignoré + 1 fer épuisé
    assert len(clicks) == 1
    assert len(moves) == 3

def test_execute_room_mining_multi_ores():
    routine = RoomMinerRoutine()
    nodes = [
        {"x": 100, "y": 100, "ore_type": "fer"},
        {"x": 200, "y": 200, "ore_type": "bronze"}
    ]
    
    clicks = []
    result = routine.execute_room_mining(
        detected_nodes=nodes,
        selected_ores=["fer", "bronze"],
        move_cursor_fn=lambda x, y: None,
        read_tooltip_fn=lambda: {"resource_name": "Bronze", "status": "available"},
        click_fn=lambda: clicks.append(1),
        sleep_fn=lambda t: None
    )
    
    assert result["mined_count"] == 2
    assert len(clicks) == 2
