from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

POSITION_CATEGORY_MAP = {
    # Porteros
    "portero": "Porteros",
    "guardameta": "Porteros",
    "gk": "Porteros",
    
    # Centrales
    "defensa central": "Centrales",
    "central": "Centrales",
    "cb": "Centrales",
    
    # Laterales
    "lateral izquierdo": "Laterales",
    "lateral derecho": "Laterales",
    "lateral izq": "Laterales",
    "lateral dcho": "Laterales",
    "lateral": "Laterales",
    "carrilero": "Laterales",
    "lb": "Laterales",
    "rb": "Laterales",
    "lwb": "Laterales",
    "rwb": "Laterales",
    
    # Mediocentros
    "pivote": "Mediocentros",
    "mediocentro": "Mediocentros",
    "mediocentro defensivo": "Mediocentros",
    "mediocentro ofensivo": "Mediocentros",
    "medular": "Mediocentros",
    "dm": "Mediocentros",
    "cm": "Mediocentros",
    "cam": "Mediocentros",
    
    # Int/Extremos
    "extremo izquierdo": "Int/Extremos",
    "extremo derecho": "Int/Extremos",
    "extremo izq": "Int/Extremos",
    "extremo dcho": "Int/Extremos",
    "extremo": "Int/Extremos",
    "interior": "Int/Extremos",
    "interior izquierdo": "Int/Extremos",
    "interior derecho": "Int/Extremos",
    "lw": "Int/Extremos",
    "rw": "Int/Extremos",
    "lm": "Int/Extremos",
    "rm": "Int/Extremos",
    
    # Delanteros
    "delantero centro": "Delanteros",
    "delantero": "Delanteros",
    "punta": "Delanteros",
    "segundo delantero": "Delanteros",
    "st": "Delanteros",
    "cf": "Delanteros",
    "ss": "Delanteros",
}

def derive_position_category(detailed_position: str) -> str:
    pos_lower = detailed_position.strip().lower()
    for key, cat in POSITION_CATEGORY_MAP.items():
        if key in pos_lower:
            return cat
    return "Mediocentros"

def calculate_age(birthdate_str: str, ref_date: Optional[str] = None) -> int:
    bdate = None
    if birthdate_str:
        s = birthdate_str.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                bdate = datetime.strptime(s, fmt).date()
                break
            except Exception:
                pass
    if not bdate:
        return 22  # Fallback age if date format is invalid
    
    if ref_date:
        try:
            rdate = datetime.strptime(ref_date, "%Y-%m-%d").date()
        except Exception:
            rdate = date.today()
    else:
        rdate = date.today()
    
    age = rdate.year - bdate.year - ((rdate.month, rdate.day) < (bdate.month, bdate.day))
    return age

class PlayerBase(BaseModel):
    name: str
    birthdate: str
    detailed_position: str
    team_id: str
    photo_url: Optional[str] = None
    minutes_played: Optional[int] = 0
    starts: Optional[int] = 0
    subs_in: Optional[int] = 0
    yellow_cards: Optional[int] = 0
    red_cards: Optional[int] = 0
    goals: Optional[int] = 0
    seasons_data: Optional[str] = None
    is_injured: Optional[bool] = False
    injury_description: Optional[str] = ""
    injury_return_time: Optional[str] = ""
    injury_phase: Optional[str] = ""
    extra_pitch_team_id: Optional[str] = None

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: str
    derived_category: str
    age: int
    pitch_x: Optional[float] = None
    pitch_y: Optional[float] = None

class PlayerInjuryUpdate(BaseModel):
    is_injured: bool = True
    injury_description: Optional[str] = ""
    injury_return_time: Optional[str] = ""
    injury_phase: Optional[str] = ""

class PlayerStatsUpdate(BaseModel):
    minutes_played: int = 0
    starts: int = 0
    subs_in: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    goals: int = 0
    seasons_data: Optional[str] = None

class PitchPositionUpdate(BaseModel):
    pitch_x: float
    pitch_y: float

class Team(BaseModel):
    id: str
    name: str
    season: str = "2026/27 SEASON"
    club_name: str = "DEPORTIVO DE A CORUÑA FC"

class SubstitutionEvent(BaseModel):
    id: str
    match_id: str
    player_out_id: str
    player_in_id: str
    minute: int

class LineupEntry(BaseModel):
    id: str
    match_id: str
    player_id: str
    field_position: str
    is_starter: bool = True
    grid_x: float = 0.5  # Relative position 0.0 - 1.0 (left to right)
    grid_y: float = 0.5  # Relative position 0.0 - 1.0 (top/attack to bottom/defense)
    sub_in_minute: Optional[int] = None
    sub_out_minute: Optional[int] = None
    has_yellow_card: bool = False
    has_red_card: bool = False
    card_minute: Optional[int] = None
    card_type: Optional[str] = None  # "YELLOW", "RED", "DOUBLE_YELLOW"
    goals: int = 0


class MatchCreate(BaseModel):
    team_id: str
    opponent: str
    date: str
    result_type: str = "WIN"  # WIN, DRAW, LOSE
    home_goals: int = 0
    away_goals: int = 0
    is_home: bool = True
    competition: str = "LALIGA HYPERMOTION"
    match_type: Optional[str] = "LIGA"  # LIGA, AMISTOSO, COPA, OTRO
    matchday: Optional[str] = ""  # ej. "Jornada 1", "J01", "1"
    custom_title: Optional[str] = None
    playing_time: str = "90 Minutes"
    substitute_cadence: str = ""
    substitution_times: List[str] = Field(default_factory=list)
    notes: Optional[str] = None

class Match(MatchCreate):
    id: str
    
    @property
    def match_time(self) -> str:
        return self.playing_time
        
    @property
    def substitution_cadence(self) -> str:
        return self.substitute_cadence

    @property
    def title_display(self) -> str:
        if self.custom_title:
            return self.custom_title
        score = f"{self.home_goals}-{self.away_goals}"
        if self.is_home:
            return f"DEPORTIVO v {self.opponent} ({self.result_type} {score})"
        else:
            return f"{self.opponent} v DEPORTIVO ({self.result_type} {score})"

class FullMatchData(BaseModel):
    match: Match
    team: Team
    starters: List[LineupEntry]
    substitutes: List[LineupEntry]
    substitutions: List[SubstitutionEvent]
    players_map: dict  # player_id -> Player object

