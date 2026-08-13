import sqlite3

valid_player_ids = {
    # Depor (30)
    "p_depor_leoroman", "p_depor_ferllo", "p_depor_german", "p_depor_puerto",
    "p_depor_noubi", "p_depor_barcia", "p_depor_ede", "p_depor_comas",
    "p_depor_quagliata", "p_depor_angelino", "p_depor_altimira", "p_depor_loureiro",
    "p_depor_ximo", "p_depor_amatucci", "p_depor_riki", "p_depor_villares",
    "p_depor_carrillo", "p_depor_gijselhart", "p_depor_patino", "p_depor_joseangel",
    "p_depor_soriano", "p_depor_aspjensen", "p_depor_jairo", "p_depor_yeremay",
    "p_depor_mella", "p_depor_luismicruz", "p_depor_bilnsongo", "p_depor_auba",
    "p_depor_eddahchouri", "p_depor_kevinsanchez",

    # Penafiel (28)
    "p_pena_femenias", "p_pena_alexei", "p_pena_migueloliveira", "p_pena_pica",
    "p_pena_claudiosilva", "p_pena_jaimesanchez", "p_pena_joaomiguel", "p_pena_injai",
    "p_pena_simao", "p_pena_alloh", "p_pena_martim", "p_pena_negrao",
    "p_extra_douglasborel", "p_pena_pedrosa", "p_pena_neto", "p_pena_carbonell",
    "p_pena_carlinhos", "p_pena_joaopinto", "p_pena_juanda", "p_pena_davo",
    "p_pena_jota", "p_pena_maddi", "p_pena_nunomartins", "p_pena_joaoleal",
    "p_pena_alcaina", "p_pena_sery", "p_pena_svensson", "p_extra_andreschutte",

    # Fabril (24)
    "p_fabril_hugorios", "p_fabril_alexmarques", "p_fabril_samu", "p_fabril_canedo",
    "p_fabril_malick", "p_fabril_vergara", "p_fabril_ikervidal", "p_fabril_pablogarcia",
    "p_fabril_teijo", "p_fabril_mardones", "p_fabril_carrillo", "p_fabril_estevez",
    "p_fabril_sanjose", "p_fabril_niang", "p_fabril_ferreiro", "p_fabril_luisao",
    "p_fabril_rubenlopez", "p_fabril_justino", "p_fabril_guerrero", "p_fabril_cortes",
    "p_fabril_areosa", "p_fabril_ochoa", "p_fabril_dipanda", "p_fabril_dominguez"
}

def purge():
    conn = sqlite3.connect("depor_demographic.db")
    c = conn.cursor()

    c.execute("SELECT id, name, team_id FROM players")
    all_rows = c.fetchall()

    deleted_count = 0
    for r in all_rows:
        if r[0] not in valid_player_ids:
            c.execute("DELETE FROM players WHERE id = ?", (r[0],))
            deleted_count += 1
            print(f"Purged extra player: {r[1]} ({r[0]}, team: {r[2]})")

    conn.commit()

    print("\n--- SQUAD TOTALS AFTER PURGE ---")
    for t_id in ['depor', 'penafiel', 'fabril']:
        c.execute("SELECT COUNT(*) FROM players WHERE team_id = ?", (t_id,))
        count = c.fetchone()[0]
        print(f"  {t_id.upper()}: {count} players")

    conn.close()

if __name__ == "__main__":
    purge()
