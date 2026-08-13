import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.brain.combat_logic import CombatLogic

def test_threat_evaluation_safe():
    logic = CombatLogic()
    monsters = [{"id": 1, "level": 30}, {"id": 2, "level": 40}]
    assert logic.evaluate_threat(monsters, max_level_allowed=150) is True

def test_threat_evaluation_dangerous():
    logic = CombatLogic()
    monsters = [{"id": 1, "level": 100}, {"id": 2, "level": 120}]
    assert logic.evaluate_threat(monsters, max_level_allowed=150) is False

def test_turn_planning_action_sequence():
    logic = CombatLogic()
    enemies = [{"id": 42}]
    actions = logic.plan_turn(player_ap=6, player_mp=3, enemies=enemies)
    assert len(actions) > 0
    assert actions[0]["action"] == "cast_spell"
