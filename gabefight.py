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
    .stApp {
        background-color: #08090c;
        color: #e2e8f0;
        font-family: 'Segoe UI', Roboto, sans-serif;
    }
    
    h1, h2, h3 {
        color: #00f0ff !important;
        letter-spacing: 1px;
        font-weight: 800 !important;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.4);
        word-break: break-word;
    }
    
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
    
    div[data-testid="stExpander"], div[data-testid="stForm"], div[data-testid="stContainer"] {
        border: 1px solid #1e293b !important;
        background-color: #11141c !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
        margin-bottom: 15px;
    }

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

    .glowing-divider {
        height: 4px;
        background: linear-gradient(90deg, #00f0ff 0%, #f59e0b 50%, #00f0ff 100%);
        box-shadow: 0 0 12px #00f0ff;
        margin: 30px 0;
        border-radius: 2px;
    }
    
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

    .challenge-body { flex: 1; min-width: 0; }

    /* Bracket Styling */
    .bracket-node {
        border: 1.5px solid #00f0ff;
        background: #111622;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 12px;
        box-shadow: 0 0 8px rgba(0, 240, 255, 0.2);
    }
    .bracket-node-loser {
        border: 1.5px solid #f59e0b;
        background: rgba(245, 158, 11, 0.05);
    }
    .bracket-node-winner {
        border: 2px solid #10b981;
        background: rgba(16, 185, 129, 0.15);
    }

    .winner-champion-banner {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(217, 119, 6, 0.6) 100%);
        border: 3px solid #f59e0b;
        box-shadow: 0 0 25px rgba(245, 158, 11, 0.8);
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-bottom: 25px;
    }

    @media (max-width: 768px) {
        .challenge-flex-container { flex-direction: column; }
        .challenge-img { width: 100%; max-width: 280px; margin: 0 auto 10px auto; display: block; }
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
    .news-card-bracket {
        border-left-color: #f59e0b !important;
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, #111520 100%) !important;
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.3) !important;
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
        "config": {"current_season": 1},
        "news": [],
        "players": {},
        "games": {},
        "challenge_games": {},
        "koth": {},
        "challenges": [],
        "brackets": {"single": None, "double": None},
        "appeals": [],
        "audit_logs": []
    }

def sync_to_github(json_str):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    path = st.secrets.get("GITHUB_FILE_PATH", "data.json")
    if not token or not repo: return

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
    res = requests.get(url, headers=headers)
    sha = res.json().get("sha") if res.status_code == 200 else None
    
    content_b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    payload = {"message": f"Auto-Sync data.json [{get_now_str()}]", "content": content_b64}
    if sha: payload["sha"] = sha
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
    with open(DATA_FILE, "w", encoding="utf-8") as f: f.write(json_str)
    if sync:
        try: sync_to_github(json_str)
        except Exception as e: st.warning(f"GitHub Sync fehlgeschlagen: {e}")

def add_audit_log(data, action, user="System"):
    data["audit_logs"].append({"timestamp": get_now_str(), "user": user, "action": action})

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
    except Exception: pass

    return "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER", ""

