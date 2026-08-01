import streamlit as st
import json
import os
import requests
import base64
import re
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
    
    /* Difficulty Badges */
    .diff-leicht { background-color: #10b981; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .diff-mittel { background-color: #f59e0b; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .diff-schwer { background-color: #f97316; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .diff-extrem { background-color: #ef4444; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    .diff-unmoeglich { background-color: #a855f7; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; box-shadow: 0 0 8px #a855f7; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. PERSISTENZ & SMART STEAM AUTO-FETCH ENGINE
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
        "games": {},           # KotH Spiele
        "challenge_games": {}, # Separate Spiele-Datenbank für Challenges
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
            data = json.load(f)
            data.setdefault("challenge_games", {})
            return data
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

def fetch_steam_info(game_name, custom_cover=""):
    """
    Sucht automatisch auf Steam nach dem Spielnamen, um Banner & Store-Link zu ziehen.
    Unterstützt Custom Overrides.
    """
    if custom_cover and custom_cover.strip():
        return custom_cover.strip(), ""

    if not game_name:
        return "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER", ""

    # Check ob der Name selbst eine URL/AppID ist
    appid_match = re.search(r'/app/(\d+)', str(game_name))
    if appid_match:
        appid = appid_match.group(1)
        return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg", f"https://store.steampowered.com/app/{appid}/"
    elif str(game_name).isdigit():
        appid = str(game_name)
        return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg", f"https://store.steampowered.com/app/{appid}/"

    # Auto-Search via Steam Store Search API
    try:
        url = f"https://store.steampowered.com/api/storesearch/?term={requests.utils.quote(game_name)}&l=german&cc=DE"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                appid = items[0]["id"]
                return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg", f"https://store.steampowered.com/app/{appid}/"
    except Exception:
        pass

    return "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER", ""

if "db" not in st.session_state:
    st.session_state.db = load_data()

def update_db():
    save_data(st.session_state.db)

db = st.session_state.db

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
# 4. KING OF THE HILL (TAB-TRENNUNG & AUTO STEAM FETCH)
# ------------------------------------------------------------------------------
if page == "👑 King of the Hill":
    st.title("👑 KING OF THE HILL")
    
    tab_koth_active, tab_koth_create = st.tabs(["🔥 Aktive Kings", "➕ Neues KotH-Spiel & Thron gründen"])
    
    games = db.get("games", {})
    player_list = list(db["players"].keys())

    # TAB 2: SPIEL ANLEGEN & KÖNIG WERDEN
    with tab_koth_create:
        st.subheader("➕ Neues KotH-Spiel erstellen & Thron beanspruchen")
        if not player_list:
            st.warning("Bitte erstelle zuerst mindestens einen Spieler im Admin-Bereich!")
        else:
            with st.form("koth_create_game_form", clear_on_submit=True):
                creator = st.selectbox("Dein Name (Ersteller / Erster König):", player_list)
                g_name = st.text_input("Spielname eingeben:", placeholder="z.B. Valheim, CS2, Rocket League")
                
                c1, c2 = st.columns(2)
                match_format = c1.selectbox("Wettkampf-Format", ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"])
                custom_cover = c2.text_input("Custom Cover Bild-URL (optional - überschreibt Auto-Steam):", placeholder="https://...")
                
                rules_comment = st.text_area("Herausforderungs-Regeln / Modus / Waffen & Maps:", 
                                             placeholder="z.B. Nur 1v1 AWP auf Aim_Map, Ohne Rüstung, Hardcore Modus...")
                
                if st.form_submit_button("Werde König"):
                    if not g_name:
                        st.error("Bitte gib einen Spielnamen ein!")
                    else:
                        # Auto-Fetch Banner & Link via Steam Engine
                        cover_url, store_link = fetch_steam_info(g_name, custom_cover)
                        
                        new_id = str(len(games) + 1)
                        games[new_id] = {
                            "name": g_name,
                            "creator": creator,
                            "custom_cover": cover_url,
                            "link": store_link,
                            "format": match_format,
                            "rules": rules_comment
                        }
                        
                        # Thron direkt mit Streak 1 gründen
                        db.setdefault("koth", {})[new_id] = {
                            "king": creator, 
                            "streak": 1, 
                            "history": [{
                                "timestamp": get_now_str(),
                                "defender": creator,
                                "challenger": "Thron-Gründung",
                                "winner": creator,
                                "format": match_format
                            }]
                        }
                        add_audit_log(db, f"KotH Spiel '{g_name}' angelegt von {creator}. King: {creator}", user=creator)
                        update_db()
                        st.success(f"KotH Arena für '{g_name}' eröffnet! Du bist der aktuelle King!")
                        st.rerun()

    # TAB 1: AKTIVE KINGS UND HERAUSFORDERUNGEN
    with tab_koth_active:
        if not games:
            st.info("Noch keine KotH-Spiele vorhanden. Wechsel in den Reiter 'Neues KotH-Spiel & Thron gründen', um das erste Spiel zu starten.")
        else:
            st.subheader("🔥 Aktuelle Könige Übersicht")
            cols = st.columns(min(len(games), 4))
            for idx, (g_id, g_info) in enumerate(games.items()):
                k_data = db["koth"].get(g_id, {"king": None, "streak": 0})
                cover = g_info.get("custom_cover") or "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER"
                
                with cols[idx % len(cols)]:
                    with st.container(border=True):
                        st.image(cover, use_container_width=True)
                        st.markdown(f"### {g_info['name']}")
                        st.write(f"👑 King: **{k_data['king'] or 'Niemand'}**")
                        st.write(f"🔥 Streak: **{k_data['streak']} Siege**")
            
            st.markdown("---")
            
            selected_g_id = st.selectbox("Wähle ein Spiel aus", list(games.keys()), format_func=lambda x: games[x]["name"])
            g_info = games[selected_g_id]
            k_data = db["koth"].setdefault(selected_g_id, {"king": None, "streak": 0, "history": []})
            
            col_img, col_detail = st.columns([1, 2])
            with col_img:
                st.image(g_info.get("custom_cover"), use_container_width=True)
            with col_detail:
                st.markdown(f"## {g_info['name']}")
                st.write(f"Gründer: `{g_info.get('creator', 'Admin')}` | Format: **{g_info.get('format', 'Bo3')}**")
                if g_info.get('link'): st.markdown(f"🔗 [Store / Steam Link öffnen]({g_info['link']})")
                if g_info.get('rules'): st.info(f"📜 **Regeln & Waffen/Maps:** {g_info['rules']}")
                st.write(f"Aktueller King: **{k_data['king'] or 'Thron unbesetzt'}** (Streak: **{k_data['streak']}**) ")

            st.markdown("### ⚔️ King herausfordern")
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
                    
                    winner = st.selectbox("Sieger des Matches", [defender, challenger])
                    
                    if st.form_submit_button("Match-Ergebnis Speichern"):
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
                            "format": g_info.get("format", "Bo3")
                        })
                        add_audit_log(db, f"KotH ({g_info['name']}): {winner} gewann gegen {defender if winner == challenger else challenger}", user=winner)
                        update_db()
                        st.success(f"Match gespeichert! Neuer King: {k_data['king']}")
                        st.rerun()

            st.markdown("---")
            st.subheader("📜 Match-Historie")
            for entry in reversed(k_data.get("history", [])):
                with st.container(border=True):
                    st.write(f"🏆 **Sieger: {entry['winner']}** ({entry.get('format', 'Bo3')}) | {entry['timestamp']}")
                    st.caption(f"Kampf: {entry['defender']} vs {entry['challenger']}")

