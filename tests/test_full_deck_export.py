import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import database as db
from backend.models import Player, Team
from backend.pdf_generator import PDFReportGenerator
from backend.pptx_generator import PPTXGenerator

def test_full_18_slide_pdf_generation():
    db.init_db()
    teams = db.get_teams()
    assert len(teams) >= 3, f"Expected at least 3 teams, found {len(teams)}"

    out_pdf = os.path.join(os.path.dirname(__file__), "test_output_full_deck.pdf")
    generator = PDFReportGenerator(out_pdf)

    # Generate complete PDF deck: Cover, Slide A, Slide B for each team, plus all 11 matches
    for team in teams:
        players = db.get_players_by_team(team.id)
        generator.generate_cover_slide(team)
        generator.generate_demographic_slide(team, players)
        generator.generate_squad_pitch_slide(team, players)

        matches = db.get_matches_by_team(team.id)
        for match in matches:
            m_data = db.get_match_full_data(match.id)
            if m_data:
                generator.generate_match_report_slide(m_data)

    generator.save()
    assert os.path.exists(out_pdf), "PDF file was not created"
    assert os.path.getsize(out_pdf) > 20000, f"PDF file size {os.path.getsize(out_pdf)} too small"
    print(f"Generated full PDF successfully: {out_pdf} ({os.path.getsize(out_pdf)} bytes)")

def test_full_pptx_generation():
    db.init_db()
    teams = db.get_teams()
    depor = next((t for t in teams if "deportivo" in t.name.lower() and "fabril" not in t.name.lower()), teams[0])
    players = db.get_players_by_team(depor.id)
    matches = db.get_matches_by_team(depor.id)

    out_pptx = os.path.join(os.path.dirname(__file__), "test_output_depor.pptx")
    pptx_gen = PPTXGenerator()
    pptx_gen.generate_demographic_slide(depor, players)
    pptx_gen.generate_squad_pitch_slide(depor, players)
    for m in matches:
        m_data = db.get_match_full_data(m.id)
        if m_data:
            pptx_gen.generate_match_report_slide(m_data)

    pptx_gen.save(out_pptx)
    assert os.path.exists(out_pptx), "PPTX file was not created"
    assert os.path.getsize(out_pptx) > 20000, f"PPTX file size {os.path.getsize(out_pptx)} too small"
    print(f"Generated full PPTX successfully: {out_pptx} ({os.path.getsize(out_pptx)} bytes)")

if __name__ == "__main__":
    test_full_18_slide_pdf_generation()
    test_full_pptx_generation()
