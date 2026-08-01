import streamlit as st
import json
import os
import requests
import base64
from datetime import datetime
from zoneinfo import ZoneInfo

# ------------------------------------------------------------------------------
# 1. KONFIGURATION & STYLES (MARTIAL BLACK METAL & BLOOD THEME)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="COMPETUS MAXIMUS",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Martial / Black Metal / Blood Design
st.markdown("""
<style>
    /* Raw Metal & Blood Base Background */
    .stApp {
        background-color: #050505;
        color: #d1d5db;
        font-family: 'Cinzel', 'Courier New', monospace, serif;
    }
    
    /* Blood Red Headers */
    h1, h2, h3 {
        color: #ff003c !important;
        text-shadow: 2px 2px 10px rgba(255, 0, 60, 0.7), 0 0 20px #8b0000;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 900 !important;
    }
    
    /* Grim Metal Containers */
    div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stContainer"] {
        border: 2px solid #3a0007 !important;
        background: linear-gradient(180deg, #110305 0%, #080808 100%) !important;
        border-radius: 4px !important;
        box-shadow: inset 0 0 15px rgba(139, 0, 0, 0.4), 0 4px 15px rgba(0, 0, 0, 0.9);
        margin-bottom: 15px;
    }
    
    /* Martial Status Badges */
    .status-open {
        background-color: rgba(185, 28, 28, 0.3);
        border: 2px solid #ef4444;
        color: #fca5a5;
        padding: 8px 12px;
        border-radius: 2px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
    }
    .status-closed {
        background-color: rgba(30, 41, 59, 0.5);
        border: 2px solid #475569;
        color: #94a3b8;
        padding: 8px 12px;
        border-radius: 2px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
    }

    /* Blood Buttons */
    .stButton>button {
        background: linear-gradient(180deg, #8b0000 0%, #3a0007 100%) !important;
        color: #ffffff !important;
        border: 1px solid #ff003c !important;
        border-radius: 2px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background: linear-gradient(180deg, #ff003c 0%, #8b0000 100%) !important;
        box-shadow: 0 0 15px rgba(255, 0, 60, 0.8) !important;
        color: #ffffff !important;
    }
    
    /* Blood Cards */
    .blood-card {
        border-left: 4px solid #ff003c;
        background: rgba(20, 5, 8, 0.8);
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 2px;
    }
    
    .king-card {
        border: 2px solid #ff003c;
        background: radial-gradient(circle, rgba(60, 0, 15, 0.6) 0%, rgba(10, 2, 4, 0.9) 100%);
        padding: 15px;
        text-align: center;
        box-shadow: 0 0 20px rgba(255, 0, 60, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. DATA ARCHITECTURE & PERSISTENCE
# ------------------------------------------------------------------------------
DATA_FILE = "data.json"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_now_str():
    return datetime.now(BERLIN_TZ).strftime("%Y-%m-%d %H:%M:%S")

def get_default_data():
    return {
        "config": {
            "bracket_tournament_status": "OPEN", # "OPEN", "CLOSED"
            "current_season": 1
        },
        "players": {},
        "games": {
            "1": {
                "name": "Tekken 8",
                "steam_appid": "1778820",
                "custom_cover": ""
            },
            "2": {
                "name": "Street Fighter 6",
                "steam_appid": "1364780",
                "custom_cover": ""
            }
        },
        "koth": {
            # "game_id": {"king": "PlayerName", "streak": 5, "history": []}
            "1": {"king": None, "streak": 0, "history": []},
            "2": {"king": None, "streak": 0, "history": []}
        },
        "brackets_de": [], # Double elimination brackets
        "appeals": [],
        "audit_logs": []
    }

def sync_to_github(json_str):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    path = st.secrets.get("GITHUB_FILE_PATH", "data.json")
    
    if not token or not repo:
        return

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"Auto-Sync data.json [{get_now_str()}]",
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha
        
    requests.put(url, headers=headers, json=payload)

def load_data():
    if not os.path.exists(DATA_FILE):
        default = get_default_data()
        save_data(default, sync=False)
        return default
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return get_default_data()

def save_data(data, sync=True):
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(json_str)
    if sync:
        try:
            sync_to_github(json_str)
        except Exception as e:
            st.warning(f"GitHub Sync fehlgeschlagen: {e}")

def add_audit_log(data, action, user="System"):
    data["audit_logs"].append({
        "timestamp": get_now_str(),
        "user": user,
        "action": action
    })

def get_steam_cover(appid, custom_override=""):
    if custom_override:
        return custom_override
    if appid:
        return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg"
    return "https://via.placeholder.com/460x215/100000/ff003c?text=NO+GAME+COVER"

if "db" not in st.session_state:
    st.session_state.db = load_data()

def update_db():
    save_data(st.session_state.db)

db = st.session_state.db

# ------------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# ------------------------------------------------------------------------------
st.sidebar.title("🩸 COMPETE MAXIMUS")
st.sidebar.caption(f"DEUTSCHLAND (BERLIN)\n{get_now_str()}")

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "NAVIGATION",
    ["👑 King of the Hill", "🌿 Double Elimination Bracket", "📩 Einspruch & Anträge", "⚙️ Admin-Bereich"]
)

# ------------------------------------------------------------------------------
# 4. KING OF THE HILL SECTION
# ------------------------------------------------------------------------------
if page == "👑 King of the Hill":
    st.title("👑 KING OF THE HILL")
    st.caption("BEHAUPTE DICH AN DER SPITZE ODER GEHE IM BLUT UNTER.")
    
    games = db.get("games", {})
    if not games:
        st.info("Keine Spiele angelegt. Bitte erstelle Spiele im Admin-Bereich.")
    else:
        # Dashboard Overview of all Kings
        st.subheader("🔥 AKTUELLE KÖNIGE (ÜBERSICHT)")
        cols = st.columns(len(games))
        for idx, (g_id, g_info) in enumerate(games.items()):
            k_data = db["koth"].get(g_id, {"king": None, "streak": 0})
            cover = get_steam_cover(g_info.get("steam_appid"), g_info.get("custom_cover"))
            
            with cols[idx % len(cols)]:
                with st.container(border=True):
                    st.image(cover, use_container_width=True)
                    st.markdown(f"### {g_info['name']}")
                    st.markdown(f"👑 **König:** `{k_data['king'] or 'NIEMAND'}`")
                    st.markdown(f"🔥 **Win-Streak:** `{k_data['streak']}` Siege")
        
        st.markdown("---")
        
        # Interactive Challenge Area per Game
        selected_g_id = st.selectbox("WÄHLE EIN SPIEL ZUM HERAUSFORDERN / AUSWERTEN", list(games.keys()), format_func=lambda x: games[x]["name"])
        g_info = games[selected_g_id]
        k_data = db["koth"].setdefault(selected_g_id, {"king": None, "streak": 0, "history": []})
        
        col_img, col_detail = st.columns([1, 2])
        with col_img:
            st.image(get_steam_cover(g_info.get("steam_appid"), g_info.get("custom_cover")), use_container_width=True)
        
        with col_detail:
            st.markdown(f"## {g_info['name']} Arena")
            st.write(f"Aktueller Herrscher: **{k_data['king'] or 'Der Thron ist leer!'}**")
            st.write(f"Aktuelle Streak: **{k_data['streak']} Siege**")
        
        st.markdown("### ⚔️ KING HERAUSFORDERN")
        player_list = list(db["players"].keys())
        
        if len(player_list) < 2:
            st.warning("Es werden mindestens 2 registrierte Spieler benötigt.")
        else:
            with st.form(f"koth_challenge_form_{selected_g_id}", clear_on_submit=True):
                c1, c2 = st.columns(2)
                
                # If there's no king, anyone can challenge anyone for the throne
                current_king = k_data['king']
                if current_king:
                    defender = current_king
                    c1.text_input("König (Verteidiger)", value=defender, disabled=True)
                    challenger = c2.selectbox("Herausforderer", [p for p in player_list if p != defender])
                else:
                    defender = c1.selectbox("Spieler 1 (Thronanwärter)", player_list)
                    challenger = c2.selectbox("Spieler 2 (Thronanwärter)", [p for p in player_list if p != defender])
                
                format_choice = st.selectbox("Format", ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"])
                winner = st.selectbox("Sieger des Matches", [defender, challenger])
                comment = st.text_input("Match-Kommentar / Beweis-Notiz")
                
                if st.form_submit_button("KING HERAUSFORDERN & ERGEBNIS EINTRAGEN"):
                    # Update KotH logic
                    if winner == k_data["king"]:
                        k_data["streak"] += 1
                    else:
                        k_data["king"] = winner
                        k_data["streak"] = 1
                    
                    history_entry = {
                        "timestamp": get_now_str(),
                        "defender": defender,
                        "challenger": challenger,
                        "winner": winner,
                        "format": format_choice,
                        "comment": comment
                    }
                    k_data.setdefault("history", []).append(history_entry)
                    add_audit_log(db, f"KotH ({g_info['name']}): {winner} gewann gegen {defender if winner == challenger else challenger} ({format_choice})", user=winner)
                    update_db()
                    st.success(f"Ergebnis eingetragen! Neuer König: {k_data['king']} (Streak: {k_data['streak']})")
                    st.rerun()

        # Stats & History for selected game
        st.markdown("---")
        st.subheader("📊 SPIEL-STATISTIK & KOTH MATCH-HISTORIE")
        if not k_data.get("history"):
            st.write("Noch keine Kämpfe in diesem Spiel aufgezeichnet.")
        else:
            for entry in reversed(k_data["history"]):
                with st.container(border=True):
                    st.write(f"🏆 **Sieger: {entry['winner']}** | Format: `{entry['format']}` | Zeit: `{entry['timestamp']}`")
                    st.caption(f"Verteidiger: {entry['defender']} vs Herausforderer: {entry['challenger']}")
                    if entry.get("comment"):
                        st.markdown(f"💬 *\"{entry['comment']}\"*")

# ------------------------------------------------------------------------------
# 5. DOUBLE ELIMINATION BRACKET SECTION
# ------------------------------------------------------------------------------
elif page == "🌿 Double Elimination Bracket":
    st.title("🌿 DOUBLE ELIMINATION BRACKETS")
    
    # Status Banner
    status = db["config"].get("bracket_tournament_status", "OPEN")
    if status == "OPEN":
        st.markdown('<div class="status-open">🟢 TURNIER GEÖFFNET - MATCH-EINGABEN ERLAUBT</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-closed">🔴 TURNIER GESPERRT - MATCH-EINGABEN BLOCKIERT</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    brackets = db.get("brackets_de", [])
    if not brackets:
        st.info("Keine aktiven Brackets vorhanden. Der Admin kann im Admin-Bereich Brackets erstellen.")
    else:
        b_names = [f"{b['name']} ({b.get('game_name', 'Allgemein')})" for b in brackets]
        selected_b_idx = st.selectbox("WÄHLE EIN TURNIER BRACKET", range(len(brackets)), format_func=lambda x: b_names[x])
        bracket = brackets[selected_b_idx]
        
        st.subheader(f"Bracket: {bracket['name']}")
        st.caption(f"Spiel: {bracket.get('game_name', 'Keine Angabe')} | Status: {bracket.get('status', 'OPEN')}")
        
        # Display Matches
        w_matches = bracket.get("winners_matches", [])
        l_matches = bracket.get("losers_matches", [])
        
        col_w, col_l = st.columns(2)
        
        with col_w:
            st.markdown("### ⚔️ WINNERS BRACKET")
            for idx, m in enumerate(w_matches):
                with st.container(border=True):
                    st.write(f"**Match #{idx+1}** ({m.get('format', 'Bo3')})")
                    st.write(f"P1: **{m['p1']}**")
                    st.write(f"P2: **{m['p2']}**")
                    st.write(f"Gewinner: `{m.get('winner') or 'Ausstehend'}`")
                    
                    if not m.get('winner') and status == "OPEN":
                        w_choice = st.selectbox("Sieger wählen", [m['p1'], m['p2']], key=f"w_sel_{bracket['id']}_{idx}")
                        if st.button("Ergebnis eintragen", key=f"w_btn_{bracket['id']}_{idx}"):
                            m['winner'] = w_choice
                            add_audit_log(db, f"DE Bracket {bracket['name']} Winners Match #{idx+1} Sieger: {w_choice}")
                            update_db()
                            st.rerun()

        with col_l:
            st.markdown("### 💀 LOSERS BRACKET")
            if not l_matches:
                st.write("Keine Loser-Bracket Matches eingetragen.")
            for idx, m in enumerate(l_matches):
                with st.container(border=True):
                    st.write(f"**Loser Match #{idx+1}** ({m.get('format', 'Bo3')})")
                    st.write(f"P1: **{m['p1']}**")
                    st.write(f"P2: **{m['p2']}**")
                    st.write(f"Gewinner: `{m.get('winner') or 'Ausstehend'}`")
                    
                    if not m.get('winner') and status == "OPEN":
                        w_choice = st.selectbox("Sieger wählen", [m['p1'], m['p2']], key=f"l_sel_{bracket['id']}_{idx}")
                        if st.button("Ergebnis eintragen", key=f"l_btn_{bracket['id']}_{idx}"):
                            m['winner'] = w_choice
                            add_audit_log(db, f"DE Bracket {bracket['name']} Losers Match #{idx+1} Sieger: {w_choice}")
                            update_db()
                            st.rerun()

# ------------------------------------------------------------------------------
# 6. EINSPRUCH & ANTRÄGE SECTION
# ------------------------------------------------------------------------------
elif page == "📩 Einspruch & Anträge":
    st.title("📩 ANTRÄGE & EINSPRÜCHE")
    
    with st.form("appeal_form", clear_on_submit=True):
        st.subheader("BLUTZENTRALE: EINSPRUCH OD. BANN-ANTRAG EINREICHEN")
        player_list = list(db["players"].keys())
        sender = st.selectbox("Dein Name (Antragsteller)", player_list if player_list else ["-"])
        target = st.selectbox("Betroffener Spieler / Gegenstand", player_list if player_list else ["-"])
        reason = st.text_area("Ausführliche Begründung / Vorfall schildern")
        
        if st.form_submit_button("ANTRAG ABSCHICKEN"):
            if sender and reason:
                new_appeal = {
                    "id": len(db["appeals"]) + 1,
                    "timestamp": get_now_str(),
                    "sender": sender,
                    "target": target,
                    "reason": reason,
                    "status": "OFFEN",
                    "defense": ""
                }
                db["appeals"].append(new_appeal)
                add_audit_log(db, f"Einspruch #{new_appeal['id']} eingereicht von {sender} gegen {target}", user=sender)
                update_db()
                st.success("Antrag eingereicht.")
                st.rerun()

    st.markdown("---")
    st.subheader("📜 LAUFENDE VERFAHREN & STELLUNGNAHMEN")
    for app in db["appeals"]:
        st.markdown(f"""
        <div class="blood-card">
            <h4>ANTRAG #{app['id']} - STATUS: {app['status']}</h4>
            <p><b>Von:</b> {app['sender']} | <b>Gegen:</b> {app['target']} | <b>Zeit:</b> {app['timestamp']}</p>
            <p><b>Begründung:</b> {app['reason']}</p>
            <p><b>Stellungnahme:</b> {app['defense'] or 'Keine abgegeben'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if app["status"] == "OFFEN":
            with st.expander(f"Stellungnahme abgeben für Antrag #{app['id']}"):
                def_text = st.text_input("Verteidigung / Gegen-Aussage", key=f"def_{app['id']}")
                if st.button("Stellungnahme Speichern", key=f"btn_def_{app['id']}"):
                    app["defense"] = def_text
                    update_db()
                    st.rerun()

# ------------------------------------------------------------------------------
# 7. ADMIN-BEREICH (FULL CONTROL)
# ------------------------------------------------------------------------------
elif page == "⚙️ Admin-Bereich":
    st.title("⚙️ ADMIN CONTROL PANEL")
    
    admin_pw = st.secrets.get("ADMIN_PASSWORD", "maximus123")
    input_pw = st.text_input("ADMIN-PASSWORT EINGEBEN", type="password")
    
    if input_pw != admin_pw:
        st.error("ZUGRIFF VERWEIGERT. ZUTRITT NUR FÜR DEN HERRSCHER.")
    else:
        st.success("AUTHENTIFIZIERUNG ERFOLGREICH.")
        
        tab_admin = st.tabs([
            "🎮 Spiele & Steam API", 
            "👥 Spieler", 
            "🌿 Bracket Generator", 
            "👑 KotH Overrides", 
            "🔒 Turnier-Status", 
            "📩 Einsprüche", 
            "📊 Audit-Logs", 
            "💾 Backup"
        ])
        
        # TAB 1: Spiele & Steam Info
        with tab_admin[0]:
            st.subheader("Spiel-Verwaltung (Steam AppID / Covers)")
            games = db.setdefault("games", {})
            
            with st.form("add_game_form", clear_on_submit=True):
                g_name = st.text_input("Spiel Name (z.B. Tekken 8)")
                g_appid = st.text_input("Steam AppID (z.B. 1778820)")
                g_cover = st.text_input("Custom Image URL (Optional - überschreibt Steam Banner)")
                if st.form_submit_button("SPIEL HINZUFÜGEN"):
                    if g_name:
                        new_id = str(len(games) + 1)
                        games[new_id] = {
                            "name": g_name,
                            "steam_appid": g_appid,
                            "custom_cover": g_cover
                        }
                        db["koth"].setdefault(new_id, {"king": None, "streak": 0, "history": []})
                        add_audit_log(db, f"Spiel hinzugefügt: {g_name} (Steam: {g_appid})", user="Admin")
                        update_db()
                        st.rerun()
            
            st.markdown("---")
            st.write("Vorhandene Spiele:")
            for g_id, g in list(games.items()):
                col1, col2 = st.columns([3, 1])
                col1.write(f"**ID {g_id}: {g['name']}** (Steam AppID: {g['steam_appid'] or 'Keine'})")
                if col2.button(f"Löschen #{g_id}", key=f"del_g_{g_id}"):
                    del games[g_id]
                    if g_id in db["koth"]:
                        del db["koth"][g_id]
                    update_db()
                    st.rerun()

        # TAB 2: Spieler-Verwaltung
        with tab_admin[1]:
            st.subheader("Spieler hinzufügen / löschen")
            col1, col2 = st.columns(2)
            new_p = col1.text_input("Neuer Spieler Name")
            if col1.button("Spieler Anlegen") and new_p:
                if new_p not in db["players"]:
                    db["players"][new_p] = {"created_at": get_now_str()}
                    add_audit_log(db, f"Spieler angelegt: {new_p}", user="Admin")
                    update_db()
                    st.rerun()
            
            del_p = col2.selectbox("Spieler entfernen", ["-"] + list(db["players"].keys()))
            if col2.button("Spieler Löschen") and del_p != "-":
                del db["players"][del_p]
                add_audit_log(db, f"Spieler entfernt: {del_p}", user="Admin")
                update_db()
                st.rerun()

        # TAB 3: Bracket Generator (Double Elimination)
        with tab_admin[2]:
            st.subheader("🌿 Double Elimination Bracket erstellen")
            p_list = list(db["players"].keys())
            
            if len(p_list) < 2:
                st.warning("Mindestens 2 Spieler erforderlich, um ein Bracket zu generieren.")
            else:
                b_name = st.text_input("Bracket / Turnier Name", value="Blutfehde 2026")
                b_game = st.selectbox("Spiel zuordnen", [g["name"] for g in db.get("games", {}).values()])
                selected_players = st.multiselect("Teilnehmende Spieler wählen", p_list, default=p_list)
                
                if st.button("DOUBLE ELIMINATION BRACKET GENERIEREN"):
                    w_matches = []
                    # Paare für R1 bilden
                    for i in range(0, len(selected_players)-1, 2):
                        w_matches.append({
                            "p1": selected_players[i],
                            "p2": selected_players[i+1],
                            "winner": None,
                            "format": "Best of 3"
                        })
                    
                    new_b = {
                        "id": len(db.get("brackets_de", [])) + 1,
                        "name": b_name,
                        "game_name": b_game,
                        "status": "OPEN",
                        "winners_matches": w_matches,
                        "losers_matches": []
                    }
                    db.setdefault("brackets_de", []).append(new_b)
                    add_audit_log(db, f"DE Bracket '{b_name}' für {b_game} generiert.", user="Admin")
                    update_db()
                    st.success("Bracket erfolgreich erstellt!")
                    st.rerun()

        # TAB 4: KotH Overrides
        with tab_admin[3]:
            st.subheader("👑 King of the Hill Manuelle Overrides")
            games = db.get("games", {})
            if games:
                ov_g = st.selectbox("Spiel wählen", list(games.keys()), format_func=lambda x: games[x]["name"], key="ov_g")
                k_data = db["koth"].setdefault(ov_g, {"king": None, "streak": 0, "history": []})
                
                col1, col2 = st.columns(2)
                new_king = col1.selectbox("König festlegen", ["NIEMAND"] + list(db["players"].keys()))
                new_streak = col2.number_input("Streak anpassen", min_value=0, value=k_data.get("streak", 0))
                
                if st.button("KotH Daten Manuell Überschreiben"):
                    k_data["king"] = None if new_king == "NIEMAND" else new_king
                    k_data["streak"] = new_streak
                    add_audit_log(db, f"KotH Override ({games[ov_g]['name']}): King={new_king}, Streak={new_streak}", user="Admin")
                    update_db()
                    st.success("Erfolgreich überschrieben!")
                    st.rerun()

        # TAB 5: Turnier-Status Control (Brackets)
        with tab_admin[4]:
            st.subheader("🔒 Bracket Turnier-Status Kontrollzentrum")
            st.caption("Steuert, ob Spieler in den Brackets Ergebnisse eintragen können.")
            curr_s = db["config"].get("bracket_tournament_status", "OPEN")
            
            c1, c2 = st.columns(2)
            if c1.button("🟢 TURNIER ÖFFNEN (Eingaben Freischalten)"):
                db["config"]["bracket_tournament_status"] = "OPEN"
                add_audit_log(db, "Turnier-Status auf GEÖFFNET gesetzt", user="Admin")
                update_db()
                st.rerun()
                
            if c2.button("🔴 TURNIER SPERREN (Eingaben Blockieren)"):
                db["config"]["bracket_tournament_status"] = "CLOSED"
                add_audit_log(db, "Turnier-Status auf GESPERRT gesetzt", user="Admin")
                update_db()
                st.rerun()

        # TAB 6: Einsprüche verwalten
        with tab_admin[5]:
            st.subheader("📩 Einsprüche & Anträge Verwalten")
            for app in db["appeals"]:
                st.write(f"#{app['id']} von {app['sender']} gegen {app['target']}: {app['reason']}")
                col1, col2 = st.columns(2)
                if col1.button("Akzeptieren / Klären", key=f"adm_app_acc_{app['id']}"):
                    app["status"] = "GEKLÄRT"
                    add_audit_log(db, f"Einspruch #{app['id']} als geklärt markiert", user="Admin")
                    update_db()
                    st.rerun()
                if col2.button("Ablehnen / Verwerfen", key=f"adm_app_rej_{app['id']}"):
                    app["status"] = "ABGELEHNT"
                    add_audit_log(db, f"Einspruch #{app['id']} abgelehnt", user="Admin")
                    update_db()
                    st.rerun()

        # TAB 7: Audit Logs
        with tab_admin[6]:
            st.subheader("📊 Audit Logs")
            st.dataframe(db["audit_logs"], use_container_width=True)

        # TAB 8: Backup & Recovery
        with tab_admin[7]:
            st.subheader("💾 Backup & Wiederherstellung")
            json_str = json.dumps(db, indent=2, ensure_ascii=False)
            st.download_button("data.json herunterladen", data=json_str, file_name="data_backup.json", mime="application/json")
            
            uploaded_file = st.file_uploader("Backup JSON hochladen", type=["json"])
            if uploaded_file is not None:
                try:
                    data = json.load(uploaded_file)
                    st.session_state.db = data
                    save_data(data)
                    st.success("Wiederherstellung erfolgreich!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Backup: {e}")
