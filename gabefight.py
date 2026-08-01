import streamlit as st
import json
import os
import requests
import base64
import re
import math
import random
from datetime import datetime
from zoneinfo import ZoneInfo

# ------------------------------------------------------------------------------
# 1. KONFIGURATION & STYLES (MARTIAL DARK METAL / RESPONSIVE NEON GLOW)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="COMPETUS MAXIMUS",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Dark Metal Base */
    .stApp {
        background-color: #08090c;
        color: #e2e8f0;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Neon Cyan Headers */
    h1, h2, h3 {
        color: #00f0ff !important;
        letter-spacing: 1px;
        font-weight: 800 !important;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
        word-break: break-word;
    }
    
    /* Prominente Sidebar Navigation */
    section[data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 2px solid #00f0ff !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        padding: 6px !important;
        color: #00f0ff !important;
        text-transform: uppercase;
    }
    
    /* Custom Neon Containers */
    div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stContainer"] {
        border: 1px solid #1e293b !important;
        background-color: #11141c !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
        margin-bottom: 15px;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%) !important;
        color: #00f0ff !important;
        border: 1.5px solid #00f0ff !important;
        border-radius: 4px !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        text-transform: uppercase;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background: #00f0ff !important;
        color: #000000 !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.8) !important;
    }

    /* Exciting Neon Divider */
    .glowing-divider {
        height: 4px;
        background: linear-gradient(90deg, #00f0ff 0%, #f59e0b 50%, #00f0ff 100%);
        box-shadow: 0 0 12px #00f0ff;
        margin: 30px 0;
        border-radius: 2px;
    }
    
    /* RESPONSIVE FULL-CARD FIX FOR MOBILE */
    .full-challenge-card {
        border: 2px solid #00f0ff !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.35), inset 0 0 10px rgba(0, 240, 255, 0.05) !important;
        background: #0f141d !important;
        border-radius: 8px !important;
        padding: 16px;
        margin-bottom: 25px;
        box-sizing: border-box;
    }

    .challenge-flex-container {
        display: flex;
        flex-direction: row;
        gap: 16px;
        align-items: flex-start;
    }

    .challenge-img {
        width: 220px;
        max-width: 100%;
        height: auto;
        border-radius: 4px;
        border: 1.5px solid #00f0ff;
        object-fit: cover;
    }

    .challenge-body {
        flex: 1;
        min-width: 0;
    }

    /* Bracket Styling */
    .bracket-node {
        border: 1.5px solid #00f0ff;
        background: #111622;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 12px;
        box-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
    }
    .bracket-node-winner {
        border: 2px solid #10b981;
        background: rgba(16, 185, 129, 0.15);
    }
    .bracket-bye {
        opacity: 0.6;
        font-style: italic;
    }

    @media (max-width: 768px) {
        .challenge-flex-container {
            flex-direction: column;
        }
        .challenge-img {
            width: 100%;
            max-width: 280px;
            margin: 0 auto 10px auto;
            display: block;
        }
    }

    .rules-blue-box {
        border: 1.5px solid #00f0ff !important;
        background: rgba(0, 240, 255, 0.08) !important;
        border-radius: 6px;
        padding: 8px 12px;
        color: #e2e8f0;
        margin-top: 8px;
        font-size: 0.95rem;
    }
    
    .news-card {
        border-left: 5px solid #00f0ff;
        background: #111520;
        padding: 16px;
        border-radius: 6px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        border-top: 1px solid #1e293b;
        border-right: 1px solid #1e293b;
        border-bottom: 1px solid #1e293b;
    }
    .news-card-koth { border-left-color: #f59e0b; }
    .news-card-challenge { border-left-color: #10b981; }
    .news-card-admin { 
        border-left-color: #a855f7 !important; 
        background: linear-gradient(135deg, #181124 0%, #111520 100%) !important;
        box-shadow: 0 0 12px rgba(168, 85, 247, 0.3) !important;
    }
    
    .diff-leicht { background-color: #10b981; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: 800; display: inline-block; }
    .diff-mittel { background-color: #f59e0b; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: 800; display: inline-block; }
    .diff-schwer { background-color: #f97316; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: 800; display: inline-block; }
    .diff-extrem { background-color: #ef4444; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: 800; display: inline-block; }
    .diff-unmoeglich { background-color: #a855f7; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: 800; box-shadow: 0 0 10px #a855f7; display: inline-block; }

    .creator-box {
        background: rgba(0, 240, 255, 0.12);
        border: 1.5px solid #00f0ff;
        padding: 4px 8px;
        border-radius: 4px;
        color: #00f0ff;
        font-weight: 800;
        display: inline-block;
        margin-bottom: 6px;
        font-size: 0.9rem;
    }
    .king-highlight-box {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.25) 0%, rgba(180, 83, 9, 0.4) 100%);
        border: 2px solid #f59e0b;
        padding: 10px 15px;
        border-radius: 6px;
        color: #fbbf24;
        font-weight: 800;
        text-shadow: 0 0 10px rgba(245, 158, 11, 0.6);
        margin-bottom: 10px;
    }
    
    .leaderboard-card {
        background: linear-gradient(90deg, #141a24 0%, #0d121a 100%);
        border-left: 5px solid #f59e0b;
        padding: 12px 20px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. PERSISTENZ & BRACKET ENGINE (SMART BYE-SYSTEM)
# ------------------------------------------------------------------------------
DATA_FILE = "data.json"
BERLIN_TZ = ZoneInfo("Europe/Berlin")

def get_now_str():
    return datetime.now(BERLIN_TZ).strftime("%Y-%m-%d %H:%M:%S")

def get_default_data():
    return {
        "config": {
            "current_season": 1
        },
        "news": [],
        "players": {},
        "games": {},
        "challenge_games": {},
        "koth": {},
        "challenges": [],
        "brackets": {
            "single": None,
            "double": None
        },
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
            data.setdefault("news", [])
            data.setdefault("brackets", {"single": None, "double": None})
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

def add_news(data, title, content_html, category="GENERAL", custom_color=""):
    data.setdefault("news", []).append({
        "id": len(data.get("news", [])) + 1,
        "timestamp": get_now_str(),
        "title": title,
        "content_html": content_html,
        "category": category,
        "custom_color": custom_color
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

# ------------------------------------------------------------------------------
# BRACKET GENERATION & AUTO-ADVANCE LOGIC
# ------------------------------------------------------------------------------
def generate_single_elimination(game_name, players):
    n = len(players)
    if n < 2: return None
    
    # Nächste 2er-Potenz finden (z.B. 3 -> 4, 5 -> 8)
    next_pow = 1 << (n - 1).bit_length() if n > 1 else 2
    if next_pow < 2: next_pow = 2
    
    num_byes = next_pow - n
    shuffled = players.copy()
    random.shuffle(shuffled)
    
    slots = []
    for p in shuffled:
        slots.append(p)
    for _ in range(num_byes):
        slots.append("BYE (Freilos)")
        
    num_rounds = int(math.log2(next_pow))
    rounds = []
    
    # Runde 1 aufbauen
    r1_matches = []
    for i in range(0, next_pow, 2):
        p1 = slots[i]
        p2 = slots[i+1]
        winner = None
        if p1 == "BYE (Freilos)": winner = p2
        elif p2 == "BYE (Freilos)": winner = p1
        
        r1_matches.append({
            "id": f"R1_M{len(r1_matches)+1}",
            "p1": p1,
            "p2": p2,
            "winner": winner
        })
    rounds.append(r1_matches)
    
    # Folge-Runden leere Platzhalter aufbauen
    for r in range(2, num_rounds + 1):
        prev_count = len(rounds[-1])
        r_matches = []
        for m in range(prev_count // 2):
            r_matches.append({
                "id": f"R{r}_M{m+1}",
                "p1": "TBD",
                "p2": "TBD",
                "winner": None
            })
        rounds.append(r_matches)
        
    bracket = {
        "game_name": game_name,
        "type": "single",
        "created_at": get_now_str(),
        "rounds": rounds
    }
    update_bracket_advancements(bracket)
    return bracket

def update_bracket_advancements(bracket):
    """Rechnet automatisch Gewinner in die nächsten Runden durch."""
    rounds = bracket["rounds"]
    for r_idx in range(len(rounds) - 1):
        curr_round = rounds[r_idx]
        next_round = rounds[r_idx + 1]
        
        for m_idx, match in enumerate(curr_round):
            winner = match.get("winner")
            target_match_idx = m_idx // 2
            target_slot = "p1" if (m_idx % 2 == 0) else "p2"
            
            if winner:
                next_round[target_match_idx][target_slot] = winner
            else:
                next_round[target_match_idx][target_slot] = "TBD"

if "db" not in st.session_state:
    st.session_state.db = load_data()

def update_db():
    save_data(st.session_state.db)

db = st.session_state.db

# ------------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION
# ------------------------------------------------------------------------------
st.sidebar.markdown("# ⚔️ COMPETUS")
st.sidebar.markdown("### MAXIMUS")
st.sidebar.caption(f"DEUTSCHLAND (BERLIN) | {get_now_str()}")
st.sidebar.markdown("<div class='glowing-divider' style='margin: 15px 0;'></div>", unsafe_allow_html=True)

page = st.sidebar.radio(
    "NAVIGATION",
    ["📰 News", "🏆 Turniere & Brackets", "👑 King of the Hill", "🎯 Challenges", "📩 Einspruch & Anträge", "⚙️ Admin-Bereich"]
)

# ------------------------------------------------------------------------------
# 4. NEWS BEREICH
# ------------------------------------------------------------------------------
if page == "📰 News":
    st.title("📰 ARENA NEWS & HIGHLIGHTS")
    st.caption("Echtzeit-Updates über neue Kings, geschaffte Challenges und Admin-Ankündigungen.")
    
    news_list = db.get("news", [])
    
    if not news_list:
        st.info("Noch keine News vorhanden. Erstelle Challenges oder kämpfe um den Thron, um die News zu füllen!")
    else:
        for item in reversed(news_list):
            cat = item.get("category", "GENERAL")
            custom_color = item.get("custom_color", "")
            
            card_class = "news-card"
            badge = "📢 NEWS"
            badge_color = "#00f0ff"
            
            if cat == "KOTH":
                card_class += " news-card-koth"
                badge = "👑 KOTH UPDATE"
                badge_color = "#f59e0b"
            elif cat == "CHALLENGE":
                card_class += " news-card-challenge"
                badge = "🎯 CHALLENGE UPDATE"
                badge_color = "#10b981"
            elif cat == "ADMIN":
                card_class += " news-card-admin"
                badge = "📢 ADMIN ANKÜNDIGUNG"
                badge_color = "#a855f7"
                
            custom_style = ""
            if custom_color:
                custom_style = f"border-left-color: {custom_color} !important;"
                badge_color = custom_color
                
            content_display = item.get("content_html") if "content_html" in item else item.get("content", "")
            
            st.markdown(f"""
            <div class="{card_class}" style="{custom_style}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="font-weight: 800; color: {badge_color}; letter-spacing: 1px;">{badge}</span>
                    <span style="color: #64748b; font-size: 0.85em; font-weight: 600;">{item['timestamp']}</span>
                </div>
                <h3 style="margin: 0 0 8px 0; color: #ffffff !important;">{item['title']}</h3>
                <div style="font-size: 1.05em; color: #e2e8f0; line-height: 1.5;">{content_display}</div>
            </div>
            """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 5. TURNIERE & BRACKETS (SINGLE & DOUBLE ELIMINATION)
# ------------------------------------------------------------------------------
elif page == "🏆 Turniere & Brackets":
    st.title("🏆 TURNIERE & BRACKETS")
    
    tab_single, tab_double = st.tabs(["🔥 Single Elimination", "⚡ Double Elimination"])
    brackets_data = db.setdefault("brackets", {"single": None, "double": None})
    
    # REITER 1: SINGLE ELIMINATION
    with tab_single:
        single_b = brackets_data.get("single")
        if not single_b:
            st.info("Aktuell ist kein Single-Elimination Turnier aktiv. Der Admin kann ein neues Turnier im Admin-Bereich erstellen.")
        else:
            st.subheader(f"⚔️ Turnier: {single_b['game_name']} (Single Elimination)")
            st.caption(f"Erstellt am: {single_b['created_at']}")
            
            update_bracket_advancements(single_b)
            rounds = single_b["rounds"]
            
            st.markdown("### 📊 Bracket Diagramm & Übersicht")
            cols = st.columns(len(rounds))
            for r_idx, r_matches in enumerate(rounds):
                with cols[r_idx]:
                    r_title = f"Runde {r_idx+1}" if r_idx < len(rounds)-1 else "🏆 FINALE"
                    st.markdown(f"#### {r_title}")
                    
                    for m in r_matches:
                        p1_str = m['p1']
                        p2_str = m['p2']
                        winner = m.get('winner')
                        
                        p1_class = "bracket-node-winner" if winner == p1_str and p1_str != "TBD" else ""
                        p2_class = "bracket-node-winner" if winner == p2_str and p2_str != "TBD" else ""
                        
                        st.markdown(f"""
                        <div class="bracket-node">
                            <div class="{p1_class}" style="padding: 4px; border-radius: 4px;">👤 <b>{p1_str}</b></div>
                            <div style="text-align: center; color: #64748b; font-size: 0.8em; margin: 2px 0;">VS</div>
                            <div class="{p2_class}" style="padding: 4px; border-radius: 4px;">👤 <b>{p2_str}</b></div>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
            st.markdown("### ✏️ Match-Ergebnisse eintragen")
            
            for r_idx, r_matches in enumerate(rounds):
                st.markdown(f"#### Runde {r_idx+1}")
                for m_idx, m in enumerate(r_matches):
                    p1, p2 = m['p1'], m['p2']
                    if p1 in ["TBD", "BYE (Freilos)"] and p2 in ["TBD", "BYE (Freilos)"]:
                        continue
                    
                    with st.container(border=True):
                        c1, c2 = st.columns([2, 1])
                        c1.write(f"Match **{m['id']}**: **{p1}** vs **{p2}**")
                        
                        if m.get('winner'):
                            c1.success(f"Sieger: {m['winner']}")
                        
                        opts = ["- Noch offen -"]
                        if p1 not in ["TBD", "BYE (Freilos)"]: opts.append(p1)
                        if p2 not in ["TBD", "BYE (Freilos)"]: opts.append(p2)
                        
                        curr_win_idx = opts.index(m['winner']) if m.get('winner') in opts else 0
                        new_winner = c2.selectbox("Sieger wählen", opts, index=curr_win_idx, key=f"sel_sing_{r_idx}_{m_idx}")
                        
                        if c2.button("Ergebnis Speichern", key=f"btn_sing_{r_idx}_{m_idx}"):
                            m['winner'] = None if new_winner == "- Noch offen -" else new_winner
                            update_bracket_advancements(single_b)
                            if new_winner != "- Noch offen -":
                                add_audit_log(db, f"Bracket Single ({single_b['game_name']}): {new_winner} gewinnt Match {m['id']}", user=new_winner)
                            update_db()
                            st.success("Ergebnis aktualisiert!")
                            st.rerun()

    # REITER 2: DOUBLE ELIMINATION
    with tab_double:
        double_b = brackets_data.get("double")
        if not double_b:
            st.info("Aktuell ist kein Double-Elimination Turnier aktiv. Der Admin kann ein neues Turnier im Admin-Bereich erstellen.")
        else:
            st.subheader(f"⚡ Turnier: {double_b['game_name']} (Double Elimination)")
            st.caption("Double Elimination befindet sich in Vorbereitung oder kann im Admin-Bereich als Vorlage gefüllt werden.")
            st.write("Information: Ein automatisches Double Elimination Bracket kann aus dem Admin-Bereich verwaltet werden.")

# ------------------------------------------------------------------------------
# 6. KING OF THE HILL
# ------------------------------------------------------------------------------
elif page == "👑 King of the Hill":
    st.title("👑 KING OF THE HILL")
    
    tab_koth_active, tab_koth_create, tab_koth_stats = st.tabs(["🔥 ÜBERSICHT", "➕ NEUES KOTH-SPIEL & THRON GRÜNDEN", "📊 KOTH STATISTIKEN"])
    
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
                custom_cover = c2.text_input("Custom Cover Bild-URL / Steam-Link (optional):", placeholder="https://...")
                
                g_link_input = st.text_input("Custom Store / Website-Link (optional):", placeholder="https://...")
                rules_comment = st.text_area("Herausforderungs-Regeln / Modus / Waffen & Maps:", 
                                             placeholder="z.B. Nur 1v1 AWP auf Aim_Map, Ohne Rüstung, Hardcore Modus...")
                
                if st.form_submit_button("Werde König"):
                    if not g_name:
                        st.error("Bitte gib einen Spielnamen ein!")
                    else:
                        cover_url, store_link = fetch_steam_info(g_name, custom_cover)
                        if g_link_input.strip():
                            store_link = g_link_input.strip()
                            
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
                        
                        news_html = f"<b>{creator}</b> hat den Thron für <span style='color:#00f0ff;'><b>{g_name}</b></span> errichtet und ist der erste König!"
                        add_news(db, f"👑 Neuer Thron errichtet: {g_name}", news_html, category="KOTH")
                        
                        update_db()
                        st.success(f"KotH Arena für '{g_name}' eröffnet! Du bist der aktuelle King!")
                        st.rerun()

    # TAB 1: ÜBERSICHT
    with tab_koth_active:
        if not games:
            st.info("Noch keine KotH-Spiele vorhanden. Wechsel in den Reiter 'Neues KotH-Spiel & Thron gründen', um das erste Spiel zu starten.")
        else:
            st.subheader("Übersicht")
            cols = st.columns(min(len(games), 4))
            for idx, (g_id, g_info) in enumerate(games.items()):
                k_data = db["koth"].get(g_id, {"king": None, "streak": 0})
                cover = g_info.get("custom_cover") or "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER"
                rules_preview = g_info.get("rules", "")
                
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
                        
                        if rules_preview:
                            st.markdown(f"""
                            <div class="rules-blue-box">
                                📜 <b>Regeln:</b> {rules_preview}
                            </div>
                            """, unsafe_allow_html=True)

            st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
            
            st.markdown("## ⚡ HERAUSFORDERUNGS-WAHL")
            
            selected_g_id = st.selectbox(
                "HERAUSFORDERUNGS-WAHL", 
                list(games.keys()), 
                format_func=lambda x: f"⚔️ {games[x]['name']} — ({games[x].get('rules', 'Keine Sonderregeln')})",
                label_visibility="collapsed"
            )
            
            g_info = games[selected_g_id]
            k_data = db["koth"].setdefault(selected_g_id, {"king": None, "streak": 0, "history": []})
            
            col_img, col_detail = st.columns([1, 2])
            with col_img:
                st.image(g_info.get("custom_cover"), use_container_width=True)
            with col_detail:
                st.markdown(f"## {g_info['name']}")
                st.write(f"Gründer: `{g_info.get('creator', 'Admin')}` | Format: **{g_info.get('format', 'Bo3')}**")
                if g_info.get('link'): st.markdown(f"🔗 [Store / Website Link öffnen]({g_info['link']})")
                
                if g_info.get('rules'):
                    st.markdown(f"""
                    <div class="rules-blue-box">
                        📜 <b>Festgelegte Regeln / Waffen & Maps:</b> {g_info['rules']}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="king-highlight-box" style="font-size: 1.25em; margin-top: 10px;">
                    👑 AKTUELLER KÖNIG: <b>{k_data['king'] or 'Thron unbesetzt'}</b> (Streak: <b>{k_data['streak']} Siege</b>)
                </div>
                """, unsafe_allow_html=True)

            st.markdown("### ⚔️ King herausfordern")
            if len(player_list) < 2:
                st.warning("Mindestens 2 registrierte Spieler erforderlich.")
            else:
                current_king = k_data['king']
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
                    match_participants = [defender, challenger]
                    winner = st.selectbox("Sieger des Matches eintragen", match_participants)
                    
                    if st.form_submit_button("Match-Ergebnis Speichern"):
                        old_king = k_data["king"]
                        if winner == k_data["king"]:
                            k_data["streak"] += 1
                            news_html = f"<b>{winner}</b> hat seinen Thron in <span style='color:#00f0ff;'><b>{g_info['name']}</b></span> erfolgreich verteidigt! (Streak: <b>{k_data['streak']}</b>)"
                        else:
                            k_data["king"] = winner
                            k_data["streak"] = 1
                            news_html = f"👑 <span style='color:#ef4444;'><b>ENTTHRONUNG!</b></span> <b>{winner}</b> hat <b>{old_king}</b> besiegt und ist der neue King in <span style='color:#00f0ff;'><b>{g_info['name']}</b></span>!"
                        
                        k_data.setdefault("history", []).append({
                            "timestamp": get_now_str(),
                            "defender": defender,
                            "challenger": challenger,
                            "winner": winner,
                            "format": g_info.get("format", "Bo3")
                        })
                        add_audit_log(db, f"KotH ({g_info['name']}): {winner} gewann gegen {defender if winner == challenger else challenger}", user=winner)
                        
                        add_news(db, f"⚔️ Thronkampf in {g_info['name']}", news_html, category="KOTH")
                        
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
        st.subheader("📊 King of the Hill Leaderboards & Hall of Fame")
        
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
            
            c_streak = k_info.get("streak", 0)
            if current_k and c_streak > max_streaks.get(current_k, 0):
                max_streaks[current_k] = c_streak

        st.markdown("#### 👑 Aktuelle Kronen-Besitzer")
        if not king_counts:
            st.info("Noch keine aktiven Könige.")
        else:
            for p_name, count in sorted(king_counts.items(), key=lambda x: x[1], reverse=True):
                st.write(f"👑 **{p_name}**: Hält aktuell **{count}** King of the Hill Titel (Höchste Streak: {max_streaks.get(p_name, 0)} Siege)")

        st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
        
        st.markdown("## 🔥 GESAMTE KOTH MATCH-SIEGE")
        if not total_wins:
            st.write("Noch keine KotH Kämpfe ausgetragen.")
        else:
            sorted_wins = sorted(total_wins.items(), key=lambda x: x[1], reverse=True)
            max_val = sorted_wins[0][1] if sorted_wins else 1
            
            for rank_idx, (p_name, w_count) in enumerate(sorted_wins):
                medal = "🥇" if rank_idx == 0 else ("🥈" if rank_idx == 1 else ("🥉" if rank_idx == 2 else "⚔️"))
                percent = int((w_count / max_val) * 100)
                
                st.markdown(f"""
                <div class="leaderboard-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.3em; font-weight: 800;">{medal} Rang #{rank_idx+1}: {p_name}</span>
                        <span style="font-size: 1.4em; font-weight: 900; color: #00f0ff;">{w_count} Siege</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(percent / 100)

# ------------------------------------------------------------------------------
# 7. CHALLENGES
# ------------------------------------------------------------------------------
elif page == "🎯 Challenges":
    st.title("🎯 CHALLENGES")
    
    tab1, tab2, tab3 = st.tabs(["🔥 Aktive Challenges", "➕ Challenge Erstellen", "📊 Challenge Statistiken"])
    
    challenge_games = db.setdefault("challenge_games", {})
    player_list = list(db["players"].keys())
    
    # TAB 2: ERSTELLUNG
    with tab2:
        st.subheader("➕ Neues Challenge-Spiel registrieren")
        
        cg_name = st.text_input("Spielname eingeben", placeholder="z.B. Elden Ring, Hollow Knight")
        cg_cover_custom = st.text_input("Custom Cover Bild-URL / Steam-Link (optional):", placeholder="https://...")
        
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

        st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
        
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
                c_custom_cover = st.text_input("Spezifisches Cover-Bild für DIESE Challenge (optional):", placeholder="Leer lassen für Spiel-Standardbild")
                c_desc = st.text_area("Detaillierte Beschreibung / Regeln", placeholder="Erkläre exakt, was getan werden muss...")
                c_difficulty = st.select_slider("Schwierigkeitsgrad", options=["Leicht", "Mittel", "Schwer", "Extrem", "Unmöglich"])
                
                if st.form_submit_button("Challenge Veröffentlichen"):
                    if c_title and c_desc:
                        new_c = {
                            "id": len(db.get("challenges", [])) + 1,
                            "creator": creator,
                            "challenge_game_id": cg_id,
                            "title": c_title,
                            "custom_cover": c_custom_cover.strip(),
                            "description": c_desc,
                            "difficulty": c_difficulty,
                            "timestamp": get_now_str(),
                            "completions": []
                        }
                        db.setdefault("challenges", []).append(new_c)
                        add_audit_log(db, f"Challenge '{c_title}' von {creator} erstellt.", user=creator)
                        
                        cg_game_name = challenge_games.get(cg_id, {}).get("name", "Unbekannt")
                        news_html = f"<b>{creator}</b> hat eine neue Challenge für <span style='color:#00f0ff;'><b>{cg_game_name}</b></span> herausgegeben! Schwierigkeit: <b>{c_difficulty}</b>"
                        add_news(db, f"🎯 Neue Challenge: {c_title}", news_html, category="CHALLENGE")
                        
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
                cover = c.get("custom_cover") if c.get("custom_cover") else cg_info.get("cover")
                diff_class = diff_css_map.get(c['difficulty'], 'diff-mittel')
                completions = c.get("completions", [])
                
                st.markdown(f"""
                <div class="full-challenge-card">
                    <div class="challenge-flex-container">
                        <img src="{cover}" class="challenge-img">
                        <div class="challenge-body">
                            <h3 style="margin: 0 0 6px 0; color: #00f0ff !important;">{c['title']} <span style="font-size: 0.85em; color: #94a3b8;">({cg_info['name']})</span></h3>
                            <div class="creator-box">🛠️ ERSTELLER: {c['creator']}</div><br>
                            <span class="{diff_class}">{c['difficulty']}</span> 
                            <span style="color: #64748b; font-size: 0.85em; font-weight: 600;">| {c['timestamp']}</span>
                            <p style="margin-top: 10px; margin-bottom: 0; font-size: 1rem; color: #e2e8f0; line-height: 1.4;">{c['description']}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.markdown("#### 🌟 Absolvierte Versuche")
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
                                    
                                    news_html = f"🏆 <b>{p_name}</b> hat die Challenge <b>{c['title']}</b> (<span style='color:#00f0ff;'><b>{cg_info['name']}</b></span>) erfolgreich gemeistert!"
                                    add_news(db, f"🏆 Challenge Meisterschaft!", news_html, category="CHALLENGE")
                                    
                                    update_db()
                                    st.success("Erfolg eingetragen!")
                                    st.rerun()

    # TAB 3: CHALLENGE STATISTIKEN
    with tab3:
        st.subheader("📊 Challenge Statistiken & Hall of Fame")
        
        if not player_list:
            st.info("Keine Spieler im System.")
        else:
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
                cg_info = challenge_games.get(c.get("challenge_game_id"), {"name": "Unbekannt"})
                game_title_str = f"{c['title']} ({cg_info['name']})"
                
                if creator in p_stats:
                    p_stats[creator]["created_count"] += 1
                    p_stats[creator]["created_list"].append(game_title_str)
                
                for comp in c.get("completions", []):
                    p_name = comp.get("player")
                    if p_name in p_stats:
                        p_stats[p_name]["completed_count"] += 1
                        p_stats[p_name]["completed_list"].append(game_title_str)
                        p_stats[p_name]["total_stars"] += comp.get("rating", 5)

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
                        st.write(f"**Geschaffte Challenges (inkl. Spiel):** {', '.join(data['completed_list']) if data['completed_list'] else 'Keine'}")
                        st.write(f"**Erstellte Challenges:** {', '.join(data['created_list']) if data['created_list'] else 'Keine'}")

# ------------------------------------------------------------------------------
# 8. EINSPRUCH & ANTRÄGE
# ------------------------------------------------------------------------------
elif page == "📩 Einspruch & Anträge":
    st.title("📩 ANTRÄGE & EINSPRÜCHE")
    
    with st.form("appeal_form", clear_on_submit=True):
        st.subheader("Einspruch oder Antrag einreichen")
        player_list = list(db["players"].keys())
        sender = st.selectbox("Antragsteller", player_list if player_list else ["-"])
        target = st.selectbox("Betroffener Spieler / Gegenstand", player_list if player_list else ["-"])
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
# 9. ADMIN-BEREICH (INKLUSIVE TURNIER- & BRACKET-VERWALTUNG)
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
            "📰 News Verwaltung",
            "🏆 Turnier Verwaltung",
            "👑 KotH Verwaltung", 
            "🎯 Challenge Verwaltung",
            "👥 Spieler-Verwaltung", 
            "📩 Einsprüche", 
            "📊 Audit Logs", 
            "💾 Backup"
        ])
        
        # TAB 1: NEWS VERWALTUNG
        with tab_admin[0]:
            st.subheader("📰 Arena-News & Ankündigungen verwalten")
            
            with st.expander("➕ Eigene Admin-News / Ankündigung verfassen", expanded=True):
                with st.form("admin_create_news_form", clear_on_submit=True):
                    news_title = st.text_input("News Überschrift", placeholder="z.B. 🔥 Großes Sommer-Turnier startet Freitag!")
                    news_content = st.text_area("Inhalt / Ankündigungstext (HTML-Tags erlaubt)", placeholder="z.B. Wir starten dieses Wochenende mit neuem Reglement...")
                    
                    c1, c2 = st.columns(2)
                    news_cat = c1.selectbox("Kategorie", ["ADMIN", "GENERAL", "KOTH", "CHALLENGE"])
                    custom_color = c2.selectbox("Auffällige Akzentfarbe wählen", ["#a855f7 (Purple)", "#00f0ff (Cyan)", "#f59e0b (Gold)", "#ef4444 (Rot)", "#10b981 (Grün)"])
                    
                    if st.form_submit_button("📢 News Veröffentlichen"):
                        if news_title and news_content:
                            color_hex = custom_color.split(" ")[0]
                            add_news(db, news_title, news_content, category=news_cat, custom_color=color_hex)
                            add_audit_log(db, f"Admin News '{news_title}' erstellt.", user="Admin")
                            update_db()
                            st.success("Ankündigung veröffentlicht!")
                            st.rerun()

            st.markdown("---")
            st.markdown("#### 📜 Bestehende News bearbeiten oder löschen")
            news_list = db.get("news", [])
            
            if not news_list:
                st.info("Keine News vorhanden.")
            else:
                for idx, n in enumerate(list(reversed(news_list))):
                    real_idx = len(news_list) - 1 - idx
                    with st.container(border=True):
                        st.write(f"**#{n.get('id', real_idx+1)}: {n['title']}** ({n['timestamp']})")
                        
                        with st.expander("✏️ Bearbeiten"):
                            e_title = st.text_input("Titel", value=n['title'], key=f"news_t_{real_idx}")
                            e_content = st.text_area("Inhalt", value=n.get('content_html', n.get('content', '')), key=f"news_c_{real_idx}")
                            
                            if st.button("Änderungen Speichern", key=f"save_news_{real_idx}"):
                                n['title'] = e_title
                                n['content_html'] = e_content
                                update_db()
                                st.success("News aktualisiert!")
                                st.rerun()

                        if st.button("🗑️ News Löschen", key=f"del_news_{real_idx}"):
                            news_list.pop(real_idx)
                            update_db()
                            st.rerun()

        # TAB 2: TURNIER VERWALTUNG (BRACKETS GENERIEREN & EDTIEREN)
        with tab_admin[1]:
            st.subheader("🏆 Turnier & Bracket-Generierung")
            player_list = list(db["players"].keys())
            
            st.markdown("#### 1. Neues Single-Elimination Turnier generieren")
            with st.form("create_single_bracket_form"):
                t_game = st.text_input("Turnier-Spielname", placeholder="z.B. Rocket League 1v1, Street Fighter")
                selected_players = st.multiselect("Teilnehmende Spieler wählen", player_list, default=player_list)
                
                if st.form_submit_button("🎲 Single-Elimination Bracket Generieren"):
                    if not t_game or len(selected_players) < 2:
                        st.error("Bitte gib einen Spielnamen ein und wähle mindestens 2 Spieler!")
                    else:
                        new_b = generate_single_elimination(t_game, selected_players)
                        db.setdefault("brackets", {})["single"] = new_b
                        add_audit_log(db, f"Neues Single-Elimination Bracket für {t_game} generiert.", user="Admin")
                        
                        news_html = f"🏆 Ein neues Single-Elimination Turnier in <span style='color:#00f0ff;'><b>{t_game}</b></span> mit {len(selected_players)} Spielern wurde gestartet!"
                        add_news(db, f"🏆 Neues Turnier: {t_game}", news_html, category="GENERAL", custom_color="#00f0ff")
                        
                        update_db()
                        st.success("Turnier erstellt!")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### 🛠️ Aktuelles Single-Bracket Override / Manuelle Anpassungen")
            curr_single = db.get("brackets", {}).get("single")
            if not curr_single:
                st.info("Aktuell kein Single-Elimination Bracket zum Bearbeiten vorhanden.")
            else:
                st.write(f"Bearbeite Turnier: **{curr_single['game_name']}**")
                for r_idx, r_matches in enumerate(curr_single["rounds"]):
                    with st.expander(f"✏️ Manuelles Override - Runde {r_idx+1}"):
                        for m_idx, m in enumerate(r_matches):
                            st.write(f"**Match {m['id']}**")
                            c1, c2, c3 = st.columns(3)
                            edit_p1 = c1.text_input("Spieler 1", value=m['p1'], key=f"ov_p1_{r_idx}_{m_idx}")
                            edit_p2 = c2.text_input("Spieler 2", value=m['p2'], key=f"ov_p2_{r_idx}_{m_idx}")
                            edit_w = c3.text_input("Gewinner (manuell)", value=m.get('winner') or "", key=f"ov_w_{r_idx}_{m_idx}")
                            
                            if st.button("Slot Speichern", key=f"btn_ov_{r_idx}_{m_idx}"):
                                m['p1'] = edit_p1
                                m['p2'] = edit_p2
                                m['winner'] = edit_w if edit_w.strip() else None
                                update_bracket_advancements(curr_single)
                                update_db()
                                st.success("Slot aktualisiert!")
                                st.rerun()

                if st.button("🗑️ Single-Elimination Turnier Zurücksetzen / Löschen"):
                    db["brackets"]["single"] = None
                    update_db()
                    st.success("Turnier gelöscht!")
                    st.rerun()

        # TAB 3: KotH
        with tab_admin[2]:
            st.subheader("👑 King of the Hill Vollkontrolle")
            games = db.get("games", {})
            if not games:
                st.info("Keine KotH-Spiele vorhanden.")
            else:
                for g_id, g in list(games.items()):
                    with st.container(border=True):
                        st.markdown(f"### ID {g_id}: {g['name']}")
                        k_data = db["koth"].setdefault(g_id, {"king": None, "streak": 0, "history": []})
                        
                        with st.expander("✏️ KotH Spiel-Daten, Cover & Store-Link anpassen"):
                            edit_name = st.text_input("Spielname", value=g["name"], key=f"adm_gname_{g_id}")
                            edit_cover = st.text_input("Cover Grafiken-URL / Steam-Link", value=g.get("custom_cover", ""), key=f"adm_gcover_{g_id}")
                            edit_link = st.text_input("Store / Website-Link", value=g.get("link", ""), key=f"adm_glink_{g_id}")
                            
                            c1, c2 = st.columns(2)
                            edit_king = c1.selectbox("König festlegen", ["NIEMAND"] + list(db["players"].keys()), 
                                                     index=0 if not k_data["king"] else (list(db["players"].keys()).index(k_data["king"]) + 1 if k_data["king"] in db["players"] else 0),
                                                     key=f"adm_king_{g_id}")
                            edit_streak = c2.number_input("Streak anpassen", min_value=0, value=k_data.get("streak", 0), key=f"adm_streak_{g_id}")
                            
                            edit_rules = st.text_area("Regeln / Waffen / Maps", value=g.get("rules", ""), key=f"adm_rules_{g_id}")
                            edit_format = st.selectbox("Format", ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"], 
                                                        index=["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"].index(g.get("format", "Best of 3 (Bo3)")) if g.get("format") in ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"] else 1,
                                                        key=f"adm_fmt_{g_id}")
                            
                            if st.button("KotH Änderungen Speichern", key=f"save_koth_{g_id}"):
                                g["name"] = edit_name
                                g["custom_cover"] = edit_cover.strip()
                                g["link"] = edit_link.strip()
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

        # TAB 4: Challenge Verwaltung
        with tab_admin[3]:
            st.subheader("🎯 Challenge-Spiele & Challenges verwalten")
            
            st.markdown("#### 1. Challenge-Spiele bearbeiten")
            cg_games = db.get("challenge_games", {})
            if not cg_games:
                st.write("Keine Challenge-Spiele vorhanden.")
            else:
                for cg_id, cg in list(cg_games.items()):
                    with st.container(border=True):
                        st.markdown(f"**ID {cg_id}: {cg['name']}**")
                        with st.expander("✏️ Challenge-Spiel Daten anpassen"):
                            cg_edit_name = st.text_input("Spielname", value=cg["name"], key=f"cg_name_{cg_id}")
                            cg_edit_cover = st.text_input("Cover-Grafik URL / Steam Link", value=cg.get("cover", ""), key=f"cg_cover_{cg_id}")
                            
                            if st.button("Spiel-Daten Speichern", key=f"save_cg_{cg_id}"):
                                cg["name"] = cg_edit_name
                                cg["cover"] = cg_edit_cover.strip()
                                update_db()
                                st.success("Challenge-Spiel aktualisiert!")
                                st.rerun()
                                
                        if st.button(f"🗑️ Challenge-Spiel Löschen", key=f"del_cg_{cg_id}"):
                            del cg_games[cg_id]
                            add_audit_log(db, f"Challenge-Spiel '{cg['name']}' gelöscht", user="Admin")
                            update_db()
                            st.rerun()

            st.markdown("---")
            st.markdown("#### 2. Einzelne Challenges bearbeiten")
            challenges = db.get("challenges", [])
            
            if not challenges:
                st.write("Keine aktiven Challenges vorhanden.")
            else:
                for c_idx, c in enumerate(list(challenges)):
                    with st.container(border=True):
                        st.markdown(f"### Challenge #{c['id']}: {c['title']}")
                        st.write(f"Ersteller: **{c['creator']}** | Schwierigkeit: **{c['difficulty']}**")
                        
                        with st.expander("✏️ Challenge bearbeiten / Grafiken anpassen"):
                            edit_title = st.text_input("Titel", value=c["title"], key=f"c_title_{c['id']}")
                            edit_cover = st.text_input("Custom Cover Bild-URL (optional)", value=c.get("custom_cover", ""), key=f"c_cover_{c['id']}")
                            edit_desc = st.text_area("Beschreibung", value=c["description"], key=f"c_desc_{c['id']}")
                            edit_diff = st.select_slider("Schwierigkeit", options=["Leicht", "Mittel", "Schwer", "Extrem", "Unmöglich"], 
                                                         value=c.get("difficulty", "Mittel"), key=f"c_diff_{c['id']}")
                            
                            if st.button("Challenge Speichern", key=f"save_c_{c['id']}"):
                                c["title"] = edit_title
                                c["custom_cover"] = edit_cover.strip()
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

        # TAB 5: Spieler-Verwaltung
        with tab_admin[4]:
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
