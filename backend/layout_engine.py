import math
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel

class Box2D(BaseModel):
    id: str
    label: str
    x: float      # Left (inches)
    y: float      # Top (inches)
    width: float  # Width (inches)
    height: float # Height (inches)
    font_size: float = 10.0 # Font size (pt)
    u: float = 0.5 # Relative pitch X (0-1)
    v: float = 0.5 # Relative pitch Y (0-1)
    
    @property
    def x_min(self) -> float:
        return self.x
    @property
    def x_max(self) -> float:
        return self.x + self.width
    @property
    def y_min(self) -> float:
        return self.y
    @property
    def y_max(self) -> float:
        return self.y + self.height
    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0
    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0

class PitchSpec(BaseModel):
    x_center: float = 6.666    # Inches from left (slide is 13.33 x 7.5 widescreen)
    y_top: float = 1.35       # Inches from top
    height: float = 5.25      # Inches total height
    w_top: float = 7.5        # Pitch width at top (inches) - RECTANGULAR
    w_bottom: float = 7.5     # Pitch width at bottom (inches) - RECTANGULAR
    margin: float = 0.15      # Internal margin from pitch border

    def get_pitch_width_at_y(self, y: float) -> float:
        v = (y - self.y_top) / self.height
        v = max(0.0, min(1.0, v))
        return self.w_top + v * (self.w_bottom - self.w_top)

    def get_x_bounds_at_y(self, y: float) -> Tuple[float, float]:
        w = self.get_pitch_width_at_y(y)
        left = self.x_center - (w / 2.0)
        right = self.x_center + (w / 2.0)
        return (left, right)

    def is_box_inside(self, box: Box2D) -> bool:
        # Check top edge and bottom edge horizontal bounds
        left_top, right_top = self.get_x_bounds_at_y(box.y_min)
        left_bot, right_bot = self.get_x_bounds_at_y(box.y_max)
        
        if box.y_min < self.y_top - 0.05 or box.y_max > (self.y_top + self.height + 0.05):
            return False
            
        if box.x_min < (left_top - self.margin) or box.x_min < (left_bot - self.margin):
            return False
            
        if box.x_max > (right_top + self.margin) or box.x_max > (right_bot + self.margin):
            return False
            
        return True

def boxes_intersect(b1: Box2D, b2: Box2D, padding: float = 0.02) -> bool:
    if b1.x_max + padding <= b2.x_min or b1.x_min >= b2.x_max + padding:
        return False
    if b1.y_max + padding <= b2.y_min or b1.y_min >= b2.y_max + padding:
        return False
    return True

def calculate_box_width_and_font(text: str, base_font_size: float = 10.0, min_width: float = 1.15, max_width: float = 2.2) -> Tuple[float, float]:
    # Estimate width: padding ~ 0.25 in + len(text) * font_size * 0.05 / 12
    char_len = len(text)
    est_width = 0.25 + (char_len * base_font_size * 0.045 / 10.0)
    
    font_size = base_font_size
    if est_width > max_width:
        # Reduce font size to scale text down
        scale = max_width / est_width
        font_size = max(7.5, round(base_font_size * scale, 1))
        est_width = max_width
    elif est_width < min_width:
        est_width = min_width
        
    return round(est_width, 2), font_size

