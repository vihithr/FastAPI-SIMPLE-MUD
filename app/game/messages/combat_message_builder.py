"""战斗消息构建器"""
from typing import Dict, Any
from .message_builder import MessageBuilder


class CombatMessageBuilder(MessageBuilder):
    """战斗消息构建器"""
    
    @staticmethod
    def build_attack_message(
        attacker_name: str,
        defender_name: str,
        combat_result: Dict[str, Any],
        exp_gained: int = 0,
        level_up: bool = False,
        is_training_dummy: bool = False
    ) -> str:
        """构建攻击消息"""
        if combat_result.get("miss"):
            return f"你攻击 {defender_name}，但未命中！(掷骰: {combat_result['roll_result']})"
        
        damage = combat_result["damage"]
        critical_text = " (暴击！)" if combat_result.get("critical") else ""
        
        if is_training_dummy:
            defender_hp = combat_result.get("defender_hp_after", 0)
            defender_max_hp = combat_result.get("defender_max_hp", 1000)
            message = f"你对测试靶子造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, 测试靶子剩余生命值: {defender_hp}/{defender_max_hp})"
        else:
            defender_hp = combat_result.get("defender_hp_after", 0)
            defender_max_hp = combat_result.get("defender_max_hp", 100)
            if defender_hp <= 0:
                message = f"你击败了 {defender_name}！造成 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']})"
                if exp_gained > 0:
                    message += f"\n获得 {exp_gained} 经验值。"
            else:
                message = f"你对 {defender_name} 造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, {defender_name} 剩余生命值: {defender_hp}/{defender_max_hp})"
        
        if level_up:
            message += f"\n恭喜！你升级了！当前等级: {combat_result.get('new_level', 1)}"
        
        if is_training_dummy and exp_gained > 0:
            message += f"\n获得 {exp_gained} 点训练经验。"
        
        return message
    
    @staticmethod
    def build_defend_message(
        attacker_name: str,
        combat_result: Dict[str, Any],
        defender_hp: int,
        defender_max_hp: int
    ) -> str:
        """构建防御消息"""
        if combat_result.get("miss"):
            return f"{attacker_name} 攻击你，但未命中！(掷骰: {combat_result['roll_result']})"
        
        damage = combat_result["damage"]
        critical_text = " (暴击！)" if combat_result.get("critical") else ""
        
        if defender_hp <= 0:
            return f"{attacker_name} 击败了你！你失去了 {damage} 生命值{critical_text}。\n你被击败了！"
        else:
            return f"{attacker_name} 对你造成了 {damage} 点伤害{critical_text}！(掷骰: {combat_result['roll_result']}, 剩余生命值: {defender_hp}/{defender_max_hp})"
    
    def build(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """构建战斗消息"""
        attacker_name = data.get("attacker", "未知")
        defender_name = data.get("defender", "未知")
        combat_result = data.get("combat_result", {})
        exp_gained = data.get("exp_gained", 0)
        level_up = data.get("level_up", False)
        is_training_dummy = data.get("is_training_dummy", False)
        
        message = self.build_attack_message(
            attacker_name,
            defender_name,
            combat_result,
            exp_gained,
            level_up,
            is_training_dummy
        )
        
        return self.create_message("combat", message, {
            "attacker": attacker_name,
            "defender": defender_name,
            "damage": combat_result.get("damage", 0),
            "defender_hp": combat_result.get("defender_hp_after", 0),
            "exp_gained": exp_gained,
            "level_up": level_up,
            "hit": combat_result.get("hit", False),
            "critical": combat_result.get("critical", False),
            "roll_result": combat_result.get("roll_result", 0),
            "miss": combat_result.get("miss", False)
        })