# ------------------------------------------------------------------------------
# DYNAMISCHE DUAL-BRACKET ENGINE (SINGLE & DOUBLE ELIMINATION MIT EXACT FREILOS)
# ------------------------------------------------------------------------------
def generate_bracket_data(game_name, players, cover, rules, link, b_type="single"):
    n = len(players)
    if n < 2: return None
    
    next_pow = 1 << (n - 1).bit_length() if n > 1 else 2
    if next_pow < 2: next_pow = 2
    
    num_byes = next_pow - n
    shuffled = players.copy()
    random.shuffle(shuffled)
    
    # Freilose an den Anfang / gleichmäßig verteilen
    byes = ["BYE (Freilos)"] * num_byes
    real_players = shuffled.copy()
    
    slots = []
    # Paarungen aufbauen: Freilose zuerst verteilen damit Freilos-Empfänger automatisch vorrücken
    for i in range(num_byes):
        slots.append(real_players.pop(0))
        slots.append("BYE (Freilos)")
    while real_players:
        slots.append(real_players.pop(0))

    num_rounds = int(math.log2(next_pow))
    winner_rounds = []
    
    # --- WINNER BRACKET (RUNDE 1) ---
    r1_matches = []
    for i in range(0, len(slots), 2):
        p1 = slots[i]
        p2 = slots[i+1] if i+1 < len(slots) else "BYE (Freilos)"
        winner = None
        if p1 == "BYE (Freilos)": winner = p2
        elif p2 == "BYE (Freilos)": winner = p1
        r1_matches.append({"id": f"W_R1_M{len(r1_matches)+1}", "p1": p1, "p2": p2, "winner": winner})
    winner_rounds.append(r1_matches)
    
    # WINNER FOLGERUNDEN
    for r in range(2, num_rounds + 1):
        prev_count = len(winner_rounds[-1])
        r_matches = []
        for m in range(prev_count // 2):
            r_matches.append({"id": f"W_R{r}_M{m+1}", "p1": "TBD", "p2": "TBD", "winner": None})
        winner_rounds.append(r_matches)
        
    bracket = {
        "game_name": game_name,
        "cover": cover,
        "rules": rules,
        "link": link,
        "type": b_type,
        "created_at": get_now_str(),
        "champion": None,
        "rounds": winner_rounds
    }

    # DOUBLE ELIMINATION: LOSERS BRACKET & GRAND FINALS
    if b_type == "double":
        losers_rounds = []
        for r in range(1, (num_rounds - 1) * 2 + 1):
            num_m = max(1, next_pow // (2 ** ((r // 2) + 2)))
            l_matches = []
            for m in range(num_m):
                l_matches.append({"id": f"L_R{r}_M{m+1}", "p1": "TBD", "p2": "TBD", "winner": None})
            losers_rounds.append(l_matches)
            
        bracket["losers_rounds"] = losers_rounds
        bracket["grand_final"] = {"id": "GF_M1", "p1": "TBD", "p2": "TBD", "winner": None}
        bracket["grand_final_reset"] = {"id": "GF_RESET", "p1": "TBD", "p2": "TBD", "winner": None, "active": False}

    update_bracket_advancements(bracket)
    return bracket

def update_bracket_advancements(bracket):
    b_type = bracket.get("type", "single")
    rounds = bracket["rounds"]
    
    # 1. WINNER BRACKET ADVANCEMENT
    for r_idx in range(len(rounds) - 1):
        curr_round = rounds[r_idx]
        next_round = rounds[r_idx + 1]
        
        for m_idx, match in enumerate(curr_round):
            winner = match.get("winner")
            target_match_idx = m_idx // 2
            target_slot = "p1" if (m_idx % 2 == 0) else "p2"
            
            if winner: next_round[target_match_idx][target_slot] = winner
            else: next_round[target_match_idx][target_slot] = "TBD"

    # SINGLE ELIMINATION CHAMPION
    if b_type == "single":
        final_match = rounds[-1][0]
        if final_match.get("winner"):
            bracket["champion"] = final_match["winner"]

    # DOUBLE ELIMINATION ADVANCEMENT
    if b_type == "double":
        l_rounds = bracket.get("losers_rounds", [])
        
        # Verlierer R1 -> Losers R1
        for m_idx, m in enumerate(rounds[0]):
            w = m.get("winner")
            if w:
                loser = m["p2"] if m["p1"] == w else m["p1"]
                if loser != "BYE (Freilos)" and l_rounds:
                    target_m = l_rounds[0][m_idx // 2]
                    slot = "p1" if (m_idx % 2 == 0) else "p2"
                    target_m[slot] = loser

        # Durchrechnen Losers Bracket
        for lr_idx in range(len(l_rounds) - 1):
            curr_lr = l_rounds[lr_idx]
            next_lr = l_rounds[lr_idx + 1]
            for m_idx, match in enumerate(curr_lr):
                w = match.get("winner")
                if w:
                    target_m_idx = m_idx // 2 if len(next_lr) < len(curr_lr) else m_idx
                    slot = "p1" if (m_idx % 2 == 0 or len(next_lr) == len(curr_lr)) else "p2"
                    next_lr[target_m_idx][slot] = w

        # Grand Finals
        gf = bracket.setdefault("grand_final", {"id": "GF_M1", "p1": "TBD", "p2": "TBD", "winner": None})
        winner_champ = rounds[-1][0].get("winner")
        losers_champ = l_rounds[-1][0].get("winner") if l_rounds else None
        
        if winner_champ: gf["p1"] = winner_champ
        if losers_champ: gf["p2"] = losers_champ

        gf_w = gf.get("winner")
        gf_reset = bracket.setdefault("grand_final_reset", {"id": "GF_RESET", "p1": "TBD", "p2": "TBD", "winner": None, "active": False})

        if gf_w:
            if gf_w == gf["p1"]:
                # Winner Champ gewinnt -> Sofort Gesamtsieger
                bracket["champion"] = gf_w
                gf_reset["active"] = False
            elif gf_w == gf["p2"]:
                # Loser Champ gewinnt Match 1 -> BRACKET RESET!
                gf_reset["active"] = True
                gf_reset["p1"] = gf["p1"]
                gf_reset["p2"] = gf["p2"]
                
                if gf_reset.get("winner"):
                    bracket["champion"] = gf_reset["winner"]

if "db" not in st.session_state:
    st.session_state.db = load_data()

def update_db(): save_data(st.session_state.db)

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
# 4. NEWS BEREICH (MIT EXTRA REITER FÜR TURNIERSIEGER)
# ------------------------------------------------------------------------------
if page == "📰 News":
    st.title("📰 ARENA NEWS & HIGHLIGHTS")
    
    news_tab_all, news_tab_brackets = st.tabs(["📢 Alle News & Updates", "🏆 Turniersieger & Brackets"])
    news_list = db.get("news", [])
    
    def render_news_items(items):
        if not items:
            st.info("Keine News in dieser Kategorie vorhanden.")
            return
        for item in reversed(items):
            cat = item.get("category", "GENERAL")
            custom_color = item.get("custom_color", "")
            
            card_class = "news-card"
            badge = "📢 NEWS"
            badge_color = "#00f0ff"
            
            if cat == "KOTH": card_class += " news-card-koth"; badge = "👑 KOTH UPDATE"; badge_color = "#f59e0b"
            elif cat == "CHALLENGE": card_class += " news-card-challenge"; badge = "🎯 CHALLENGE UPDATE"; badge_color = "#10b981"
            elif cat == "BRACKET": card_class += " news-card-bracket"; badge = "🏆 TURNIER SIEGER"; badge_color = "#f59e0b"
            elif cat == "ADMIN": card_class += " news-card-admin"; badge = "📢 ADMIN ANKÜNDIGUNG"; badge_color = "#a855f7"
                
            custom_style = f"border-left-color: {custom_color} !important;" if custom_color else ""
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

    with news_tab_all:
        render_news_items(news_list)
        
    with news_tab_brackets:
        bracket_news = [n for n in news_list if n.get("category") == "BRACKET"]
        render_news_items(bracket_news)

# ------------------------------------------------------------------------------
# 5. TURNIERE & BRACKETS (DOUBLE ELIMINATION ZUERST + CHAMPION BANNER OBEN)
# ------------------------------------------------------------------------------
elif page == "🏆 Turniere & Brackets":
    st.title("🏆 TURNIERE & BRACKETS")
    
    tab_double, tab_single = st.tabs(["⚡ Double Elimination", "🔥 Single Elimination"])
    brackets_data = db.setdefault("brackets", {"single": None, "double": None})
    
    def render_bracket_view(b_data, b_key):
        if not b_data:
            st.info("Aktuell ist kein Turnier in dieser Kategorie aktiv. Der Admin kann ein neues Turnier im Admin-Bereich erstellen.")
            return

        update_bracket_advancements(b_data)
        
        # PROMINENTER CHAMPION BANNER GANZ OBEN
        if b_data.get("champion"):
            st.markdown(f"""
            <div class="winner-champion-banner">
                <h1 style="color: #fbbf24 !important; margin: 0; font-size: 2.2em;">👑 TURNIERSIEGER 👑</h1>
                <h2 style="color: #ffffff !important; margin: 10px 0 0 0; font-size: 2.8em; text-shadow: 0 0 15px #f59e0b;">{b_data['champion']}</h2>
                <p style="color: #fde68a; font-size: 1.1em; margin-top: 5px;">Hat das Turnier <b>"{b_data['game_name']}"</b> triumphal gewonnen!</p>
            </div>
            """, unsafe_allow_html=True)

        col_img, col_detail = st.columns([1, 2])
        with col_img:
            st.image(b_data.get('cover', 'https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER'), use_container_width=True)
        with col_detail:
            st.markdown(f"## {b_data['game_name']}")
            st.caption(f"Erstellt am: {b_data['created_at']}")
            if b_data.get('link'): st.markdown(f"🔗 [Store / Website Link öffnen]({b_data['link']})")
            if b_data.get('rules'): st.markdown(f"<div class='rules-blue-box'>📜 <b>Turnier-Regeln:</b> {b_data['rules']}</div>", unsafe_allow_html=True)

        # 1. WINNERS BRACKET ANZEIGEN
        st.markdown("### 📊 Winner Bracket (Ungeschlagen)")
        rounds = b_data["rounds"]
        cols = st.columns(len(rounds))
        for r_idx, r_matches in enumerate(rounds):
            with cols[r_idx]:
                r_title = f"Runde {r_idx+1}" if r_idx < len(rounds)-1 else "🏆 Winner Finale"
                st.markdown(f"#### {r_title}")
                for m in r_matches:
                    p1, p2, winner = m['p1'], m['p2'], m.get('winner')
                    p1_c = "bracket-node-winner" if winner == p1 and p1 != "TBD" else ""
                    p2_c = "bracket-node-winner" if winner == p2 and p2 != "TBD" else ""
                    st.markdown(f"""
                    <div class="bracket-node">
                        <div class="{p1_c}" style="padding: 4px; border-radius: 4px;">👤 <b>{p1}</b></div>
                        <div style="text-align: center; color: #64748b; font-size: 0.8em; margin: 2px 0;">VS</div>
                        <div class="{p2_c}" style="padding: 4px; border-radius: 4px;">👤 <b>{p2}</b></div>
                    </div>
                    """, unsafe_allow_html=True)

        # 2. LOSERS BRACKET ANZEIGEN (BEI DOUBLE ELIMINATION)
        if b_data.get("type") == "double" and b_data.get("losers_rounds"):
            st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
            st.markdown("### 💀 Losers Bracket (1 Niederlage — Kampf um die 2. Chance)")
            l_rounds = b_data["losers_rounds"]
            l_cols = st.columns(len(l_rounds))
            for lr_idx, lr_matches in enumerate(l_rounds):
                with l_cols[lr_idx]:
                    st.markdown(f"#### L-Runde {lr_idx+1}")
                    for m in lr_matches:
                        p1, p2, winner = m['p1'], m['p2'], m.get('winner')
                        p1_c = "bracket-node-winner" if winner == p1 and p1 != "TBD" else ""
                        p2_c = "bracket-node-winner" if winner == p2 and p2 != "TBD" else ""
                        st.markdown(f"""
                        <div class="bracket-node bracket-node-loser">
                            <div class="{p1_c}" style="padding: 4px; border-radius: 4px;">👤 <b>{p1}</b></div>
                            <div style="text-align: center; color: #f59e0b; font-size: 0.8em; margin: 2px 0;">VS</div>
                            <div class="{p2_c}" style="padding: 4px; border-radius: 4px;">👤 <b>{p2}</b></div>
                        </div>
                        """, unsafe_allow_html=True)

            # GRAND FINALS
            st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
            st.markdown("### 👑 GRAND FINALS")
            gf = b_data.get("grand_final", {})
            gf_reset = b_data.get("grand_final_reset", {})
            
            gf_cols = st.columns(2)
            with gf_cols[0]:
                st.markdown("#### 🥇 Grand Final (Match 1)")
                st.write(f"**{gf.get('p1', 'TBD')}** (Winner Champ) vs **{gf.get('p2', 'TBD')}** (Loser Champ)")
            with gf_cols[1]:
                st.markdown("#### 🔄 Grand Final Reset (Entscheidungsspiel)")
                if gf_reset.get("active"):
                    st.warning("⚠️ BRACKET RESET! Da der Losers Champ Match 1 gewonnen hat, entscheidet dieses Match den Gesamtsieg!")
                    st.write(f"**{gf_reset.get('p1', 'TBD')}** vs **{gf_reset.get('p2', 'TBD')}**")
                else:
                    st.caption("Wird nur aktiviert, wenn der Losers-Bracket Champ das erste Finalspiel gewinnt.")

        st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
        st.markdown("### ✏️ Match-Ergebnisse eintragen")
        
        # Formular-Eingabe Winner Matches
        for r_idx, r_matches in enumerate(rounds):
            st.markdown(f"#### Winner Round {r_idx+1}")
            for m_idx, m in enumerate(r_matches):
                p1, p2 = m['p1'], m['p2']
                if p1 in ["TBD", "BYE (Freilos)"] or p2 in ["TBD", "BYE (Freilos)"]: continue
                
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    c1.write(f"Match **{m['id']}**: **{p1}** vs **{p2}**")
                    if m.get('winner'): c1.success(f"Sieger: {m['winner']}")
                    
                    opts = ["- Noch offen -", p1, p2]
                    curr_idx = opts.index(m['winner']) if m.get('winner') in opts else 0
                    new_w = c2.selectbox("Sieger wählen", opts, index=curr_idx, key=f"sel_{b_key}_w_{r_idx}_{m_idx}")
                    
                    if c2.button("Ergebnis Speichern", key=f"btn_{b_key}_w_{r_idx}_{m_idx}"):
                        m['winner'] = None if new_w == "- Noch offen -" else new_w
                        update_bracket_advancements(b_data)
                        if b_data.get("champion"):
                            add_news(db, f"👑 CHAMPION GEKRÖNT: {b_data['champion']}", 
                                     f"<b>{b_data['champion']}</b> hat soeben das Turnier <span style='color:#00f0ff;'><b>{b_data['game_name']}</b></span> gewonnen!", 
                                     category="BRACKET", custom_color="#f59e0b")
                        update_db()
                        st.success("Ergebnis aktualisiert!")
                        st.rerun()

        # Formular-Eingabe Losers Matches
        if b_data.get("type") == "double" and b_data.get("losers_rounds"):
            st.markdown("#### 💀 Losers Round Matches")
            for lr_idx, lr_matches in enumerate(b_data["losers_rounds"]):
                for m_idx, m in enumerate(lr_matches):
                    p1, p2 = m['p1'], m['p2']
                    if p1 in ["TBD", "BYE (Freilos)"] or p2 in ["TBD", "BYE (Freilos)"]: continue
                    
                    with st.container(border=True):
                        c1, c2 = st.columns([2, 1])
                        c1.write(f"Match **{m['id']}**: **{p1}** vs **{p2}**")
                        if m.get('winner'): c1.success(f"Sieger: {m['winner']}")
                        opts = ["- Noch offen -", p1, p2]
                        curr_idx = opts.index(m['winner']) if m.get('winner') in opts else 0
                        new_w = c2.selectbox("Sieger wählen", opts, index=curr_idx, key=f"sel_{b_key}_l_{lr_idx}_{m_idx}")
                        if c2.button("Ergebnis Speichern", key=f"btn_{b_key}_l_{lr_idx}_{m_idx}"):
                            m['winner'] = None if new_w == "- Noch offen -" else new_w
                            update_bracket_advancements(b_data)
                            update_db()
                            st.rerun()

            # Formular-Eingabe Grand Finals
            st.markdown("#### 🏆 Grand Finals Matches")
            gf = b_data.get("grand_final", {})
            if gf.get("p1") != "TBD" and gf.get("p2") != "TBD":
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    c1.write(f"Grand Final: **{gf['p1']}** vs **{gf['p2']}**")
                    opts = ["- Noch offen -", gf['p1'], gf['p2']]
                    curr_idx = opts.index(gf['winner']) if gf.get('winner') in opts else 0
                    new_w = c2.selectbox("Sieger wählen", opts, index=curr_idx, key=f"sel_gf_{b_key}")
                    if c2.button("Grand Final Speichern", key=f"btn_gf_{b_key}"):
                        gf['winner'] = None if new_w == "- Noch offen -" else new_w
                        update_bracket_advancements(b_data)
                        if b_data.get("champion"):
                            add_news(db, f"👑 CHAMPION GEKRÖNT: {b_data['champion']}", f"<b>{b_data['champion']}</b> hat das Turnier <b>{b_data['game_name']}</b> gewonnen!", category="BRACKET", custom_color="#f59e0b")
                        update_db()
                        st.rerun()

            gf_reset = b_data.get("grand_final_reset", {})
            if gf_reset.get("active"):
                with st.container(border=True):
                    c1, c2 = st.columns([2, 1])
                    c1.write(f"Grand Final RESET: **{gf_reset['p1']}** vs **{gf_reset['p2']}**")
                    opts = ["- Noch offen -", gf_reset['p1'], gf_reset['p2']]
                    curr_idx = opts.index(gf_reset['winner']) if gf_reset.get('winner') in opts else 0
                    new_w = c2.selectbox("Sieger wählen", opts, index=curr_idx, key=f"sel_gf_reset_{b_key}")
                    if c2.button("Reset-Match Speichern", key=f"btn_gf_reset_{b_key}"):
                        gf_reset['winner'] = None if new_w == "- Noch offen -" else new_w
                        update_bracket_advancements(b_data)
                        if b_data.get("champion"):
                            add_news(db, f"👑 CHAMPION GEKRÖNT: {b_data['champion']}", f"<b>{b_data['champion']}</b> hat das Reset-Match gewonnen!", category="BRACKET", custom_color="#f59e0b")
                        update_db()
                        st.rerun()

    with tab_double:
        render_bracket_view(brackets_data.get("double"), "doub")

    with tab_single:
        render_bracket_view(brackets_data.get("single"), "sing")

# ------------------------------------------------------------------------------
# 6. KING OF THE HILL
# ------------------------------------------------------------------------------
elif page == "👑 King of the Hill":
    st.title("👑 KING OF THE HILL")
    tab_koth_active, tab_koth_create, tab_koth_stats = st.tabs(["🔥 ÜBERSICHT", "➕ NEUES KOTH-SPIEL & THRON GRÜNDEN", "📊 KOTH STATISTIKEN"])
    games = db.get("games", {})
    player_list = list(db["players"].keys())

    with tab_koth_create:
        st.subheader("➕ Neues KotH-Spiel erstellen & Thron beanspruchen")
        if not player_list: st.warning("Bitte erstelle zuerst Spieler im Admin-Bereich!")
        else:
            with st.form("koth_create_game_form", clear_on_submit=True):
                creator = st.selectbox("Ersteller / Erster König:", player_list)
                g_name = st.text_input("Spielname eingeben:")
                c1, c2 = st.columns(2)
                match_format = c1.selectbox("Wettkampf-Format", ["Best of 1 (Bo1)", "Best of 3 (Bo3)", "Best of 5 (Bo5)", "Best of 7 (Bo7)"])
                custom_cover = c2.text_input("Custom Cover Bild-URL / Steam-Link (optional):")
                g_link_input = st.text_input("Custom Store / Website-Link (optional):")
                rules_comment = st.text_area("Herausforderungs-Regeln / Modus / Waffen & Maps:")
                
                if st.form_submit_button("Werde König"):
                    if g_name:
                        cover_url, store_link = fetch_steam_info(g_name, custom_cover)
                        if g_link_input.strip(): store_link = g_link_input.strip()
                            
                        new_id = str(len(games) + 1)
                        games[new_id] = {"name": g_name, "creator": creator, "custom_cover": cover_url, "link": store_link, "format": match_format, "rules": rules_comment}
                        db.setdefault("koth", {})[new_id] = {"king": creator, "streak": 1, "history": [{"timestamp": get_now_str(), "defender": creator, "challenger": "Thron-Gründung", "winner": creator, "format": match_format}]}
                        add_news(db, f"👑 Neuer Thron errichtet: {g_name}", f"<b>{creator}</b> hat den Thron für <span style='color:#00f0ff;'><b>{g_name}</b></span> errichtet!", category="KOTH")
                        update_db()
                        st.success(f"KotH Arena für '{g_name}' eröffnet!")
                        st.rerun()

    with tab_koth_active:
        if not games: st.info("Noch keine KotH-Spiele vorhanden.")
        else:
            cols = st.columns(min(len(games), 4))
            for idx, (g_id, g_info) in enumerate(games.items()):
                k_data = db["koth"].get(g_id, {"king": None, "streak": 0})
                cover = g_info.get("custom_cover") or "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER"
                with cols[idx % len(cols)]:
                    with st.container(border=True):
                        st.image(cover, use_container_width=True)
                        st.markdown(f"### {g_info['name']}")
                        st.markdown(f"<div class='king-highlight-box'>👑 KING: <b>{k_data['king'] or 'Niemand'}</b><br>🔥 Streak: <b>{k_data['streak']} Siege</b></div>", unsafe_allow_html=True)
                        if g_info.get("rules"): st.markdown(f"<div class='rules-blue-box'>📜 <b>Regeln:</b> {g_info['rules']}</div>", unsafe_allow_html=True)

            st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
            selected_g_id = st.selectbox("HERAUSFORDERUNGS-WAHL", list(games.keys()), format_func=lambda x: f"⚔️ {games[x]['name']} — ({games[x].get('rules', 'Keine Sonderregeln')})", label_visibility="collapsed")
            
            g_info = games[selected_g_id]
            k_data = db["koth"].setdefault(selected_g_id, {"king": None, "streak": 0, "history": []})
            
            col_img, col_detail = st.columns([1, 2])
            with col_img: st.image(g_info.get("custom_cover"), use_container_width=True)
            with col_detail:
                st.markdown(f"## {g_info['name']}")
                st.write(f"Gründer: `{g_info.get('creator', 'Admin')}` | Format: **{g_info.get('format', 'Bo3')}**")
                if g_info.get('link'): st.markdown(f"🔗 [Store / Website Link öffnen]({g_info['link']})")
                if g_info.get('rules'): st.markdown(f"<div class='rules-blue-box'>📜 <b>Festgelegte Regeln:</b> {g_info['rules']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='king-highlight-box' style='font-size: 1.25em;'>👑 AKTUELLER KÖNIG: <b>{k_data['king'] or 'Thron unbesetzt'}</b> (Streak: <b>{k_data['streak']} Siege</b>)</div>", unsafe_allow_html=True)

            if len(player_list) >= 2:
                current_king = k_data['king']
                c1, c2 = st.columns(2)
                if current_king:
                    defender = current_king
                    c1.text_input("King (Verteidiger)", value=defender, disabled=True)
                    challenger = c2.selectbox("Herausforderer wählen", [p for p in player_list if p != defender], key=f"c_sel_{selected_g_id}")
                else:
                    defender = c1.selectbox("Spieler 1", player_list, key=f"d_sel_{selected_g_id}")
                    challenger = c2.selectbox("Spieler 2", [p for p in player_list if p != defender], key=f"c_sel_{selected_g_id}")

                with st.form(f"koth_challenge_form_{selected_g_id}", clear_on_submit=True):
                    winner = st.selectbox("Sieger des Matches eintragen", [defender, challenger])
                    if st.form_submit_button("Match-Ergebnis Speichern"):
                        old_king = k_data["king"]
                        if winner == k_data["king"]:
                            k_data["streak"] += 1
                            news_html = f"<b>{winner}</b> hat seinen Thron in <span style='color:#00f0ff;'><b>{g_info['name']}</b></span> verteidigt!"
                        else:
                            k_data["king"] = winner
                            k_data["streak"] = 1
                            news_html = f"👑 <span style='color:#ef4444;'><b>ENTTHRONUNG!</b></span> <b>{winner}</b> ist neuer King in <span style='color:#00f0ff;'><b>{g_info['name']}</b></span>!"
                        
                        k_data.setdefault("history", []).append({"timestamp": get_now_str(), "defender": defender, "challenger": challenger, "winner": winner, "format": g_info.get("format", "Bo3")})
                        add_news(db, f"⚔️ Thronkampf in {g_info['name']}", news_html, category="KOTH")
                        update_db()
                        st.success("Ergebnis gespeichert!")
                        st.rerun()

    with tab_koth_stats:
        st.subheader("📊 King of the Hill Leaderboards")
        total_wins = {}
        for g_id, k_info in db.get("koth", {}).items():
            for h in k_info.get("history", []):
                w = h.get("winner")
                if w and w != "Thron-Gründung": total_wins[w] = total_wins.get(w, 0) + 1
        
        if total_wins:
            for rank_idx, (p_name, w_count) in enumerate(sorted(total_wins.items(), key=lambda x: x[1], reverse=True)):
                st.markdown(f"<div class='leaderboard-card'><b>Rang #{rank_idx+1}: {p_name}</b> — <span style='color: #00f0ff;'>{w_count} Siege</span></div>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 7. CHALLENGES
# ------------------------------------------------------------------------------
elif page == "🎯 Challenges":
    st.title("🎯 CHALLENGES")
    tab1, tab2, tab3 = st.tabs(["🔥 Aktive Challenges", "➕ Challenge Erstellen", "📊 Challenge Statistiken"])
    challenge_games = db.setdefault("challenge_games", {})
    player_list = list(db["players"].keys())
    
    with tab2:
        st.subheader("➕ Neues Challenge-Spiel registrieren")
        cg_name = st.text_input("Spielname eingeben")
        cg_cover_custom = st.text_input("Custom Cover Bild-URL / Steam-Link (optional):")
        if st.button("Spiel Speichern") and cg_name:
            cover_url, _ = fetch_steam_info(cg_name, cg_cover_custom)
            challenge_games[str(len(challenge_games) + 1)] = {"name": cg_name, "cover": cover_url}
            update_db()
            st.success("Spiel gespeichert!")
            st.rerun()

        st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
        if challenge_games and player_list:
            with st.form("create_challenge_form", clear_on_submit=True):
                creator = st.selectbox("Ersteller", player_list)
                cg_id = st.selectbox("Spiel", list(challenge_games.keys()), format_func=lambda x: challenge_games[x]["name"])
                c_title = st.text_input("Challenge Titel")
                c_custom_cover = st.text_input("Spezifisches Cover-Bild (optional)")
                c_desc = st.text_area("Detaillierte Beschreibung / Regeln")
                c_difficulty = st.select_slider("Schwierigkeitsgrad", options=["Leicht", "Mittel", "Schwer", "Extrem", "Unmöglich"])
                
                if st.form_submit_button("Challenge Veröffentlichen") and c_title and c_desc:
                    db.setdefault("challenges", []).append({
                        "id": len(db.get("challenges", [])) + 1, "creator": creator, "challenge_game_id": cg_id,
                        "title": c_title, "custom_cover": c_custom_cover.strip(), "description": c_desc,
                        "difficulty": c_difficulty, "timestamp": get_now_str(), "completions": []
                    })
                    add_news(db, f"🎯 Neue Challenge: {c_title}", f"<b>{creator}</b> hat eine neue Challenge für <b>{challenge_games[cg_id]['name']}</b> veröffentlicht!", category="CHALLENGE")
                    update_db()
                    st.success("Veröffentlicht!")
                    st.rerun()

    with tab1:
        challenges = db.get("challenges", [])
        if not challenges: st.info("Noch keine Challenges vorhanden.")
        else:
            diff_map = {"Leicht": "diff-leicht", "Mittel": "diff-mittel", "Schwer": "diff-schwer", "Extrem": "diff-extrem", "Unmöglich": "diff-unmoeglich"}
            for c in reversed(challenges):
                cg_info = challenge_games.get(c.get("challenge_game_id"), {"name": "Allgemein", "cover": "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER"})
                cover = c.get("custom_cover") or cg_info.get("cover")
                
                st.markdown(f"""
                <div class="full-challenge-card">
                    <div class="challenge-flex-container">
                        <img src="{cover}" class="challenge-img">
                        <div class="challenge-body">
                            <h3 style="margin: 0 0 6px 0; color: #00f0ff !important;">{c['title']} <span style="font-size: 0.85em; color: #94a3b8;">({cg_info['name']})</span></h3>
                            <div class="creator-box">🛠️ ERSTELLER: {c['creator']}</div><br>
                            <span class="{diff_map.get(c['difficulty'], 'diff-mittel')}">{c['difficulty']}</span> | {c['timestamp']}
                            <p style="margin-top: 10px; color: #e2e8f0;">{c['description']}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.markdown("#### 🌟 Absolvierte Versuche")
                    for comp in c.get("completions", []):
                        st.write(f"✅ **{comp['player']}** | Rating: **{comp['rating']} ⭐** | Kommentar: *\"{comp['comment']}\"*")
                    
                    with st.expander("Eintragen: Challenge geschafft!"):
                        if player_list:
                            with st.form(f"complete_c_{c['id']}", clear_on_submit=True):
                                p_name = st.selectbox("Dein Name", player_list, key=f"c_p_{c['id']}")
                                rating = st.slider("Rating (1-5 Stars)", 1, 5, 5, key=f"c_r_{c['id']}")
                                comment = st.text_input("Beweis-Link / Kommentar", key=f"c_c_{c['id']}")
                                if st.form_submit_button("Als Geschafft Markieren"):
                                    c.setdefault("completions", []).append({"player": p_name, "rating": rating, "comment": comment, "timestamp": get_now_str()})
                                    add_news(db, f"🏆 Challenge Meisterschaft!", f"<b>{p_name}</b> hat <b>{c['title']}</b> absolviert!", category="CHALLENGE")
                                    update_db()
                                    st.success("Gespeichert!")
                                    st.rerun()

    with tab3: st.subheader("📊 Challenge Statistiken")

# ------------------------------------------------------------------------------
# 8. EINSPRUCH & ANTRÄGE
# ------------------------------------------------------------------------------
elif page == "📩 Einspruch & Anträge":
    st.title("📩 ANTRÄGE & EINSPRÜCHE")
    with st.form("appeal_form", clear_on_submit=True):
        player_list = list(db["players"].keys())
        sender = st.selectbox("Antragsteller", player_list if player_list else ["-"])
        target = st.selectbox("Betroffener Spieler", player_list if player_list else ["-"])
        reason = st.text_area("Begründung")
        if st.form_submit_button("Einreichen") and sender and reason:
            db["appeals"].append({"id": len(db["appeals"]) + 1, "timestamp": get_now_str(), "sender": sender, "target": target, "reason": reason, "status": "OFFEN", "defense": ""})
            update_db()
            st.success("Eingereicht.")
            st.rerun()

# ------------------------------------------------------------------------------
# 9. ADMIN-BEREICH (MIT FULL NEWS-BEARBEITUNG & DOUBLE BRACKET CREATOR)
# ------------------------------------------------------------------------------
elif page == "⚙️ Admin-Bereich":
    st.title("⚙️ ADMIN CONTROL PANEL")
    admin_pw = st.secrets.get("ADMIN_PASSWORD", "zm1234")
    input_pw = st.text_input("Admin-Passwort eingeben", type="password")
    
    if input_pw != admin_pw:
        st.error("Zugriff verweigert.")
    else:
        st.success("Authentifiziert.")
        tab_admin = st.tabs(["📰 News", "🏆 Turniere", "👑 KotH", "🎯 Challenges", "👥 Spieler", "📩 Einsprüche", "📊 Logs", "💾 Backup"])
        
        # TAB 1: NEWS BEARBEEITEN & POSTEN
        with tab_admin[0]:
            st.subheader("📰 News & Ankündigungen Verwalten")
            with st.expander("➕ Eigene Admin-News posten", expanded=True):
                with st.form("admin_create_news_form", clear_on_submit=True):
                    news_title = st.text_input("News Überschrift")
                    news_content = st.text_area("Inhalt")
                    news_cat = st.selectbox("Kategorie", ["ADMIN", "GENERAL", "KOTH", "CHALLENGE", "BRACKET"])
                    custom_color = st.selectbox("Farbe", ["#a855f7 (Purple)", "#00f0ff (Cyan)", "#f59e0b (Gold)", "#ef4444 (Rot)"])
                    if st.form_submit_button("Veröffentlichen") and news_title and news_content:
                        add_news(db, news_title, news_content, category=news_cat, custom_color=custom_color.split(" ")[0])
                        update_db()
                        st.success("Veröffentlicht!")
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

        # TAB 2: TURNIER VERWALTUNG (DOUBLE ELIMINATION ZUERST)
        with tab_admin[1]:
            st.subheader("🏆 Turnier & Bracket Verwaltung")
            player_list = list(db["players"].keys())
            
            sub_t2, sub_t1 = st.tabs(["⚡ Double Elimination", "🔥 Single Elimination"])
            
            def render_admin_bracket_creator(b_type_name, b_key):
                st.markdown(f"#### 1. Neues {b_type_name} Turnier erstellen")
                with st.form(f"create_{b_key}_bracket_form"):
                    t_game = st.text_input("Turnier-Spielname", placeholder="z.B. Rocket League, Tekken 8")
                    c1, c2 = st.columns(2)
                    custom_cover = c1.text_input("Custom Cover Bild-URL / Steam-Link (optional):")
                    t_link = c2.text_input("Custom Store / Website-Link (optional):")
                    t_rules = st.text_area("Turnier-Regeln & Modus:")
                    selected_players = st.multiselect("Teilnehmende Spieler wählen", player_list, default=player_list)
                    
                    if st.form_submit_button(f"🎲 {b_type_name} Turnier Starten"):
                        if not t_game or len(selected_players) < 2:
                            st.error("Bitte Spielnamen eingeben und mindestens 2 Spieler wählen!")
                        else:
                            cover_url, store_link = fetch_steam_info(t_game, custom_cover)
                            if t_link.strip(): store_link = t_link.strip()
                            
                            new_b = generate_bracket_data(t_game, selected_players, cover_url, t_rules, store_link, b_type=b_key)
                            db.setdefault("brackets", {})[b_key] = new_b
                            add_news(db, f"🏆 Neues {b_type_name} Turnier: {t_game}", f"Das Turnier in <b>{t_game}</b> wurde gestartet! {len(selected_players)} Teilnehmer.", category="GENERAL", custom_color="#00f0ff")
                            update_db()
                            st.success("Turnier erstellt!")
                            st.rerun()

                st.markdown("---")
                st.markdown(f"#### 🛠️ Aktuelles {b_type_name} Bracket Override & Manuelle Anpassung")
                curr_b = db.get("brackets", {}).get(b_key)
                if not curr_b:
                    st.info("Kein aktives Bracket vorhanden.")
                else:
                    st.write(f"Bearbeite: **{curr_b['game_name']}**")
                    for r_idx, r_matches in enumerate(curr_b["rounds"]):
                        with st.expander(f"✏️ Override - Winner Runde {r_idx+1}"):
                            for m_idx, m in enumerate(r_matches):
                                st.write(f"**Match {m['id']}**")
                                c1, c2, c3 = st.columns(3)
                                edit_p1 = c1.text_input("Spieler 1", value=m['p1'], key=f"ov_p1_{b_key}_{r_idx}_{m_idx}")
                                edit_p2 = c2.text_input("Spieler 2", value=m['p2'], key=f"ov_p2_{b_key}_{r_idx}_{m_idx}")
                                edit_w = c3.text_input("Gewinner", value=m.get('winner') or "", key=f"ov_w_{b_key}_{r_idx}_{m_idx}")
                                
                                if st.button("Speichern", key=f"btn_ov_{b_key}_{r_idx}_{m_idx}"):
                                    m['p1'] = edit_p1
                                    m['p2'] = edit_p2
                                    m['winner'] = edit_w if edit_w.strip() else None
                                    update_bracket_advancements(curr_b)
                                    update_db()
                                    st.success("Match angepasst!")
                                    st.rerun()

                    if st.button(f"🗑️ {b_type_name} Turnier Zurücksetzen", key=f"del_{b_key}_btn"):
                        db["brackets"][b_key] = None
                        update_db()
                        st.success("Turnier gelöscht!")
                        st.rerun()

            with sub_t2: render_admin_bracket_creator("Double Elimination", "double")
            with sub_t1: render_admin_bracket_creator("Single Elimination", "single")

        # TAB 3: KotH
        with tab_admin[2]:
            st.subheader("👑 KotH Verwaltung")
            games = db.get("games", {})
            for g_id, g in list(games.items()):
                with st.container(border=True):
                    st.write(f"ID {g_id}: **{g['name']}**")
                    if st.button("Löschen", key=f"del_koth_{g_id}"):
                        del games[g_id]
                        update_db()
                        st.rerun()

        # TAB 4: CHALLENGE ADMIN
        with tab_admin[3]: st.subheader("🎯 Challenge Verwaltung")

        # TAB 5: SPIELER ADMIN
        with tab_admin[4]:
            st.subheader("👥 Spieler verwalten")
            c1, c2 = st.columns(2)
            new_p = c1.text_input("Neuer Spieler Name")
            if c1.button("Spieler Anlegen") and new_p:
                if new_p not in db["players"]:
                    db["players"][new_p] = {"created_at": get_now_str()}
                    update_db()
                    st.rerun()
            del_p = c2.selectbox("Spieler entfernen", ["-"] + list(db["players"].keys()))
            if c2.button("Spieler Löschen") and del_p != "-":
                del db["players"][del_p]
                update_db()
                st.rerun()

        # TAB 6-8: RESTLICHE TABS
        with tab_admin[5]: st.dataframe(db.get("appeals", []))
        with tab_admin[6]: st.dataframe(db["audit_logs"])
        with tab_admin[7]:
            st.download_button("data.json herunterladen", data=json.dumps(db, indent=2, ensure_ascii=False), file_name="data_backup.json")