class LayoutEngine:
    def __init__(self, pitch_spec: Optional[PitchSpec] = None):
        self.pitch = pitch_spec or PitchSpec()

    def relative_to_absolute(self, u: float, v: float) -> Tuple[float, float]:
        """
        Converts (u, v) in [0, 1]^2 to (x, y) in inches on trapezoidal pitch.
        u: 0.0 (left) to 1.0 (right)
        v: 0.0 (top/attack) to 1.0 (bottom/defense)
        """
        y = self.pitch.y_top + v * self.pitch.height
        left, right = self.pitch.get_x_bounds_at_y(y)
        x = left + u * (right - left)
        return round(x, 3), round(y, 3)

    def absolute_to_relative(self, x: float, y: float) -> Tuple[float, float]:
        v = (y - self.pitch.y_top) / self.pitch.height
        left, right = self.pitch.get_x_bounds_at_y(y)
        u = (x - left) / (right - left) if right != left else 0.5
        return round(u, 3), round(v, 3)

    def get_tactical_role(self, detailed_position: str) -> str:
        pos = detailed_position.strip().lower()
        if any(k in pos for k in ["portero", "guardameta", "gk"]):
            return "GK"
        if any(k in pos for k in ["izquierdo", "izq", "lb", "lwb"]) and any(k in pos for k in ["lateral", "carrilero", "defensa"]):
            return "LB"
        if any(k in pos for k in ["derecho", "dcho", "rb", "rwb"]) and any(k in pos for k in ["lateral", "carrilero", "defensa"]):
            return "RB"
        if any(k in pos for k in ["central", "cb", "defensa central"]):
            return "CB"
        if any(k in pos for k in ["pivote", "defensivo", "dm"]):
            return "DM"
        if any(k in pos for k in ["ofensivo", "mediapunta", "cam"]):
            return "CAM"
        if any(k in pos for k in ["izquierdo", "izq", "lw", "lm"]) and any(k in pos for k in ["extremo", "interior", "banda"]):
            return "LW"
        if any(k in pos for k in ["derecho", "dcho", "rw", "rm"]) and any(k in pos for k in ["extremo", "interior", "banda"]):
            return "RW"
        if any(k in pos for k in ["extremo", "interior"]):
            return "LW"
        if any(k in pos for k in ["delantero", "punta", "st", "cf", "segundo delantero"]):
            return "ST"
        return "CM"

    def compute_default_tactical_coordinates(self, players: List[Dict]) -> Dict[str, Tuple[float, float]]:
        """
        Computes default (u, v) on-pitch coordinates for every player based on authentic soccer formations:
        - GK: bottom goal line (v ~ 0.88)
        - LB / RB: wide defensive flanks (u ~ 0.18, 0.82; v ~ 0.72)
        - CB: central defense line (u ~ 0.38 - 0.62; v ~ 0.77)
        - DM / Pivote: just ahead of CBs (u ~ 0.50; v ~ 0.62)
        - CM / Interiores: central & interior midfield (u ~ 0.34 - 0.66; v ~ 0.48 - 0.54)
        - CAM / Mediapunta: attacking midfield (u ~ 0.50; v ~ 0.38)
        - LW / RW: attacking wings (u ~ 0.18, 0.82; v ~ 0.28)
        - ST: central forwards (u ~ 0.42 - 0.58; v ~ 0.16)
        """
        role_groups: Dict[str, List[Dict]] = {
            "GK": [], "LB": [], "CB": [], "RB": [],
            "DM": [], "CM": [], "CAM": [],
            "LW": [], "RW": [], "ST": []
        }
        
        for p in players:
            pos = p.get('detailed_position', '')
            role = self.get_tactical_role(pos)
            role_groups[role].append(p)
            
        coords: Dict[str, Tuple[float, float]] = {}
        
        # 1. Porteros (GK)
        gks = role_groups["GK"]
        if gks:
            n = len(gks)
            u_slots = [0.50] if n == 1 else [0.35 + (0.30 / (n - 1)) * i for i in range(n)] if n <= 3 else [0.24 + (0.52 / (n - 1)) * i for i in range(n)]
            for i, p in enumerate(gks):
                coords[p['id']] = (round(u_slots[i], 3), 0.88)
                
        # 2. Laterales Izquierdos (LB)
        lbs = role_groups["LB"]
        if lbs:
            n = len(lbs)
            v_slots = [0.72] if n == 1 else [0.66 + (0.12 / (n - 1)) * i for i in range(n)]
            u_slots = [0.18] if n == 1 else [0.15 + (0.07 / (n - 1)) * i for i in range(n)]
            for i, p in enumerate(lbs):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        # 3. Defensas Centrales (CB)
        cbs = role_groups["CB"]
        if cbs:
            n = len(cbs)
            u_slots = [0.50] if n == 1 else [0.42, 0.58] if n == 2 else [0.36 + (0.28 / (n - 1)) * i for i in range(n)]
            v_slots = [0.77] * n
            if n > 2:
                # Slight vertical stagger for odd/even
                v_slots = [0.75 if i % 2 == 0 else 0.79 for i in range(n)]
            for i, p in enumerate(cbs):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        # 4. Laterales Derechos (RB)
        rbs = role_groups["RB"]
        if rbs:
            n = len(rbs)
            v_slots = [0.72] if n == 1 else [0.66 + (0.12 / (n - 1)) * i for i in range(n)]
            u_slots = [0.82] if n == 1 else [0.78 + (0.07 / (n - 1)) * i for i in range(n)]
            for i, p in enumerate(rbs):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        # 5. Pivotes (DM)
        dms = role_groups["DM"]
        if dms:
            n = len(dms)
            u_slots = [0.50] if n == 1 else [0.42 + (0.16 / (n - 1)) * i for i in range(n)]
            for i, p in enumerate(dms):
                coords[p['id']] = (round(u_slots[i], 3), 0.62)

        # 6. Mediocentros (CM)
        cms = role_groups["CM"]
        if cms:
            n = len(cms)
            if n <= 3:
                u_slots = [0.50] if n == 1 else [0.38 + (0.24 / (n - 1)) * i for i in range(n)]
                v_slots = [0.50] * n
            else:
                # 2 tiers of midfielders (e.g. interior line & center)
                u_slots = []
                v_slots = []
                for i in range(n):
                    tier = i % 2
                    col = i // 2
                    total_in_tier = (n + 1) // 2 if tier == 0 else n // 2
                    u_val = 0.35 + (0.30 / max(1, total_in_tier - 1)) * col if total_in_tier > 1 else 0.50
                    v_val = 0.53 if tier == 0 else 0.46
                    u_slots.append(u_val)
                    v_slots.append(v_val)
            for i, p in enumerate(cms):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        # 7. Mediocentros Ofensivos (CAM)
        cams = role_groups["CAM"]
        if cams:
            n = len(cams)
            u_slots = [0.50] if n == 1 else [0.42 + (0.16 / (n - 1)) * i for i in range(n)]
            v_slots = [0.38] * n
            for i, p in enumerate(cams):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        # 8. Extremos Izquierdos (LW)
        lws = role_groups["LW"]
        if lws:
            n = len(lws)
            v_slots = [0.28] if n == 1 else [0.22 + (0.12 / (n - 1)) * i for i in range(n)]
            u_slots = [0.20] if n == 1 else [0.16 + (0.08 / (n - 1)) * i for i in range(n)]
            for i, p in enumerate(lws):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        # 9. Extremos Derechos (RW)
        rws = role_groups["RW"]
        if rws:
            n = len(rws)
            v_slots = [0.28] if n == 1 else [0.22 + (0.12 / (n - 1)) * i for i in range(n)]
            u_slots = [0.80] if n == 1 else [0.76 + (0.08 / (n - 1)) * i for i in range(n)]
            for i, p in enumerate(rws):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        # 10. Delanteros (ST)
        sts = role_groups["ST"]
        if sts:
            n = len(sts)
            if n == 1:
                u_slots = [0.50]
                v_slots = [0.16]
            elif n == 2:
                u_slots = [0.42, 0.58]
                v_slots = [0.16, 0.16]
            else:
                u_slots = [0.36 + (0.28 / (n - 1)) * i for i in range(n)]
                v_slots = [0.15 if i % 2 == 0 else 0.19 for i in range(n)]
            for i, p in enumerate(sts):
                coords[p['id']] = (round(u_slots[i], 3), round(v_slots[i], 3))

        return coords

    def layout_full_squad(self, players: List[Dict]) -> List[Box2D]:
        """
        Layouts 20-30 full squad players onto the tactical pitch:
        - If player has custom saved `pitch_x` and `pitch_y`, use them.
        - Otherwise, calculates authentic tactical formation positions (GK at bottom, Defense in line, Midfield, Attack).
        """
        default_coords = self.compute_default_tactical_coordinates(players)
        boxes: List[Box2D] = []
        box_h = 0.29
        
        for player in players:
            p_id = player.get('id', '')
            text = f"{player['name']} - {player['age']}"
            
            # Check if custom coordinates exist
            u = player.get('pitch_x')
            v = player.get('pitch_y')
            
            if u is None or v is None:
                u, v = default_coords.get(p_id, (0.50, 0.50))
            else:
                u = float(u)
                v = float(v)
                
            bw, font_sz = calculate_box_width_and_font(text, base_font_size=8.5, min_width=1.05, max_width=1.75)
            cx, cy = self.relative_to_absolute(u, v)
            box = Box2D(id=p_id, label=text, x=cx - bw/2.0, y=cy - box_h/2.0, width=bw, height=box_h, font_size=font_sz, u=u, v=v)
            boxes.append(box)
            
        boxes = self.resolve_collisions(boxes)
        for b in boxes:
            b.u, b.v = self.absolute_to_relative(b.center_x, b.center_y)
        return boxes

    def layout_match_starters(self, starters: List[Dict], players_map: Dict[str, Dict]) -> List[Box2D]:
        """
        Layouts 11 starters on Slide C pitch based on assigned field grid coordinates.
        """
        boxes: List[Box2D] = []
        box_h = 0.32
        
        for entry in starters:
            p_id = entry.get('player_id')
            p_info = players_map.get(p_id, {'name': 'Jugador', 'age': 22}) if isinstance(players_map.get(p_id), dict) else getattr(players_map.get(p_id), '__dict__', {'name': 'Jugador', 'age': 22})
            sub_out = entry.get('sub_out_minute')
            has_yellow = entry.get('has_yellow_card')
            has_red = entry.get('has_red_card')
            card_min = entry.get('card_minute')
            
            p_name = p_info.get('name', 'Jugador')
            card_str = ""
            if has_red:
                card_str = f" ({card_min}’ 🟥)" if card_min else " 🟥"
            elif has_yellow:
                card_str = f" ({card_min}’ 🟨)" if card_min else " 🟨"

            if sub_out:
                text = f"{p_name} ({sub_out}’){card_str}"
            else:
                text = f"{p_name}{card_str}"
                
            u = float(entry.get('grid_x', 0.5))
            v = float(entry.get('grid_y', 0.5))
            
            bw, font_sz = calculate_box_width_and_font(text, base_font_size=8.5, min_width=1.0, max_width=1.65)
            cx, cy = self.relative_to_absolute(u, v)
            box = Box2D(id=p_id, label=text, x=cx - bw/2.0, y=cy - box_h/2.0, width=bw, height=box_h, font_size=font_sz, u=u, v=v)
            boxes.append(box)
            
        boxes = self.resolve_collisions(boxes)
        for b in boxes:
            b.u, b.v = self.absolute_to_relative(b.center_x, b.center_y)
        return boxes

    def resolve_collisions(self, boxes: List[Box2D], max_iterations: int = 50) -> List[Box2D]:
        """
        Iteratively pushes overlapping boxes apart slightly vertically or horizontally,
        while maintaining pitch bounds.
        """
        for _ in range(max_iterations):
            collision_found = False
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    if boxes_intersect(boxes[i], boxes[j], padding=0.015):
                        collision_found = True
                        b1 = boxes[i]
                        b2 = boxes[j]
                        
                        overlap_x = min(b1.x_max - b2.x_min, b2.x_max - b1.x_min)
                        overlap_y = min(b1.y_max - b2.y_min, b2.y_max - b1.y_min)
                        
                        if overlap_y < overlap_x:
                            shift = (overlap_y + 0.02) / 2.0
                            if b1.center_y <= b2.center_y:
                                b1.y -= shift
                                b2.y += shift
                            else:
                                b1.y += shift
                                b2.y -= shift
                        else:
                            shift = (overlap_x + 0.02) / 2.0
                            if b1.center_x <= b2.center_x:
                                b1.x -= shift
                                b2.x += shift
                            else:
                                b1.x += shift
                                b2.x -= shift
                                
                        b1.y = max(self.pitch.y_top, min(self.pitch.y_top + self.pitch.height - b1.height, b1.y))
                        b2.y = max(self.pitch.y_top, min(self.pitch.y_top + self.pitch.height - b2.height, b2.y))
                        
            if not collision_found:
                break
                
        return boxes

    def calculate_demographic_column_widths(self, players: List[Dict], total_table_width: float = 11.8) -> List[float]:
        """
        Calculates dynamic column widths for Slide A 8-column table.
        Cols: [Age Band, Porteros, Centrales, Laterales, Mediocentros, Int/Extremos, Delanteros, TOTAL]
        """
        fixed_age_width = 1.2
        fixed_total_width = 0.9
        rem_width = total_table_width - fixed_age_width - fixed_total_width # 9.7 inches
        
        category_counts = {
            "Porteros": 0,
            "Centrales": 0,
            "Laterales": 0,
            "Mediocentros": 0,
            "Int/Extremos": 0,
            "Delanteros": 0
        }
        for p in players:
            cat = p.get('derived_category', 'Mediocentros')
            if cat in category_counts:
                category_counts[cat] += 1
                
        total_p = sum(category_counts.values()) or 1
        
        widths = [fixed_age_width]
        min_pos_width = 1.25
        
        # Calculate raw weights
        raw_weights = [max(1, category_counts[cat]) for cat in category_counts]
        sum_weights = sum(raw_weights)
        
        pos_widths = [(w / sum_weights) * rem_width for w in raw_weights]
        
        # Enforce min_pos_width
        for i in range(len(pos_widths)):
            if pos_widths[i] < min_pos_width:
                pos_widths[i] = min_pos_width
                
        # Re-normalize position widths to fit exactly rem_width
        norm_sum = sum(pos_widths)
        pos_widths = [round((pw / norm_sum) * rem_width, 2) for pw in pos_widths]
        
        # Adjust last position width for float rounding precision
        diff = round(rem_width - sum(pos_widths), 2)
        pos_widths[-1] = round(pos_widths[-1] + diff, 2)
        
        widths.extend(pos_widths)
        widths.append(fixed_total_width)
        return widths
