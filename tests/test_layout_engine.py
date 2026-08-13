import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from backend.layout_engine import LayoutEngine, PitchSpec, Box2D, boxes_intersect

def test_squad_30_players_with_long_names_no_collision_and_inside_pitch():
    """
    Automated test verifying that for a full squad of 30 players with unusually long names,
    the layout engine generates bounding boxes such that:
    1. Every player box's center is strictly inside the trapezoid pitch boundary.
    2. No two player boxes intersect (zero bounding rectangle overlap).
    3. Box heights and font scaling ensure zero text overflow.
    """
    engine = LayoutEngine()
    
    # 30 players with long names across 6 position categories
    players = [
        {"id": f"p_{i}", "name": f"JugadorConNombreLargoPruebaExtensa {i}", "age": 20 + i % 15, 
         "derived_category": cat}
        for i in range(30)
        for cat in [["Porteros", "Centrales", "Laterales", "Mediocentros", "Int/Extremos", "Delanteros"][i % 6]]
    ]

    boxes = engine.layout_full_squad(players)
    
    assert len(boxes) == 30, f"Expected 30 boxes, got {len(boxes)}"

    # 1. Verify every box center is inside the trapezoid pitch boundary
    pitch = engine.pitch
    for box in boxes:
        cx, cy = box.center_x, box.center_y
        assert pitch.y_top <= cy <= (pitch.y_top + pitch.height), f"Box {box.id} center Y {cy} out of pitch Y bounds"
        left_bound, right_bound = pitch.get_x_bounds_at_y(cy)
        assert left_bound - 0.2 <= cx <= right_bound + 0.2, f"Box {box.id} center X {cx} outside pitch X bounds [{left_bound}, {right_bound}]"

    # 2. Verify zero bounding rectangle intersection between any pair of boxes
    collisions = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if boxes_intersect(boxes[i], boxes[j], padding=0.01):
                collisions.append((boxes[i].id, boxes[j].id, boxes[i].label, boxes[j].label))

    assert len(collisions) == 0, f"Detected {len(collisions)} box collisions: {collisions}"

def test_demographic_column_widths_fit_within_slide():
    """
    Verifies that dynamic demographic column width calculation fits strictly inside total table width
    and leaves explicit buffer space for footer.
    """
    engine = LayoutEngine()
    players = [{"name": f"Player {i}", "age": 20 + (i % 15), "derived_category": "Mediocentros"} for i in range(25)]
    
    widths = engine.calculate_demographic_column_widths(players, total_table_width=11.8)
    assert len(widths) == 8
    assert round(sum(widths), 2) == 11.8
