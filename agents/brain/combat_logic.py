from typing import Dict, List, Any

class CombatLogic:
    """
    Agent Tactique et Décisionnel (Le Cerveau) - Module de Combat et Grimoire.
    Évalue les lignes de vue (LoS), les PA/PM et sélectionne les séquences de sorts optimales.
    """
    def __init__(self, spell_database: Dict[str, Any] = None):
        self.spell_db = spell_database or {
            "Attaque Directe": {"pa": 3, "range_min": 1, "range_max": 4, "los_required": True},
            "Buff Puissance": {"pa": 2, "range_min": 0, "range_max": 0, "los_required": False}
        }

    def evaluate_threat(self, monster_group: List[Dict[str, Any]], max_level_allowed: int = 150) -> bool:
        """
        Détermine si le groupe de monstres sur la tuile peut être engagé en sécurité.
        """
        total_level = sum(m.get("level", 1) for m in monster_group)
        return total_level <= max_level_allowed

    def plan_turn(self, player_ap: int, player_mp: int, enemies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Génère une séquence d'actions tactiques pour le tour de jeu courant.
        """
        actions = []
        current_ap = player_ap
        
        # Exemple simple d'enchaînement de sorts
        for spell_name, details in self.spell_db.items():
            if current_ap >= details["pa"]:
                actions.append({
                    "action": "cast_spell",
                    "spell_name": spell_name,
                    "target_id": enemies[0]["id"] if enemies else None,
                    "cost_ap": details["pa"]
                })
                current_ap -= details["pa"]

        return actions

if __name__ == "__main__":
    combat = CombatLogic()
    print("[Le Cerveau] Engine de combat et évaluation des menaces initialisé.")
