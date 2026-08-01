import streamlit as st
import json
import os
import requests
import base64
import math
from datetime import datetime
from zoneinfo import ZoneInfo

# ------------------------------------------------------------------------------
# 1. KONFIGURATION & STYLES (CYBERPUNK NEON THEME)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="COMPETE MAXIMUS",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Neon Glow / Dark Mode UI
st.markdown("""
<style>
    /* Dark Theme Base */
    .stApp {
        background-color: #0b0e14;
        color: #e0e6ed;
    }
    
    /* Neon Text Headers */
    h1, h2, h3 {
        color: #00f3ff !important;
        text-shadow: 0 0 8px rgba(0, 243, 255, 0.4);
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Neon Glow Containers */
    div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stContainer"] {
        border: 1px solid rgba(0, 243, 255, 0.2) !important;
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 8px !important;
        box-shadow: 0 0 10px rgba(0, 243, 255, 0.05);
    }
    
    /* Status Boxes */
    .status-open {
        background-color: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .status-closed {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid #ef4444;
        color: #f87171;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    .status-pending {
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px solid #f59e0b;
        color: #fbbf24;
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: bold;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #00f3ff 0%, #7000ff 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(0, 243, 255, 0.6) !important;
        transform: translateY(-1px);
    }
    
    /* Custom Cards */
    .neon-card-green {
        border: 1px solid #10b981;
        background: rgba(16, 185, 129, 0.05);
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.2);
        margin-bottom: 10px;
    }
    .neon-card-red {
        border: 1px solid #ef4444;
        background: rgba(239, 68, 68, 0.05);
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(239, 68, 68, 0.2);
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=1)

# ------------------------------------------------------------------------------
# 2. PERSISTENZ, ZEITZONE & GITHUB AUTO-SYNC
# ------------------------------------------------------------------------------
DATA_FILE = "data.json"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_now_str():
    return datetime.now(BERLIN_TZ).strftime("%Y-%m-%d %H:%M:%S")

def get_default_data():
    return {
        "config": {
            "tournament_status_override": "AUTO", # "OPEN", "CLOSED", "AUTO"
            "current_season": 1
        },
        "players": {},
        "ladder_matches": [],
        "brackets": {
            "single": {"rounds": []},
            "double": {"winners": [], "losers": [], "grand_final": None}
        },
        "round_robin": [],
        "koth": {
            "king": None,
            "streak": 0,
            "history": []
        },
        "swiss": {
            "current_round": 0,
            "rounds": []
        },
        "appeals": [],
        "audit_logs": [],
        "history": []
    }

def sync_to_github(json_str):
    """Synchronisiert die data.json mit dem GitHub Repository via REST API."""
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    path = st.secrets.get("GITHUB_FILE_PATH", "data.json")
    
    if not token or not repo:
        return  # Auto-Sync überspringen, falls Secrets nicht konfiguriert sind

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    
    # 1. Hohle aktuellen File SHA
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    # 2. Update Content
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

# Session State Initialisierung
if "db" not in st.session_state:
    st.session_state.db = load_data()

def update_db():
    save_data(st.session_state.db)

db = st.session_state.db

# ------------------------------------------------------------------------------
# 3. HILFSFUNKTIONEN & LOGIK
# ------------------------------------------------------------------------------
def is_tournament_open():
    status = db["config"].get("tournament_status_override", "AUTO")
    if status == "OPEN":
        return True
    if status == "CLOSED":
        return False
    # Auto-Zeitplan: Beispielhaft immer offen außer Sonntags von 0-6 Uhr
    now = datetime.now(BERLIN_TZ)
    if now.weekday() == 6 and 0 <= now.hour < 6:
        return False
    return True

def recalculate_elo():
    # Setze alle Spieler zurück
    for p in db["players"].values():
        p["elo"] = 1000
        p["wins"] = 0
        p["losses"] = 0
        p["streak"] = 0
        p["max_streak"] = 0
        p["matches_played"] = 0

    # Sortiere bestätigte Ladder-Matches nach Zeitstempel
    confirmed = [m for m in db["ladder_matches"] if m.get("status") == "APPROVED"]
    confirmed.sort(key=lambda x: x["timestamp"])

    for m in confirmed:
        p1, p2 = m["player1"], m["player2"]
        if p1 not in db["players"] or p2 not in db["players"]:
            continue
        
        s1, s2 = m["score1"], m["score2"]
        win1 = s1 > s2
        
        # Elo Delta
        k = 32
        r1, r2 = db["players"][p1]["elo"], db["players"][p2]["elo"]
        e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
        e2 = 1 - e1
        a1 = 1.0 if win1 else 0.0
        a2 = 0.0 if win1 else 1.0
        
        db["players"][p1]["elo"] = round(r1 + k * (a1 - e1))
        db["players"][p2]["elo"] = round(r2 + k * (a2 - e2))
        
        # Stats
        db["players"][p1]["matches_played"] += 1
        db["players"][p2]["matches_played"] += 1
        
        if win1:
            db["players"][p1]["wins"] += 1
            db["players"][p1]["streak"] += 1
            if db["players"][p1]["streak"] > db["players"][p1]["max_streak"]:
                db["players"][p1]["max_streak"] = db["players"][p1]["streak"]
            
            db["players"][p2]["losses"] += 1
            db["players"][p2]["streak"] = 0
        else:
            db["players"][p2]["wins"] += 1
            db["players"][p2]["streak"] += 1
            if db["players"][p2]["streak"] > db["players"][p2]["max_streak"]:
                db["players"][p2]["max_streak"] = db["players"][p2]["streak"]
            
            db["players"][p1]["losses"] += 1
            db["players"][p1]["streak"] = 0

# ------------------------------------------------------------------------------
# 4. SIDEBAR & NAVIGATION
# ------------------------------------------------------------------------------
st.sidebar.title("⚔️ COMPETE MAXIMUS")
st.sidebar.caption(f"Deutschland (Berlin) | {get_now_str()}")

status_open = is_tournament_open()
if status_open:
    st.sidebar.markdown('<div class="status-open">🟢 TURNIER GEÖFFNET</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="status-closed">🔴 TURNIER GESPERRT</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard & Stats", "🥇 Ladder System", "🌿 Bracket System", "⚔️ Weitere Modi", "📩 Einspruch & Anträge", "⚙️ Admin-Bereich"]
)

# ------------------------------------------------------------------------------
# 5. DASHBOARD & ALL-TIME STATS
# ------------------------------------------------------------------------------
if page == "📊 Dashboard & Stats":
    st.title("📊 Tournament Dashboard & All-Time Stats")
    
    recalculate_elo()
    players = db["players"]
    
    if not players:
        st.info("Noch keine Spieler registriert. Gehe in den Admin-Bereich um Spieler anzulegen.")
    else:
        col1, col2, col3 = st.columns(3)
        top_elo = max(players.items(), key=lambda x: x[1]["elo"]) if players else ("-", {"elo": 0})
        top_streak = max(players.items(), key=lambda x: x[1]["max_streak"]) if players else ("-", {"max_streak": 0})
        total_matches = sum(p["matches_played"] for p in players.values()) // 2
        
        col1.metric("👑 Rang 1 (Elo)", f"{top_elo[0]} ({top_elo[1]['elo']})")
        col2.metric("🔥 Höchste Streak", f"{top_streak[0]} ({top_streak[1]['max_streak']} Siege)")
        col3.metric("⚔️ Absolvierte Matches", total_matches)
        
        st.markdown("### 🏆 Leaderboard")
        leaderboard = []
        for name, p in players.items():
            wr = round((p["wins"] / p["matches_played"] * 100), 1) if p["matches_played"] > 0 else 0.0
            leaderboard.append({
                "Spieler": name,
                "Elo": p["elo"],
                "Matches": p["matches_played"],
                "Siege": p["wins"],
                "Niederlagen": p["losses"],
                "Winrate (%)": wr,
                "Aktuelle Streak": p["streak"],
                "Max Streak": p["max_streak"]
            })
        
        leaderboard.sort(key=lambda x: x["Elo"], reverse=True)
        st.dataframe(leaderboard, use_container_width=True)
        
        st.markdown("### 📈 Saisons & Gewinner-Historie")
        if not db["history"]:
            st.write("Keine vergangenen Saisons aufgezeichnet.")
        else:
            for entry in reversed(db["history"]):
                with st.expander(f"🏆 Saison {entry.get('season')} - Sieger: {entry.get('winner')} ({entry.get('date')})"):
                    st.write(f"**Details:** {entry.get('details', 'Keine weiteren Angaben')}")
                    st.write("**Top-Spieler der Saison:**")
                    st.json(entry.get("top_players", {}))

# ------------------------------------------------------------------------------
# 6. LADDER SYSTEM (RANGLISTE)
# ------------------------------------------------------------------------------
elif page == "🥇 Ladder System":
    st.title("🥇 Ladder Rangliste & Match-Eintragung")
    
    if not is_tournament_open():
        st.warning("Das Turnier ist aktuell gesperrt. Neue Matches können nicht eingetragen werden.")
    
    st.subheader("Match eintragen")
    player_list = list(db["players"].keys())
    
    if len(player_list) < 2:
        st.info("Mindestens 2 Spieler erforderlich.")
    else:
        with st.form("ladder_match_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            p1 = col1.selectbox("Eintrager (Spieler 1)", player_list, key="l_p1")
            p2 = col2.selectbox("Gegner (Spieler 2)", [p for p in player_list if p != p1], key="l_p2")
            
            sc1 = col1.number_input(f"Punkte {p1}", min_value=0, value=2)
            sc2 = col2.number_input(f"Punkte {p2}", min_value=0, value=0)
            
            note = st.text_input("Beweis-Notiz / Begründung (z.B. Screenshot-Link, Match-Details)")
            submitted = st.form_submit_button("Match Einreichen")
            
            if submitted:
                if not is_tournament_open():
                    st.error("Turnier ist gesperrt!")
                else:
                    new_match = {
                        "id": len(db["ladder_matches"]) + 1,
                        "timestamp": get_now_str(),
                        "player1": p1,
                        "player2": p2,
                        "score1": sc1,
                        "score2": sc2,
                        "note": note,
                        "status": "PENDING", # PENDING, APPROVED, REJECTED
                        "confirmed_by_p2": False
                    }
                    db["ladder_matches"].append(new_match)
                    add_audit_log(db, f"Ladder Match eingereicht: {p1} vs {p2} ({sc1}:{sc2})", user=p1)
                    update_db()
                    st.success("Match eingereicht! Wartet auf Bestätigung durch den Gegner oder Admin.")
    
    st.markdown("---")
    st.subheader("Ausstehende Matches (Bestätigung erforderlich)")
    pending_matches = [m for m in db["ladder_matches"] if m["status"] == "PENDING"]
    
    if not pending_matches:
        st.write("Keine ausstehenden Matches.")
    else:
        for m in pending_matches:
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.write(f"**{m['player1']}** ({m['score1']}) vs **{m['player2']}** ({m['score2']})")
                col1.caption(f"Notiz: {m['note']} | Zeit: {m['timestamp']}")
                
                # Gegner Bestätigung
                if col2.button(f"Als {m['player2']} bestätigen", key=f"confirm_{m['id']}"):
                    m["status"] = "APPROVED"
                    m["confirmed_by_p2"] = True
                    recalculate_elo()
                    add_audit_log(db, f"Ladder Match #{m['id']} durch {m['player2']} bestätigt", user=m['player2'])
                    update_db()
                    st.rerun()

# ------------------------------------------------------------------------------
# 7. BRACKET SYSTEM (TURNIER-BÄUME)
# ------------------------------------------------------------------------------
elif page == "🌿 Bracket System":
    st.title("🌿 Bracket System (Elimination)")
    
    tab1, tab2 = st.tabs(["Single Elimination", "Double Elimination"])
    
    with tab1:
        st.subheader("Single Elimination Bracket")
        rounds = db["brackets"]["single"]["rounds"]
        
        if not rounds:
            st.info("Kein Single Elimination Bracket aktiv. Admin muss ein Bracket generieren.")
        else:
            for r_idx, r in enumerate(rounds):
                st.markdown(f"#### Runde {r_idx + 1}")
                cols = st.columns(len(r))
                for m_idx, match in enumerate(r):
                    with cols[m_idx if m_idx < len(cols) else 0]:
                        with st.container(border=True):
                            p1 = match["p1"] or "TBD"
                            p2 = match["p2"] or "BYE / TBD"
                            winner = match.get("winner")
                            
                            st.write(f"**Match {m_idx+1}**")
                            st.write(f"🟢 {p1}" if winner == p1 else p1)
                            st.write("VS")
                            st.write(f"🟢 {p2}" if winner == p2 else p2)
                            
                            if not winner and p1 != "TBD" and p2 not in ["TBD", "BYE"] and is_tournament_open():
                                win_choice = st.selectbox("Sieger eintragen", [p1, p2], key=f"se_{r_idx}_{m_idx}")
                                if st.button("Ergebnis Speichern", key=f"btn_se_{r_idx}_{m_idx}"):
                                    match["winner"] = win_choice
                                    # Automatischer Fortschritt in die nächste Runde
                                    if r_idx + 1 < len(rounds):
                                        next_m_idx = m_idx // 2
                                        if m_idx % 2 == 0:
                                            rounds[r_idx+1][next_m_idx]["p1"] = win_choice
                                        else:
                                            rounds[r_idx+1][next_m_idx]["p2"] = win_choice
                                    add_audit_log(db, f"Single Elimination R{r_idx+1}M{m_idx+1} Sieger: {win_choice}")
                                    update_db()
                                    st.rerun()

    with tab2:
        st.subheader("Double Elimination Bracket")
        st.info("Double Elimination Brackets werden im Admin-Bereich initialisiert.")
        # Vereinfachte Darstellung der DE Brackets
        st.json(db["brackets"]["double"])

# ------------------------------------------------------------------------------
# 8. WEITERE WETTKAMPF-MODI
# ------------------------------------------------------------------------------
elif page == "⚔️ Weitere Modi":
    st.title("⚔️ Weitere Wettkampf-Modi")
    
    mode = st.selectbox("Modus Auswählen", ["Round-Robin (Jeder gegen Jeden)", "King of the Hill", "Schweizer System"])
    
    if mode == "Round-Robin (Jeder gegen Jeden)":
        st.subheader("🔄 Round-Robin Tabelle")
        rr = db["round_robin"]
        if not rr:
            st.info("Kein Round-Robin Turnier aktiv.")
        else:
            for idx, match in enumerate(rr):
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.write(f"**{match['p1']}** vs **{match['p2']}**")
                if match["winner"]:
                    col2.success(f"Sieger: {match['winner']}")
                elif is_tournament_open():
                    w = col2.selectbox("Sieger", [match['p1'], match['p2']], key=f"rr_{idx}")
                    if col3.button("Eintragen", key=f"rr_btn_{idx}"):
                        match["winner"] = w
                        add_audit_log(db, f"Round-Robin Match {match['p1']} vs {match['p2']} -> Sieger: {w}")
                        update_db()
                        st.rerun()

    elif mode == "King of the Hill":
        st.subheader("👑 King of the Hill (K.o.-Challenge)")
        koth = db["koth"]
        col1, col2 = st.columns(2)
        col1.metric("Aktueller König", koth.get("king") or "Keiner")
        col2.metric("Win-Streak", koth.get("streak", 0))
        
        st.markdown("---")
        st.subheader("König herausfordern")
        players = [p for p in db["players"].keys() if p != koth.get("king")]
        if players and is_tournament_open():
            challenger = st.selectbox("Herausforderer wählen", players)
            if st.button("Herausforderung eintragen"):
                st.session_state.active_koth_challenger = challenger
                st.rerun()
                
            if "active_koth_challenger" in st.session_state:
                ch = st.session_state.active_koth_challenger
                st.write(f"**Match:** {koth.get('king')} (König) vs {ch} (Herausforderer)")
                winner = st.radio("Sieger", [koth.get('king'), ch])
                if st.button("Ergebnis Bestätigen"):
                    if winner == koth.get('king'):
                        koth["streak"] += 1
                    else:
                        koth["king"] = winner
                        koth["streak"] = 1
                    koth["history"].append({"timestamp": get_now_str(), "winner": winner, "challenger": ch})
                    add_audit_log(db, f"KotH Match: {winner} hat gewonnen. Neuer Streak: {koth['streak']}")
                    del st.session_state.active_koth_challenger
                    update_db()
                    st.rerun()

    elif mode == "Schweizer System":
        st.subheader("🇨🇭 Schweizer System")
        swiss = db["swiss"]
        st.write(f"Aktuelle Runde: **{swiss.get('current_round', 0)}**")
        st.json(swiss.get("rounds", []))

# ------------------------------------------------------------------------------
# 9. EINSPRUCH & ANTRÄGE
# ------------------------------------------------------------------------------
elif page == "📩 Einspruch & Anträge":
    st.title("📩 Anträge & Einsprüche")
    
    with st.form("appeal_form", clear_on_submit=True):
        st.subheader("Neuen Einspruch / Bann-Antrag einreichen")
        player_list = list(db["players"].keys())
        sender = st.selectbox("Dein Name", player_list if player_list else ["-"])
        target = st.selectbox("Betroffener Spieler / Match", player_list if player_list else ["-"])
        reason = st.text_area("Begründung / Vorfall schildern")
        
        if st.form_submit_button("Einspruch Einreichen"):
            if sender and reason:
                new_appeal = {
                    "id": len(db["appeals"]) + 1,
                    "timestamp": get_now_str(),
                    "sender": sender,
                    "target": target,
                    "reason": reason,
                    "status": "OPEN", # OPEN, RESOLVED, REJECTED
                    "defense": ""
                }
                db["appeals"].append(new_appeal)
                add_audit_log(db, f"Einspruch #{new_appeal['id']} eingereicht von {sender} gegen {target}", user=sender)
                update_db()
                st.success("Einspruch erfolgreich eingereicht.")

    st.markdown("---")
    st.subheader("Aktive Anträge & Stellungnahmen")
    for app in db["appeals"]:
        css_class = "neon-card-red" if app["status"] == "OPEN" else "neon-card-green"
        st.markdown(f"""
        <div class="{css_class}">
            <h4>Antrag #{app['id']} - Status: {app['status']}</h4>
            <p><b>Von:</b> {app['sender']} | <b>Gegen:</b> {app['target']} | <b>Zeit:</b> {app['timestamp']}</p>
            <p><b>Begründung:</b> {app['reason']}</p>
            <p><b>Verteidigung:</b> {app['defense'] or 'Keine'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Verteidigung hinzufügen
        if app["status"] == "OPEN":
            with st.expander(f"Stellungnahme / Verteidigung für #{app['id']} abgeben"):
                def_text = st.text_input("Verteidigung", key=f"def_{app['id']}")
                if st.button("Stellungnahme Speichern", key=f"btn_def_{app['id']}"):
                    app["defense"] = def_text
                    update_db()
                    st.rerun()

# ------------------------------------------------------------------------------
# 10. ADMIN-BEREICH (VOLLE KONTROLLE)
# ------------------------------------------------------------------------------
elif page == "⚙️ Admin-Bereich":
    st.title("⚙️ Admin Control Panel")
    
    admin_pw = st.secrets.get("ADMIN_PASSWORD", "maximus123")
    input_pw = st.text_input("Admin-Passwort eingeben", type="password")
    
    if input_pw != admin_pw:
        st.error("Zugriff verweigert. Bitte gültiges Admin-Passwort eingeben.")
    else:
        st.success("Erfolgreich als Admin authentifiziert.")
        
        tab_admin = st.tabs([
            "👥 Spieler", 
            "⚔️ Matches", 
            "📩 Einsprüche", 
            "👑 Override", 
            "🔓 Status", 
            "🔄 Saison", 
            "📊 Logs", 
            "✏️ Historie", 
            "💾 Backup"
        ])
        
        # TAB 1: Spieler-Verwaltung
        with tab_admin[0]:
            st.subheader("Spieler hinzufügen / löschen")
            col1, col2 = st.columns(2)
            new_p = col1.text_input("Neuer Spieler Name")
            if col1.button("Spieler Anlegen") and new_p:
                if new_p not in db["players"]:
                    db["players"][new_p] = {"elo": 1000, "wins": 0, "losses": 0, "streak": 0, "max_streak": 0, "matches_played": 0}
                    add_audit_log(db, f"Spieler angelegt: {new_p}", user="Admin")
                    update_db()
                    st.rerun()
            
            del_p = col2.selectbox("Spieler löschen", ["-"] + list(db["players"].keys()))
            if col2.button("Spieler Entfernen") and del_p != "-":
                del db["players"][del_p]
                add_audit_log(db, f"Spieler gelöscht: {del_p}", user="Admin")
                update_db()
                st.rerun()

        # TAB 2: Match-Verwaltung
        with tab_admin[1]:
            st.subheader("Match Freigabe & Korrektur")
            for m in db["ladder_matches"]:
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.write(f"#{m['id']}: {m['player1']} ({m['score1']}) vs {m['player2']} ({m['score2']}) - Status: {m['status']}")
                if col2.button("Genehmigen", key=f"adm_app_{m['id']}"):
                    m["status"] = "APPROVED"
                    recalculate_elo()
                    add_audit_log(db, f"Admin genehmigte Match #{m['id']}", user="Admin")
                    update_db()
                    st.rerun()
                if col3.button("Ablehnen", key=f"adm_rej_{m['id']}"):
                    m["status"] = "REJECTED"
                    recalculate_elo()
                    add_audit_log(db, f"Admin lehnte Match #{m['id']} ab", user="Admin")
                    update_db()
                    st.rerun()

        # TAB 3: Einsprüche bearbeiten
        with tab_admin[2]:
            st.subheader("Einsprüche verwalten")
            for app in db["appeals"]:
                st.write(f"#{app['id']} von {app['sender']} gegen {app['target']}: {app['reason']}")
                col1, col2 = st.columns(2)
                if col1.button("Stattgeben / Akzeptieren", key=f"app_acc_{app['id']}"):
                    app["status"] = "RESOLVED"
                    add_audit_log(db, f"Einspruch #{app['id']} akzeptiert", user="Admin")
                    update_db()
                    st.rerun()
                if col2.button("Ablehnen", key=f"app_ref_{app['id']}"):
                    app["status"] = "REJECTED"
                    add_audit_log(db, f"Einspruch #{app['id']} abgelehnt", user="Admin")
                    update_db()
                    st.rerun()

        # TAB 4: Match-Override
        with tab_admin[3]:
            st.subheader("👑 Sieger manuell erzwingen (Bracket / Round-Robin)")
            p_list = list(db["players"].keys())
            st.info("Ermöglicht das direkte Überschreiben von Ergebnissen im System.")

        # TAB 5: Status-Override
        with tab_admin[4]:
            st.subheader("🔓 Turnier Status-Override")
            curr_status = db["config"].get("tournament_status_override", "AUTO")
            new_status = st.radio("Status wählen", ["OPEN", "CLOSED", "AUTO"], index=["OPEN", "CLOSED", "AUTO"].index(curr_status))
            if st.button("Status Speichern"):
                db["config"]["tournament_status_override"] = new_status
                add_audit_log(db, f"Turnier-Status auf {new_status} gesetzt", user="Admin")
                update_db()
                st.rerun()

        # TAB 6: Saison Abschließen
        with tab_admin[5]:
            st.subheader("🔄 Saison abschließen & Historie archivieren")
            if st.button("Aktuelle Saison Abschließen & Reset"):
                recalculate_elo()
                top_player = max(db["players"].items(), key=lambda x: x[1]["elo"])[0] if db["players"] else "Keiner"
                
                history_entry = {
                    "season": db["config"]["current_season"],
                    "date": get_now_str(),
                    "winner": top_player,
                    "top_players": db["players"],
                    "details": f"Saison {db['config']['current_season']} erfolgreich beendet."
                }
                db["history"].append(history_entry)
                db["config"]["current_season"] += 1
                
                # Matches zurücksetzen
                db["ladder_matches"] = []
                add_audit_log(db, f"Saison {history_entry['season']} abgeschlossen. Gewinner: {top_player}", user="Admin")
                update_db()
                st.success("Saison archiviert und neue Saison gestartet!")

        # TAB 7: Audit-Logs
        with tab_admin[6]:
            st.subheader("📊 Lückenlose Audit-Logs")
            st.dataframe(db["audit_logs"], use_container_width=True)

        # TAB 8: Historie Bearbeiten
        with tab_admin[7]:
            st.subheader("✏️ Historie & Gewinner anpassen")
            if st.button("Manuell Historien-Eintrag hinzufügen"):
                db["history"].append({
                    "season": len(db["history"]) + 1,
                    "date": get_now_str(),
                    "winner": "Manueller Eintrag",
                    "details": "Admin Modifikation"
                })
                update_db()
                st.rerun()

        # TAB 9: Backup & Recovery
        with tab_admin[8]:
            st.subheader("💾 Backup & Recovery")
            
            # Download
            json_str = json.dumps(db, indent=2, ensure_ascii=False)
            st.download_button("data.json herunterladen", data=json_str, file_name="data_backup.json", mime="application/json")
            
            # Upload
            uploaded_file = st.file_uploader("Backup JSON wiederherstellen", type=["json"])
            if uploaded_file is not None:
                try:
                    data = json.load(uploaded_file)
                    st.session_state.db = data
                    save_data(data)
                    st.success("Daten erfolgreich wiederhergestellt!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler beim Laden des Backups: {e}")
