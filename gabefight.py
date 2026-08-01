import streamlit as st
import json
import os
import requests
import base64
import math
from datetime import datetime
from zoneinfo import ZoneInfo

# ------------------------------------------------------------------------------
# 1. KONFIGURATION & STYLES (DARK METAL THEME)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="COMPETUS MAXIMUS",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Metal Aesthetic
st.markdown("""
<style>
    .stApp {
        background-color: #0c0d10;
        color: #e2e8f0;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    h1, h2, h3 {
        color: #e2e8f0 !important;
        letter-spacing: 1px;
        font-weight: 700 !important;
    }
    
    div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stContainer"] {
        border: 1px solid #2d3748 !important;
        background-color: #14171d !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        margin-bottom: 15px;
    }
    
    .status-open {
        background-color: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #34d399;
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: bold;
        text-align: center;
    }
    .status-closed {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid #ef4444;
        color: #f87171;
        padding: 6px 12px;
        border-radius: 4px;
        font-weight: bold;
        text-align: center;
    }

    .stButton>button {
        background: linear-gradient(180deg, #2b303c 0%, #1a1d24 100%) !important;
        color: #00f0ff !important;
        border: 1px solid #00f0ff !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background: #00f0ff !important;
        color: #000000 !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.5) !important;
    }
    
    .koth-card {
        border: 1px solid #334155;
        background: #1e293b;
        padding: 15px;
        border-radius: 6px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. PERSISTENZ & UTILS
# ------------------------------------------------------------------------------
DATA_FILE = "data.json"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_now_str():
    return datetime.now(BERLIN_TZ).strftime("%Y-%m-%d %H:%M:%S")

def get_default_data():
    return {
        "config": {
            "bracket_tournament_status": "OPEN",
            "current_season": 1
        },
        "players": {},
        "games": {}, # KPL. LEER - Keine Vorab-Spiele
        "koth": {},
        "challenges": [],
        "brackets_de": [],
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
    return "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER"

if "db" not in st.session_state:
    st.session_state.db = load_data()

def update_db():
    save_data(st.session_state.db)

db = st.session_state.db

# ------------------------------------------------------------------------------
# HILFSFUNKTION: NEUES SPIEL FORMULAR (GEMÄSS SCREENSHOT)
# ------------------------------------------------------------------------------
def render_add_game_form():
    with st.expander("➕ Neues Spiel vorschlagen / anlegen"):
        player_list = list(db["players"].keys())
        creator = st.selectbox("Dein Name (Ersteller):", ["-- Bitte wählen --"] + player_list)
        
        c1, c2 = st.columns(2)
        g_name = c1.text_input("Spielname eingeben:", placeholder="z.B. Valheim")
        g_cover = c2.text_input("Cover Bild-URL (optional):", placeholder="Leer für Steam / Bild-Link")
        
        c3, c4 = st.columns(2)
        g_note = c3.text_input("Notiz / Kommentar (z.B. 6 Player Mod):")
        g_link = c4.text_input("Website / Store Link (optional):", placeholder="https://...")
        
        g_reason = st.text_area("Begründung / Meinung (Warum sollte es hinzugefügt werden?):", placeholder="Erhöht den Spaß, hat super Koop-Modus...")
        
        if st.button("Vorschlag einreichen"):
            if creator == "-- Bitte wählen --":
                st.error("Bitte wähle deinen Namen als Ersteller aus.")
            elif not g_name:
                st.error("Bitte gib einen Spielnamen ein.")
            else:
                new_id = str(len(db.get("games", {})) + 1)
                db.setdefault("games", {})[new_id] = {
                    "name": g_name,
                    "creator": creator,
                    "custom_cover": g_cover,
                    "steam_appid": "",
                    "note": g_note,
                    "link": g_link,
                    "reason": g_reason
                }
                db.setdefault("koth", {})[new_id] = {"king": None, "streak": 0, "history": []}
                add_audit_log(db, f"Spiel '{g_name}' hinzugefügt von {creator}", user=creator)
                update_db()
                st.success(f"Spiel '{g_name}' wurde erfolgreich hinzugefügt!")
                st.rerun()

# ------------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# ------------------------------------------------------------------------------
st.sidebar.title("⚔️ COMPETUS MAXIMUS")
st.sidebar.caption(f"Deutschland (Berlin) | {get_now_str()}")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "NAVIGATION",
    ["👑 King of the Hill", "🎯 Challenges", "🌿 Double Elimination Bracket", "📩 Einspruch & Anträge", "⚙️ Admin-Bereich"]
)

# ------------------------------------------------------------------------------
# 4. KING OF THE HILL
# ------------------------------------------------------------------------------
if page == "👑 King of the Hill":
    st.title("👑 KING OF THE HILL")
    
    render_add_game_form()
    
    games = db.get("games", {})
    if not games:
        st.info("Noch keine Spiele vorhanden. Benutze das Formular oben oder den Admin-Bereich, um das erste Spiel anzulegen.")
    else:
        st.subheader("🔥 Aktuelle Könige Übersicht")
        cols = st.columns(min(len(games), 4))
        for idx, (g_id, g_info) in enumerate(games.items()):
            k_data = db["koth"].get(g_id, {"king": None, "streak": 0})
            cover = get_steam_cover(g_info.get("steam_appid"), g_info.get("custom_cover"))
            
            with cols[idx % len(cols)]:
                with st.container(border=True):
                    st.image(cover, use_container_width=True)
                    st.markdown(f"### {g_info['name']}")
                    st.write(f"👑 King: **{k_data['king'] or 'Niemand'}**")
                    st.write(f"🔥 Streak: **{k_data['streak']} Siege**")
        
        st.markdown("---")
        
        selected_g_id = st.selectbox("Wähle ein Spiel", list(games.keys()), format_func=lambda x: games[x]["name"])
        g_info = games[selected_g_id]
        k_data = db["koth"].setdefault(selected_g_id, {"king": None, "streak": 0, "history": []})
        
        col_img, col_detail = st.columns([1, 2])
        with col_img:
            st.image(get_steam_cover(g_info.get("steam_appid"), g_info.get("custom_cover")), use_container_width=True)
        with col_detail:
            st.markdown(f"## {g_info['name']}")
            st.write(f"Erstellt von: `{g_info.get('creator', 'Admin')}`")
            if g_info.get('note'): st.write(f"Notiz: *{g_info['note']}*")
            if g_info.get('link'): st.markdown(f"[Store / Website Link]({g_info['link']})")
            st.write(f"Aktueller King: **{k_data['king'] or 'Thron unbesetzt'}** (Streak: **{k_data['streak']}**) ")

        st.markdown("### ⚔️ King herausfordern")
        player_list = list(db["players"].keys())
        
        if len(player_list) < 2:
            st.warning("Mindestens 2 registrierte Spieler erforderlich.")
        else:
            with st.form(f"koth_challenge_form_{selected_g_id}", clear_on_submit=True):
                c1, c2 = st.columns(2)
                current_king = k_data['king']
                
                if current_king:
                    defender = current_king
                    c1.text_input("King (Verteidiger)", value=defender, disabled=True)
                    challenger = c2.selectbox("Herausforderer", [p for p in player_list if p != defender])
                else:
                    defender = c1.selectbox("Spieler 1 (Anwärter)", player_list)
                    challenger = c2.selectbox("Spieler 2 (Anwärter)", [p for p in player_list if p != defender])
                
                format_choice = st.selectbox("Format", ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"])
                winner = st.selectbox("Sieger", [defender, challenger])
                comment = st.text_input("Match-Kommentar")
                
                if st.form_submit_button("Ergebnis eintragen"):
                    if winner == k_data["king"]:
                        k_data["streak"] += 1
                    else:
                        k_data["king"] = winner
                        k_data["streak"] = 1
                    
                    k_data.setdefault("history", []).append({
                        "timestamp": get_now_str(),
                        "defender": defender,
                        "challenger": challenger,
                        "winner": winner,
                        "format": format_choice,
                        "comment": comment
                    })
                    add_audit_log(db, f"KotH ({g_info['name']}): {winner} gewann gegen {defender if winner == challenger else challenger}", user=winner)
                    update_db()
                    st.success(f"Match gespeichert! Neuer King: {k_data['king']}")
                    st.rerun()

        st.markdown("---")
        st.subheader("📜 Match-Historie")
        for entry in reversed(k_data.get("history", [])):
            with st.container(border=True):
                st.write(f"🏆 **Sieger: {entry['winner']}** ({entry['format']}) | {entry['timestamp']}")
                st.caption(f"{entry['defender']} vs {entry['challenger']}")
                if entry.get("comment"): st.info(f"Kommentar: {entry['comment']}")

# ------------------------------------------------------------------------------
# 5. NEUE SEKTION: CHALLENGES
# ------------------------------------------------------------------------------
elif page == "🎯 Challenges":
    st.title("🎯 CHALLENGES & HERAUSFORDERUNGEN")
    
    tab1, tab2 = st.tabs(["🔥 Aktive Challenges", "➕ Challenge Generieren"])
    
    games = db.get("games", {})
    player_list = list(db["players"].keys())
    
    with tab2:
        st.subheader("Neue Spiel-Challenge erstellen")
        if not games:
            st.error("Lege zuerst mindestens ein Spiel an!")
        elif not player_list:
            st.error("Lege zuerst Spieler im Admin-Bereich an!")
        else:
            with st.form("create_challenge_form", clear_on_submit=True):
                creator = st.selectbox("Ersteller", player_list)
                game_id = st.selectbox("Spiel wählen", list(games.keys()), format_func=lambda x: games[x]["name"])
                c_title = st.text_input("Challenge Titel", placeholder="z.B. Speedrun unter 10 Minuten / No Hit Boss")
                c_desc = st.text_area("Detaillierte Beschreibung / Regeln", placeholder="Erkläre exakt, was getan werden muss...")
                c_difficulty = st.select_slider("Schwierigkeitsgrad", options=["Leicht", "Mittel", "Schwer", "Extrem", "Unmöglich"])
                
                if st.form_submit_button("Challenge Veröffentlichen"):
                    if c_title and c_desc:
                        new_c = {
                            "id": len(db.get("challenges", [])) + 1,
                            "creator": creator,
                            "game_id": game_id,
                            "title": c_title,
                            "description": c_desc,
                            "difficulty": c_difficulty,
                            "timestamp": get_now_str(),
                            "completions": []
                        }
                        db.setdefault("challenges", []).append(new_c)
                        add_audit_log(db, f"Challenge '{c_title}' von {creator} erstellt.", user=creator)
                        update_db()
                        st.success("Challenge erstellt!")
                        st.rerun()

    with tab1:
        st.subheader("Übersicht aller Challenges")
        challenges = db.get("challenges", [])
        if not challenges:
            st.info("Noch keine Challenges vorhanden.")
        else:
            for c in reversed(challenges):
                g_info = games.get(c["game_id"], {"name": "Unbekannt", "steam_appid": "", "custom_cover": ""})
                cover = get_steam_cover(g_info.get("steam_appid"), g_info.get("custom_cover"))
                
                with st.container(border=True):
                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        st.image(cover, use_container_width=True)
                    with col_info:
                        st.markdown(f"### {c['title']} (`{g_info['name']}`)")
                        st.caption(f"Erstellt von: **{c['creator']}** | Schwierigkeit: **{c['difficulty']}** | Am: {c['timestamp']}")
                        st.write(c["description"])
                    
                    st.markdown("#### 🌟 Absolvierte Versuche / Success-List")
                    completions = c.get("completions", [])
                    if completions:
                        for comp in completions:
                            st.write(f"✅ **{comp['player']}** | Rating: **{comp['rating']} ⭐** | Kommentar: *\"{comp['comment']}\"* ({comp['timestamp']})")
                    else:
                        st.caption("Noch niemand hat diese Challenge als absolviert eingetragen.")
                    
                    # Formular zum Absolvieren
                    with st.expander(f"Eintragen: Challenge geschafft!"):
                        if not player_list:
                            st.warning("Keine Spieler registriert.")
                        else:
                            with st.form(f"complete_c_{c['id']}", clear_on_submit=True):
                                p_name = st.selectbox("Dein Name", player_list, key=f"c_p_{c['id']}")
                                rating = st.slider("Wie bewertest du diese Challenge? (1-5 Stars)", 1, 5, 5, key=f"c_r_{c['id']}")
                                comment = st.text_input("Beweis-Link / Kommentar", placeholder="Link zum Video/Screenshot...", key=f"c_c_{c['id']}")
                                
                                if st.form_submit_button("Als Geschafft Markieren"):
                                    c.setdefault("completions", []).append({
                                        "player": p_name,
                                        "rating": rating,
                                        "comment": comment,
                                        "timestamp": get_now_str()
                                    })
                                    add_audit_log(db, f"Challenge #{c['id']} von {p_name} absolviert.", user=p_name)
                                    update_db()
                                    st.success("Erfolg eingetragen!")
                                    st.rerun()

# ------------------------------------------------------------------------------
# 6. DOUBLE ELIMINATION BRACKET (DYNAMISCH MIT FREILOS / BYE FIX)
# ------------------------------------------------------------------------------
elif page == "🌿 Double Elimination Bracket":
    st.title("🌿 DOUBLE ELIMINATION BRACKET")
    
    status = db["config"].get("bracket_tournament_status", "OPEN")
    if status == "OPEN":
        st.markdown('<div class="status-open">🟢 TURNIER GEÖFFNET</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-closed">🔴 TURNIER GESPERRT</div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    brackets = db.get("brackets_de", [])
    if not brackets:
        st.info("Keine Brackets aktiv. Erstelle ein Turnier im Admin-Bereich.")
    else:
        b_names = [f"{b['name']} ({b.get('game_name', 'General')})" for b in brackets]
        sel_b = st.selectbox("Bracket auswählen", range(len(brackets)), format_func=lambda x: b_names[x])
        bracket = brackets[sel_b]
        
        st.subheader(f"Turnier: {bracket['name']}")
        
        rounds = bracket.get("rounds", [])
        if not rounds:
            st.warning("Turnierbaum noch nicht initialisiert.")
        else:
            col_w, col_l = st.columns(2)
            
            with col_w:
                st.markdown("### ⚔️ WINNERS BRACKET")
                for r_idx, r in enumerate(rounds):
                    st.markdown(f"#### Runde {r_idx + 1}")
                    for m_idx, m in enumerate(r["winners"]):
                        with st.container(border=True):
                            p1, p2 = m["p1"], m["p2"]
                            w = m.get("winner")
                            st.write(f"**Match #{m['id']}**")
                            st.write(f"🟢 {p1}" if w == p1 else p1)
                            st.write(f"🟢 {p2}" if w == p2 else p2)
                            
                            if not w and p1 != "TBD" and p2 != "TBD" and status == "OPEN":
                                win_choice = st.selectbox("Sieger", [p1, p2], key=f"w_sel_{bracket['id']}_{r_idx}_{m_idx}")
                                if st.button("Ergebnis Speichern", key=f"w_btn_{bracket['id']}_{r_idx}_{m_idx}"):
                                    m["winner"] = win_choice
                                    loser = p2 if win_choice == p1 else p1
                                    
                                    # Gewinner rückt in nächste Winners-Runde vor
                                    if r_idx + 1 < len(rounds):
                                        next_m = rounds[r_idx + 1]["winners"][m_idx // 2]
                                        if m_idx % 2 == 0:
                                            next_m["p1"] = win_choice
                                        else:
                                            next_m["p2"] = win_choice
                                    
                                    # Verlierer ins Losers Bracket verschieben
                                    if loser != "BYE":
                                        l_target = rounds[r_idx]["losers"]
                                        for lm in l_target:
                                            if lm["p1"] == "TBD":
                                                lm["p1"] = loser
                                                break
                                            elif lm["p2"] == "TBD":
                                                lm["p2"] = loser
                                                break
                                                
                                    add_audit_log(db, f"Bracket '{bracket['name']}': {win_choice} schlägt {loser}")
                                    update_db()
                                    st.rerun()

            with col_l:
                st.markdown("### 💀 LOSERS BRACKET")
                for r_idx, r in enumerate(rounds):
                    st.markdown(f"#### Loser Runde {r_idx + 1}")
                    for m_idx, m in enumerate(r["losers"]):
                        with st.container(border=True):
                            p1, p2 = m["p1"], m["p2"]
                            w = m.get("winner")
                            st.write(f"**Loser Match #{m['id']}**")
                            st.write(f"🟢 {p1}" if w == p1 else p1)
                            st.write(f"🟢 {p2}" if w == p2 else p2)
                            
                            if not w and p1 not in ["TBD", "BYE"] and p2 not in ["TBD", "BYE"] and status == "OPEN":
                                win_choice = st.selectbox("Sieger", [p1, p2], key=f"l_sel_{bracket['id']}_{r_idx}_{m_idx}")
                                if st.button("Ergebnis Speichern", key=f"l_btn_{bracket['id']}_{r_idx}_{m_idx}"):
                                    m["winner"] = win_choice
                                    add_audit_log(db, f"Loser Match '{bracket['name']}': {win_choice} gewinnt")
                                    update_db()
                                    st.rerun()

# ------------------------------------------------------------------------------
# 7. EINSPRUCH & ANTRÄGE
# ------------------------------------------------------------------------------
elif page == "📩 Einspruch & Anträge":
    st.title("📩 ANTRÄGE & EINSPRÜCHE")
    
    with st.form("appeal_form", clear_on_submit=True):
        st.subheader("Einspruch oder Antrag einreichen")
        player_list = list(db["players"].keys())
        sender = st.selectbox("Antragsteller", player_list if player_list else ["-"])
        target = st.selectbox("Betroffener Spieler / Match", player_list if player_list else ["-"])
        reason = st.text_area("Begründung / Vorfall schildern")
        
        if st.form_submit_button("Antrag einreichen"):
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
                add_audit_log(db, f"Einspruch #{new_appeal['id']} von {sender} eingereicht", user=sender)
                update_db()
                st.success("Antrag eingereicht.")
                st.rerun()

    st.markdown("---")
    st.subheader("📜 Laufende Anträge")
    for app in db["appeals"]:
        with st.container(border=True):
            st.write(f"**Antrag #{app['id']}** | Status: `{app['status']}` | Datum: {app['timestamp']}")
            st.write(f"Von: **{app['sender']}** | Gegen: **{app['target']}**")
            st.write(f"Begründung: *{app['reason']}*")
            if app.get("defense"): st.write(f"Stellungnahme: *{app['defense']}*")
            
            if app["status"] == "OFFEN":
                with st.expander("Stellungnahme abgeben"):
                    def_t = st.text_input("Gegen-Aussage", key=f"def_{app['id']}")
                    if st.button("Speichern", key=f"btn_def_{app['id']}"):
                        app["defense"] = def_t
                        update_db()
                        st.rerun()

# ------------------------------------------------------------------------------
# 8. ADMIN-BEREICH (PASSWORT: zm1234)
# ------------------------------------------------------------------------------
elif page == "⚙️ Admin-Bereich":
    st.title("⚙️ ADMIN CONTROL PANEL")
    
    # PASSWORT STRIKT GEÄNDERT AUF: zm1234
    admin_pw = st.secrets.get("ADMIN_PASSWORD", "zm1234")
    input_pw = st.text_input("Admin-Passwort eingeben", type="password")
    
    if input_pw != admin_pw:
        st.error("Zugriff verweigert. Bitte gültiges Admin-Passwort eingeben.")
    else:
        st.success("Authentifizierung erfolgreich.")
        
        tab_admin = st.tabs([
            "🎮 Spiele", 
            "👥 Spieler", 
            "🌿 Bracket Generator", 
            "👑 KotH Overrides", 
            "🔒 Status", 
            "📩 Einsprüche", 
            "📊 Audit Logs", 
            "💾 Backup"
        ])
        
        # TAB 1: Spiele Verwaltung
        with tab_admin[0]:
            st.subheader("Spiele verwalten")
            render_add_game_form()
            
            st.markdown("---")
            games = db.get("games", {})
            for g_id, g in list(games.items()):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**ID {g_id}: {g['name']}** (Ersteller: {g.get('creator', 'Admin')})")
                if c2.button(f"Löschen #{g_id}", key=f"del_g_{g_id}"):
                    del games[g_id]
                    if g_id in db["koth"]: del db["koth"][g_id]
                    update_db()
                    st.rerun()

        # TAB 2: Spieler-Verwaltung
        with tab_admin[1]:
            st.subheader("Spieler hinzufügen / löschen")
            c1, c2 = st.columns(2)
            new_p = c1.text_input("Neuer Spieler Name")
            if c1.button("Spieler Anlegen") and new_p:
                if new_p not in db["players"]:
                    db["players"][new_p] = {"created_at": get_now_str()}
                    add_audit_log(db, f"Spieler angelegt: {new_p}", user="Admin")
                    update_db()
                    st.rerun()
            
            del_p = c2.selectbox("Spieler entfernen", ["-"] + list(db["players"].keys()))
            if c2.button("Spieler Löschen") and del_p != "-":
                del db["players"][del_p]
                add_audit_log(db, f"Spieler gelöscht: {del_p}", user="Admin")
                update_db()
                st.rerun()

        # TAB 3: Double Elimination Bracket Generator (FIXED FÜR UNGERADE ANZAHL & AUTOMATIK)
        with tab_admin[2]:
            st.subheader("🌿 Double Elimination Bracket Generator")
            p_list = list(db["players"].keys())
            
            if len(p_list) < 2:
                st.warning("Mindestens 2 Spieler erforderlich.")
            else:
                b_name = st.text_input("Turnier Name", value="Turnier 1")
                b_game = st.selectbox("Spiel zuordnen", [g["name"] for g in db.get("games", {}).values()] if db.get("games") else ["Allgemein"])
                sel_players = st.multiselect("Teilnehmer wählen", p_list, default=p_list)
                
                if st.button("DOUBLE ELIMINATION BRACKET ERSTELLEN"):
                    num_players = len(sel_players)
                    # Nächste 2er-Potenz ermitteln (für ausgeglichene Brackets)
                    next_power = 2 ** math.ceil(math.log2(num_players))
                    byes_needed = next_power - num_players
                    
                    padded_players = sel_players + ["BYE"] * byes_needed
                    num_rounds = int(math.log2(next_power))
                    
                    rounds_data = []
                    
                    # Runde 1 aufbauen
                    r1_winners = []
                    r1_losers = []
                    
                    match_id_counter = 1
                    for i in range(0, len(padded_players), 2):
                        p1 = padded_players[i]
                        p2 = padded_players[i+1]
                        
                        # Freilos Automatik
                        auto_winner = None
                        if p2 == "BYE": auto_winner = p1
                        elif p1 == "BYE": auto_winner = p2
                        
                        r1_winners.append({
                            "id": match_id_counter,
                            "p1": p1,
                            "p2": p2,
                            "winner": auto_winner
                        })
                        
                        r1_losers.append({
                            "id": match_id_counter,
                            "p1": "TBD",
                            "p2": "TBD",
                            "winner": None
                        })
                        match_id_counter += 1
                        
                    rounds_data.append({"winners": r1_winners, "losers": r1_losers})
                    
                    # Folgerunden mit Platzhaltern generieren
                    curr_matches = len(r1_winners) // 2
                    for r in range(1, num_rounds):
                        r_win = []
                        r_los = []
                        for _ in range(curr_matches):
                            r_win.append({"id": match_id_counter, "p1": "TBD", "p2": "TBD", "winner": None})
                            r_los.append({"id": match_id_counter, "p1": "TBD", "p2": "TBD", "winner": None})
                            match_id_counter += 1
                        rounds_data.append({"winners": r_win, "losers": r_los})
                        curr_matches //= 2
                    
                    new_bracket = {
                        "id": len(db.get("brackets_de", [])) + 1,
                        "name": b_name,
                        "game_name": b_game,
                        "rounds": rounds_data
                    }
                    db.setdefault("brackets_de", []).append(new_bracket)
                    add_audit_log(db, f"DE Bracket '{b_name}' generiert ({num_players} Spieler, {byes_needed} Freilose).", user="Admin")
                    update_db()
                    st.success("Bracket erfolgreich und komplett automatisiert erstellt!")
                    st.rerun()

        # TAB 4: KotH Overrides
        with tab_admin[3]:
            st.subheader("👑 King of the Hill Override")
            games = db.get("games", {})
            if games:
                ov_g = st.selectbox("Spiel", list(games.keys()), format_func=lambda x: games[x]["name"], key="ov_g")
                k_data = db["koth"].setdefault(ov_g, {"king": None, "streak": 0, "history": []})
                
                c1, c2 = st.columns(2)
                new_king = c1.selectbox("König", ["NIEMAND"] + list(db["players"].keys()))
                new_streak = c2.number_input("Streak", min_value=0, value=k_data.get("streak", 0))
                
                if st.button("Überschreiben"):
                    k_data["king"] = None if new_king == "NIEMAND" else new_king
                    k_data["streak"] = new_streak
                    add_audit_log(db, f"KotH Override ({games[ov_g]['name']}): {new_king} ({new_streak})", user="Admin")
                    update_db()
                    st.success("KotH geändert!")
                    st.rerun()

        # TAB 5: Status Control
        with tab_admin[4]:
            st.subheader("🔒 Bracket Status")
            c1, c2 = st.columns(2)
            if c1.button("🟢 ÖFFNEN"):
                db["config"]["bracket_tournament_status"] = "OPEN"
                update_db()
                st.rerun()
            if c2.button("🔴 SPERREN"):
                db["config"]["bracket_tournament_status"] = "CLOSED"
                update_db()
                st.rerun()

        # TAB 6: Einsprüche
        with tab_admin[5]:
            st.subheader("📩 Einsprüche bearbeiten")
            for app in db["appeals"]:
                st.write(f"#{app['id']} von {app['sender']} gegen {app['target']}")
                c1, c2 = st.columns(2)
                if c1.button("Klären", key=f"acc_{app['id']}"):
                    app["status"] = "GEKLÄRT"
                    update_db()
                    st.rerun()
                if c2.button("Ablehnen", key=f"rej_{app['id']}"):
                    app["status"] = "ABGELEHNT"
                    update_db()
                    st.rerun()

        # TAB 7: Logs
        with tab_admin[6]:
            st.subheader("📊 Audit Logs")
            st.dataframe(db["audit_logs"], use_container_width=True)

        # TAB 8: Backup
        with tab_admin[7]:
            st.subheader("💾 Backup & Restore")
            st.download_button("data.json herunterladen", data=json.dumps(db, indent=2, ensure_ascii=False), file_name="data_backup.json")
            up_file = st.file_uploader("Backup hochladen", type=["json"])
            if up_file:
                db_up = json.load(up_file)
                st.session_state.db = db_up
                save_data(db_up)
                st.success("Backup wiederhergestellt!")
                st.rerun()
