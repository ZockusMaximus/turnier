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

    /* Highlights */
    .creator-box {
        background: rgba(0, 240, 255, 0.08);
        border: 1px solid #00f0ff;
        padding: 6px 12px;
        border-radius: 4px;
        color: #00f0ff;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 8px;
    }
    .king-highlight-box {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(180, 83, 9, 0.3) 100%);
        border: 2px solid #f59e0b;
        padding: 10px 15px;
        border-radius: 6px;
        color: #fbbf24;
        font-weight: bold;
        text-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. PERSISTENZ & STEAM API ENGINE
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
    if custom_cover and custom_cover.strip():
        return custom_cover.strip(), ""

    if not game_name:
        return "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER", ""

    appid_match = re.search(r'/app/(\d+)', str(game_name))
    if appid_match:
        appid = appid_match.group(1)
        return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg", f"https://store.steampowered.com/app/{appid}/"
    elif str(game_name).isdigit():
        appid = str(game_name)
        return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg", f"https://store.steampowered.com/app/{appid}/"

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
# 4. KING OF THE HILL (STATISTIKEN & KÖNIG HIGHLIGHT & FIXED CHALLENGE)
# ------------------------------------------------------------------------------
if page == "👑 King of the Hill":
    st.title("👑 KING OF THE HILL")
    
    tab_koth_active, tab_koth_create, tab_koth_stats = st.tabs(["🔥 Aktive Kings", "➕ Neues KotH-Spiel & Thron gründen", "📊 KotH Statistiken"])
    
    games = db.get("games", {})
    player_list = list(db["players"].keys())

    # TAB 2: NEUES SPIEL ANLEGEN
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
                custom_cover = c2.text_input("Custom Cover Bild-URL (optional):", placeholder="https://...")
                
                rules_comment = st.text_area("Herausforderungs-Regeln / Modus / Waffen & Maps:", 
                                             placeholder="z.B. Nur 1v1 AWP auf Aim_Map, Ohne Rüstung, Hardcore Modus...")
                
                if st.form_submit_button("Werde König"):
                    if not g_name:
                        st.error("Bitte gib einen Spielnamen ein!")
                    else:
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

    # TAB 1: AKTIVE KINGS
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
                        st.markdown(f"""
                        <div class="king-highlight-box">
                            👑 KING: <b>{k_data['king'] or 'Niemand'}</b><br>
                            🔥 Streak: <b>{k_data['streak']} Siege</b>
                        </div>
                        """, unsafe_allow_html=True)
            
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
                
                st.markdown(f"""
                <div class="king-highlight-box" style="font-size: 1.2em;">
                    👑 AKTUELLER KÖNIG: <b>{k_data['king'] or 'Thron unbesetzt'}</b> (Streak: <b>{k_data['streak']} Siege</b>)
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### ⚔️ King herausfordern")
            if len(player_list) < 2:
                st.warning("Mindestens 2 registrierte Spieler erforderlich.")
            else:
                current_king = k_data['king']
                
                # Herausforderer-Auswahl AUSSERHALB des Formulars, damit das Sieger-Dropdown dynamisch aktualisiert wird!
                c1, c2 = st.columns(2)
                if current_king:
                    defender = current_king
                    c1.text_input("King (Verteidiger)", value=defender, disabled=True)
                    available_challengers = [p for p in player_list if p != defender]
                    challenger = c2.selectbox("Herausforderer wählen", available_challengers, key=f"challenger_select_{selected_g_id}")
                else:
                    defender = c1.selectbox("Spieler 1 (Anwärter)", player_list, key=f"def_select_{selected_g_id}")
                    available_challengers = [p for p in player_list if p != defender]
                    challenger = c2.selectbox("Spieler 2 (Anwärter)", available_challengers, key=f"challenger_select_{selected_g_id}")

                with st.form(f"koth_challenge_form_{selected_g_id}", clear_on_submit=True):
                    # EXAKTE BEIDEN SPIELER FÜR SIEGER-DROPDOWN:
                    match_participants = [defender, challenger]
                    winner = st.selectbox("Sieger des Matches eintragen", match_participants)
                    
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

    # TAB 3: KOTH STATISTIKEN
    with tab_koth_stats:
        st.subheader("📊 King of the Hill Leaderboards & Statistiken")
        
        # Aggregiere KotH Daten
        king_counts = {}
        max_streaks = {}
        total_wins = {}
        
        for g_id, k_info in db.get("koth", {}).items():
            current_k = k_info.get("king")
            if current_k:
                king_counts[current_k] = king_counts.get(current_k, 0) + 1
            
            for h in k_info.get("history", []):
                w = h.get("winner")
                if w and w != "Thron-Gründung":
                    total_wins[w] = total_wins.get(w, 0) + 1
            
            # Höchste Streak tracken
            c_streak = k_info.get("streak", 0)
            if current_k and c_streak > max_streaks.get(current_k, 0):
                max_streaks[current_k] = c_streak

        st.markdown("#### 👑 Aktuelle Kronen-Besitzer")
        if not king_counts:
            st.info("Noch keine aktiven Könige.")
        else:
            for p_name, count in sorted(king_counts.items(), key=lambda x: x[1], reverse=True):
                st.write(f"👑 **{p_name}**: Hält aktuell **{count}** King of the Hill Titel (Höchste Streak: {max_streaks.get(p_name, 0)} Siege)")

        st.markdown("---")
        st.markdown("#### 🏆 Gesamte KotH Match-Siege")
        if not total_wins:
            st.write("Noch keine Matches ausgetragen.")
        else:
            stats_table = [{"Spieler": p, "Gesamt KotH Siege": w} for p, w in sorted(total_wins.items(), key=lambda x: x[1], reverse=True)]
            st.dataframe(stats_table, use_container_width=True)

# ------------------------------------------------------------------------------
# 5. CHALLENGES (ERSTELLER HIGHLIGHT & VOLLSTÄNDIGE STATISTIKEN)
# ------------------------------------------------------------------------------
elif page == "🎯 Challenges":
    st.title("🎯 CHALLENGES & HERAUSFORDERUNGEN")
    
    tab1, tab2, tab3 = st.tabs(["🔥 Aktive Challenges", "➕ Challenge Erstellen", "📊 Challenge Statistiken"])
    
    challenge_games = db.setdefault("challenge_games", {})
    player_list = list(db["players"].keys())
    
    # TAB 2: ERSTELLUNG
    with tab2:
        st.subheader("Neues Challenge-Spiel registrieren oder bestehendes wählen")
        
        with st.expander("➕ Ein neues Spiel zur Challenge-Datenbank hinzufügen"):
            cg_name = st.text_input("Spielname eingeben", placeholder="z.B. Elden Ring, Hollow Knight")
            cg_cover_custom = st.text_input("Custom Cover Bild-URL (optional):", placeholder="https://...")
            
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

    # TAB 1: AKTIVE CHALLENGES
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
                        # ERSTELLER FARBLICH HEVORGEHOBEN
                        st.markdown(f"### {c['title']} (`{cg_info['name']}`)")
                        st.markdown(f"""
                        <div class="creator-box">🛠️ ERSTELLER: {c['creator']}</div>
                        <span class="{diff_class}">{c['difficulty']}</span> | Am: {c['timestamp']}
                        """, unsafe_allow_html=True)
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

    # TAB 3: CHALLENGE STATISTIKEN
    with tab3:
        st.subheader("📊 Challenge Statistiken & Hall of Fame")
        
        if not player_list:
            st.info("Keine Spieler im System.")
        else:
            # Stats berechnen
            p_stats = {}
            for p in player_list:
                p_stats[p] = {
                    "completed_count": 0,
                    "completed_list": [],
                    "created_count": 0,
                    "created_list": [],
                    "total_stars": 0
                }
            
            challenges_list = db.get("challenges", [])
            
            for c in challenges_list:
                creator = c.get("creator")
                if creator in p_stats:
                    p_stats[creator]["created_count"] += 1
                    p_stats[creator]["created_list"].append(c["title"])
                
                for comp in c.get("completions", []):
                    p_name = comp.get("player")
                    if p_name in p_stats:
                        p_stats[p_name]["completed_count"] += 1
                        p_stats[p_name]["completed_list"].append(c["title"])
                        p_stats[p_name]["total_stars"] += comp.get("rating", 5)

            # Leaderboard anzeigen
            st.markdown("#### 🏆 Spieler-Rankings & Abzeichen")
            for p_name, data in sorted(p_stats.items(), key=lambda x: x[1]["completed_count"], reverse=True):
                stars_avg = round(data["total_stars"] / data["completed_count"], 1) if data["completed_count"] > 0 else 0
                
                badge = ""
                if data["completed_count"] >= 10: badge = "🥇 Challenge-Legende"
                elif data["completed_count"] >= 5: badge = "🥈 Master-Meister"
                elif data["completed_count"] >= 1: badge = "🥉 Herausforderer"
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 2])
                    c1.markdown(f"### **{p_name}** {badge}")
                    c2.metric("Geschaffte Challenges", f"{data['completed_count']}", f"Ø {stars_avg} ⭐ Rating")
                    c3.metric("Erstellte Challenges", f"{data['created_count']}")
                    
                    with st.expander(f"Details von {p_name} ansehen"):
                        st.write(f"**Geschaffte Challenges:** {', '.join(data['completed_list']) if data['completed_list'] else 'Keine'}")
                        st.write(f"**Erstellte Challenges:** {', '.join(data['created_list']) if data['created_list'] else 'Keine'}")

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
# 8. ADMIN-BEREICH (STRUCTURED & FULL CONTROL)
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
            "👑 KotH Verwaltung", 
            "🎯 Challenge Verwaltung",
            "👥 Spieler-Verwaltung", 
            "🌿 Brackets", 
            "🔒 Status", 
            "📩 Einsprüche", 
            "📊 Audit Logs", 
            "💾 Backup"
        ])
        
        # TAB 1: KotH Verwaltung & Full Override
        with tab_admin[0]:
            st.subheader("👑 King of the Hill Vollkontrolle & Bearbeitung")
            games = db.get("games", {})
            if not games:
                st.info("Keine KotH-Spiele vorhanden.")
            else:
                for g_id, g in list(games.items()):
                    with st.container(border=True):
                        st.markdown(f"### ID {g_id}: {g['name']}")
                        k_data = db["koth"].setdefault(g_id, {"king": None, "streak": 0, "history": []})
                        
                        # Direct Edit Form for Games
                        with st.expander("✏️ KotH Spiel-Einstellungen & King anpassen"):
                            c1, c2 = st.columns(2)
                            edit_king = c1.selectbox("König festlegen", ["NIEMAND"] + list(db["players"].keys()), 
                                                     index=0 if not k_data["king"] else (list(db["players"].keys()).index(k_data["king"]) + 1 if k_data["king"] in db["players"] else 0),
                                                     key=f"adm_king_{g_id}")
                            edit_streak = c2.number_input("Streak anpassen", min_value=0, value=k_data.get("streak", 0), key=f"adm_streak_{g_id}")
                            
                            edit_rules = st.text_area("Regeln / Waffen / Maps anpassen", value=g.get("rules", ""), key=f"adm_rules_{g_id}")
                            edit_format = st.selectbox("Format anpassen", ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"], 
                                                        index=["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"].index(g.get("format", "Best of 3 (Bo3)")) if g.get("format") in ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"] else 1,
                                                        key=f"adm_fmt_{g_id}")
                            
                            if st.button("KotH Änderungen Speichern", key=f"save_koth_{g_id}"):
                                k_data["king"] = None if edit_king == "NIEMAND" else edit_king
                                k_data["streak"] = edit_streak
                                g["rules"] = edit_rules
                                g["format"] = edit_format
                                add_audit_log(db, f"KotH Spiel {g['name']} von Admin bearbeitet.", user="Admin")
                                update_db()
                                st.success("Änderungen gespeichert!")
                                st.rerun()

                        if st.button(f"🗑️ KotH Spiel komplett löschen", key=f"del_g_{g_id}"):
                            del games[g_id]
                            if g_id in db.get("koth", {}): del db["koth"][g_id]
                            add_audit_log(db, f"KotH Spiel '{g['name']}' gelöscht", user="Admin")
                            update_db()
                            st.rerun()

        # TAB 2: Challenge Verwaltung & Full Override
        with tab_admin[1]:
            st.subheader("🎯 Challenge Vollkontrolle & Bearbeitung")
            challenges = db.get("challenges", [])
            
            if not challenges:
                st.write("Keine aktiven Challenges vorhanden.")
            else:
                for c_idx, c in enumerate(list(challenges)):
                    with st.container(border=True):
                        st.markdown(f"### Challenge #{c['id']}: {c['title']}")
                        st.write(f"Ersteller: **{c['creator']}** | Schwierigkeit: **{c['difficulty']}**")
                        
                        with st.expander("✏️ Challenge bearbeiten / korrigieren"):
                            edit_title = st.text_input("Titel", value=c["title"], key=f"c_title_{c['id']}")
                            edit_desc = st.text_area("Beschreibung", value=c["description"], key=f"c_desc_{c['id']}")
                            edit_diff = st.select_slider("Schwierigkeit", options=["Leicht", "Mittel", "Schwer", "Extrem", "Unmöglich"], 
                                                         value=c.get("difficulty", "Mittel"), key=f"c_diff_{c['id']}")
                            
                            if st.button("Challenge Speichern", key=f"save_c_{c['id']}"):
                                c["title"] = edit_title
                                c["description"] = edit_desc
                                c["difficulty"] = edit_diff
                                add_audit_log(db, f"Challenge #{c['id']} von Admin bearbeitet.", user="Admin")
                                update_db()
                                st.success("Challenge aktualisiert!")
                                st.rerun()

                        if st.button("🗑️ Challenge Löschen", key=f"del_c_{c['id']}"):
                            challenges.pop(c_idx)
                            add_audit_log(db, f"Challenge #{c['id']} ({c['title']}) gelöscht", user="Admin")
                            update_db()
                            st.rerun()

        # TAB 3: Spieler-Verwaltung
        with tab_admin[2]:
            st.subheader("👥 Spieler verwalten")
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
            st.subheader("🌿 Double Elimination Brackets")
            brackets = db.get("brackets_de", [])
            if brackets:
                for b_idx, b in enumerate(list(brackets)):
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"**Bracket #{b['id']}: {b['name']}** ({b.get('game_name', 'General')})")
                    if c2.button("🗑️ Bracket Löschen", key=f"del_b_{b['id']}"):
                        brackets.pop(b_idx)
                        add_audit_log(db, f"Bracket '{b['name']}' gelöscht", user="Admin")
                        update_db()
                        st.rerun()
                st.markdown("---")

            p_list = list(db["players"].keys())
            if len(p_list) >= 2:
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
                    r1_winners, r1_losers = [], []
                    match_id_counter = 1
                    
                    for i in range(0, len(padded_players), 2):
                        p1, p2 = padded_players[i], padded_players[i+1]
                        auto_winner = p1 if p2 == "BYE" else (p2 if p1 == "BYE" else None)
                        
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