# ------------------------------------------------------------------------------
# 5. CHALLENGES (KLARE SPIEL-SELEKTION & AUTO STEAM FETCH)
# ------------------------------------------------------------------------------
elif page == "🎯 Challenges":
    st.title("🎯 CHALLENGES & HERAUSFORDERUNGEN")
    
    tab1, tab2 = st.tabs(["🔥 Aktive Challenges", "➕ Challenge Erstellen"])
    
    challenge_games = db.setdefault("challenge_games", {})
    player_list = list(db["players"].keys())
    
    with tab2:
        st.subheader("Neues Challenge-Spiel registrieren oder bestehendes wählen")
        
        # Schritt 1: Spiel registrieren (falls es noch nicht existiert)
        with st.expander("➕ Ein neues Spiel zur Challenge-Datenbank hinzufügen"):
            cg_name = st.text_input("Spielname eingeben", placeholder="z.B. Elden Ring, Hollow Knight")
            cg_cover_custom = st.text_input("Custom Cover Bild-URL (optional - sonst Auto-Steam):", placeholder="https://...")
            
            if st.button("Spiel in Challenge-Datenbank Speichern"):
                if cg_name:
                    cover_url, _ = fetch_steam_info(cg_name, cg_cover_custom)
                    new_cg_id = str(len(challenge_games) + 1)
                    challenge_games[new_cg_id] = {
                        "name": cg_name,
                        "cover": cover_url
                    }
                    update_db()
                    st.success(f"Spiel '{cg_name}' wurde für Challenges hinzugefügt!")
                    st.rerun()

        st.markdown("---")
        # Schritt 2: Challenge erstellen für ein gewähltes Spiel
        st.subheader("Challenge für ein existierendes Spiel erstellen")
        if not challenge_games:
            st.info("Es ist noch kein Challenge-Spiel angelegt. Bitte erstelle oben das erste Spiel!")
        elif not player_list:
            st.error("Lege zuerst Spieler im Admin-Bereich an!")
        else:
            with st.form("create_challenge_form", clear_on_submit=True):
                creator = st.selectbox("Ersteller", player_list)
                cg_id = st.selectbox("Wähle das Spiel für die Challenge", list(challenge_games.keys()), format_func=lambda x: challenge_games[x]["name"])
                
                c_title = st.text_input("Challenge Titel", placeholder="z.B. Speedrun unter 10 Minuten / No Hit Boss")
                c_desc = st.text_area("Detaillierte Beschreibung / Regeln", placeholder="Erkläre exakt, was getan werden muss...")
                c_difficulty = st.select_slider("Schwierigkeitsgrad", options=["Leicht", "Mittel", "Schwer", "Extrem", "Unmöglich"])
                
                if st.form_submit_button("Challenge Veröffentlichen"):
                    if c_title and c_desc:
                        new_c = {
                            "id": len(db.get("challenges", [])) + 1,
                            "creator": creator,
                            "challenge_game_id": cg_id,
                            "title": c_title,
                            "description": c_desc,
                            "difficulty": c_difficulty,
                            "timestamp": get_now_str(),
                            "completions": []
                        }
                        db.setdefault("challenges", []).append(new_c)
                        add_audit_log(db, f"Challenge '{c_title}' von {creator} erstellt.", user=creator)
                        update_db()
                        st.success("Challenge veröffentlicht!")
                        st.rerun()

    with tab1:
        st.subheader("Übersicht aller Challenges")
        challenges = db.get("challenges", [])
        if not challenges:
            st.info("Noch keine Challenges vorhanden.")
        else:
            diff_css_map = {
                "Leicht": "diff-leicht",
                "Mittel": "diff-mittel",
                "Schwer": "diff-schwer",
                "Extrem": "diff-extrem",
                "Unmöglich": "diff-unmoeglich"
            }
            
            for c in reversed(challenges):
                cg_info = challenge_games.get(c.get("challenge_game_id"), {"name": "Allgemein", "cover": "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER"})
                cover = cg_info.get("cover")
                diff_class = diff_css_map.get(c['difficulty'], 'diff-mittel')
                
                with st.container(border=True):
                    col_img, col_info = st.columns([1, 3])
                    with col_img:
                        st.image(cover, use_container_width=True)
                    with col_info:
                        st.markdown(f"### {c['title']} (`{cg_info['name']}`)")
                        st.markdown(f"Schwierigkeit: <span class='{diff_class}'>{c['difficulty']}</span> | Erstellt von: **{c['creator']}** | Am: {c['timestamp']}", unsafe_allow_html=True)
                        st.write(c["description"])
                    
                    st.markdown("#### 🌟 Absolvierte Versuche")
                    completions = c.get("completions", [])
                    if completions:
                        for comp in completions:
                            st.write(f"✅ **{comp['player']}** | Rating: **{comp['rating']} ⭐** | Kommentar: *\"{comp['comment']}\"* ({comp['timestamp']})")
                    else:
                        st.caption("Noch niemand hat diese Challenge geschafft.")
                    
                    with st.expander("Eintragen: Challenge geschafft!"):
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
# 6. DOUBLE ELIMINATION BRACKET
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
                                    
                                    if r_idx + 1 < len(rounds):
                                        next_m = rounds[r_idx + 1]["winners"][m_idx // 2]
                                        if m_idx % 2 == 0:
                                            next_m["p1"] = win_choice
                                        else:
                                            next_m["p2"] = win_choice
                                    
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
# 8. ADMIN-BEREICH
# ------------------------------------------------------------------------------
elif page == "⚙️ Admin-Bereich":
    st.title("⚙️ ADMIN CONTROL PANEL")
    
    admin_pw = st.secrets.get("ADMIN_PASSWORD", "zm1234")
    input_pw = st.text_input("Admin-Passwort eingeben", type="password")
    
    if input_pw != admin_pw:
        st.error("Zugriff verweigert. Bitte gültiges Admin-Passwort eingeben.")
    else:
        st.success("Authentifizierung erfolgreich.")
        
        tab_admin = st.tabs([
            "🎮 KotH Spiele", 
            "🎯 Challenges",
            "👥 Spieler", 
            "🌿 Brackets", 
            "👑 KotH Overrides", 
            "🔒 Status", 
            "📩 Einsprüche", 
            "📊 Audit Logs", 
            "💾 Backup"
        ])
        
        # TAB 1: KotH Spiele
        with tab_admin[0]:
            st.subheader("👑 KotH Spiele & Match-Historie Löschen")
            games = db.get("games", {})
            if not games:
                st.info("Keine KotH-Spiele vorhanden.")
            else:
                for g_id, g in list(games.items()):
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"### ID {g_id}: {g['name']}")
                        c1.write(f"Ersteller: **{g.get('creator', 'Admin')}** | Format: **{g.get('format', 'Bo3')}**")
                        
                        if c2.button(f"🗑️ Spiel komplett löschen", key=f"del_g_{g_id}"):
                            del games[g_id]
                            if g_id in db.get("koth", {}): 
                                del db["koth"][g_id]
                            add_audit_log(db, f"KotH Spiel '{g['name']}' gelöscht", user="Admin")
                            update_db()
                            st.rerun()
                        
                        k_hist = db.get("koth", {}).get(g_id, {}).get("history", [])
                        if k_hist:
                            with st.expander(f"Einzelne Matches von '{g['name']}' löschen ({len(k_hist)} Matches)"):
                                for h_idx, h in enumerate(reversed(k_hist)):
                                    real_idx = len(k_hist) - 1 - h_idx
                                    col_m, col_btn = st.columns([4, 1])
                                    col_m.write(f"Match #{real_idx+1}: **{h['winner']}** gewann ({h['timestamp']})")
                                    if col_btn.button("Match Löschen", key=f"del_km_{g_id}_{real_idx}"):
                                        k_hist.pop(real_idx)
                                        add_audit_log(db, f"KotH Match #{real_idx+1} in {g['name']} gelöscht.", user="Admin")
                                        update_db()
                                        st.rerun()

        # TAB 2: Challenges
        with tab_admin[1]:
            st.subheader("🎯 Challenges & Challenge-Spiele Verwalten / Löschen")
            
            st.markdown("#### 1. Einzelne Challenges löschen")
            challenges = db.get("challenges", [])
            if not challenges:
                st.write("Keine aktiven Challenges vorhanden.")
            else:
                for c_idx, c in enumerate(list(challenges)):
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"**Challenge #{c['id']}: {c['title']}** (Schwierigkeit: {c['difficulty']})")
                        c1.caption(f"Erstellt von {c['creator']} am {c['timestamp']}")
                        
                        if c2.button("🗑️ Challenge Löschen", key=f"del_c_{c['id']}"):
                            challenges.pop(c_idx)
                            add_audit_log(db, f"Challenge #{c['id']} ({c['title']}) gelöscht", user="Admin")
                            update_db()
                            st.rerun()
            
            st.markdown("---")
            st.markdown("#### 2. Challenge-Spiele löschen")
            c_games = db.get("challenge_games", {})
            if not c_games:
                st.write("Keine Challenge-Spiele vorhanden.")
            else:
                for cg_id, cg in list(c_games.items()):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**ID {cg_id}: {cg['name']}**")
                    if c2.button(f"🗑️ Challenge-Spiel Löschen", key=f"del_cg_{cg_id}"):
                        del c_games[cg_id]
                        add_audit_log(db, f"Challenge-Spiel '{cg['name']}' gelöscht", user="Admin")
                        update_db()
                        st.rerun()

        # TAB 3: Spieler
        with tab_admin[2]:
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

        # TAB 4: Brackets
        with tab_admin[3]:
            st.subheader("🌿 Double Elimination Bracket Generator & Löschen")
            
            brackets = db.get("brackets_de", [])
            if brackets:
                st.markdown("#### Aktive Brackets löschen")
                for b_idx, b in enumerate(list(brackets)):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**Bracket #{b['id']}: {b['name']}** ({b.get('game_name', 'General')})")
                    if c2.button("🗑️ Bracket Löschen", key=f"del_b_{b['id']}"):
                        brackets.pop(b_idx)
                        add_audit_log(db, f"Bracket '{b['name']}' gelöscht", user="Admin")
                        update_db()
                        st.rerun()
                st.markdown("---")

            st.markdown("#### Neues Bracket Erstellen")
            p_list = list(db["players"].keys())
            
            if len(p_list) < 2:
                st.warning("Mindestens 2 Spieler erforderlich.")
            else:
                b_name = st.text_input("Turnier Name", value="Turnier 1")
                b_game = st.selectbox("Spiel zuordnen", [g["name"] for g in db.get("games", {}).values()] if db.get("games") else ["Allgemein"])
                sel_players = st.multiselect("Teilnehmer wählen", p_list, default=p_list)
                
                if st.button("DOUBLE ELIMINATION BRACKET ERSTELLEN"):
                    num_players = len(sel_players)
                    next_power = 2 ** math.ceil(math.log2(num_players))
                    byes_needed = next_power - num_players
                    
                    padded_players = sel_players + ["BYE"] * byes_needed
                    num_rounds = int(math.log2(next_power))
                    
                    rounds_data = []
                    r1_winners = []
                    r1_losers = []
                    
                    match_id_counter = 1
                    for i in range(0, len(padded_players), 2):
                        p1 = padded_players[i]
                        p2 = padded_players[i+1]
                        
                        auto_winner = None
                        if p2 == "BYE": auto_winner = p1
                        elif p1 == "BYE": auto_winner = p2
                        
                        r1_winners.append({"id": match_id_counter, "p1": p1, "p2": p2, "winner": auto_winner})
                        r1_losers.append({"id": match_id_counter, "p1": "TBD", "p2": "TBD", "winner": None})
                        match_id_counter += 1
                        
                    rounds_data.append({"winners": r1_winners, "losers": r1_losers})
                    
                    curr_matches = len(r1_winners) // 2
                    for r in range(1, num_rounds):
                        r_win, r_los = [], []
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
                    add_audit_log(db, f"DE Bracket '{b_name}' generiert.", user="Admin")
                    update_db()
                    st.success("Bracket erfolgreich erstellt!")
                    st.rerun()

        # TAB 5: KotH Overrides
        with tab_admin[4]:
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

        # TAB 6: Status
        with tab_admin[5]:
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

        # TAB 7: Einsprüche
        with tab_admin[6]:
            st.subheader("📩 Einsprüche bearbeiten / löschen")
            for a_idx, app in enumerate(list(db["appeals"])):
                with st.container(border=True):
                    st.write(f"#{app['id']} von **{app['sender']}** gegen **{app['target']}**: {app['reason']}")
                    c1, c2, c3 = st.columns(3)
                    if c1.button("Klären", key=f"acc_{app['id']}"):
                        app["status"] = "GEKLÄRT"
                        update_db()
                        st.rerun()
                    if c2.button("Ablehnen", key=f"rej_{app['id']}"):
                        app["status"] = "ABGELEHNT"
                        update_db()
                        st.rerun()
                    if c3.button("🗑️ Löschen", key=f"del_app_{app['id']}"):
                        db["appeals"].pop(a_idx)
                        update_db()
                        st.rerun()

        # TAB 8: Logs
        with tab_admin[7]:
            st.subheader("📊 Audit Logs")
            st.dataframe(db["audit_logs"], use_container_width=True)

        # TAB 9: Backup
        with tab_admin[8]:
            st.subheader("💾 Backup & Restore")
            st.download_button("data.json herunterladen", data=json.dumps(db, indent=2, ensure_ascii=False), file_name="data_backup.json")
            up_file = st.file_uploader("Backup hochladen", type=["json"])
            if up_file:
                db_up = json.load(up_file)
                st.session_state.db = db_up
                save_data(db_up)
                st.success("Backup wiederhergestellt!")
                st.rerun()
