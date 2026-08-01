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
# 1. KONFIGURATION & STYLES (MARTIAL DARK METAL & INLINE MATCH BUTTONS)
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
    }
    
    section[data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 2px solid #00f0ff !important;
    }

    .glowing-divider {
        height: 4px;
        background: linear-gradient(90deg, #00f0ff 0%, #f59e0b 50%, #00f0ff 100%);
        box-shadow: 0 0 12px #00f0ff;
        margin: 25px 0;
        border-radius: 2px;
    }

    .bracket-match-card {
        background: #111522;
        border: 1.5px solid #1e293b;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 15px;
        position: relative;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    
    .bracket-match-card-active {
        border: 2px solid #00f0ff !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.35) !important;
        background: #151c2d !important;
    }

    .bracket-slot {
        padding: 6px 10px;
        margin: 3px 0;
        border-radius: 4px;
        background: #182030;
        font-size: 0.95rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .slot-placeholder {
        color: #64748b;
        font-style: italic;
        background: rgba(30, 41, 59, 0.4);
        border: 1px dashed #334155;
    }

    .slot-bye {
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.3);
    }

    .slot-winner {
        color: #10b981;
        font-weight: 800;
        background: rgba(16, 185, 129, 0.15);
        border: 1.5px solid #10b981;
    }

    .simple-next-banner {
        border-left: 5px solid #00f0ff;
        background: #111827;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 25px;
        border-top: 1px solid #1e293b;
        border-right: 1px solid #1e293b;
        border-bottom: 1px solid #1e293b;
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

    .news-card {
        border-left: 5px solid #00f0ff;
        background: #111520;
        padding: 16px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. PERSISTENZ ENGINE
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

def load_data():
    if not os.path.exists(DATA_FILE):
        default = get_default_data()
        save_data(default, sync=False)
        return default
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            data.setdefault("brackets", {"single": None, "double": None})
            return data
    except Exception:
        return get_default_data()

def save_data(data, sync=True):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
    if custom_cover and custom_cover.strip(): return custom_cover.strip(), ""
    if not game_name: return "https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER", ""
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

def get_round_name(r_index, total_rounds, is_loser=False):
    if is_loser:
        if r_index == total_rounds - 1: return "🏆 Loser Finale"
        return f"L-Runde {r_index + 1}"
    
    rounds_left = total_rounds - r_index
    if rounds_left == 1: return "🏆 Winner Finale"
    if rounds_left == 2: return "Halbfinale"
    if rounds_left == 3: return "Viertelfinale"
    return f"Qualifikation {r_index + 1}"

# ------------------------------------------------------------------------------
# 3. KORREKTE DOUBLE-ELIMINATION ENGINE (PERFEKTE SYMMETRIE FÜR 6 SPIELER)
# ------------------------------------------------------------------------------
def generate_bracket_data(game_name, players, cover, rules, link, b_type="single"):
    n = len(players)
    if n < 2: return None
    
    next_pow = 1 << (n - 1).bit_length() if n > 1 else 2
    if next_pow < 2: next_pow = 2
    
    num_byes = next_pow - n
    shuffled = players.copy()
    random.shuffle(shuffled)
    
    # Symmetrisches Freilos-Seeding (Freilos an 1. und 4. Position für 6 Spieler)
    slots = ["TBD"] * next_pow
    bye_positions = []
    if num_byes == 1: bye_positions = [1]
    elif num_byes == 2: bye_positions = [1, next_pow - 1] # Top (W1M1) & Bottom (W1M4)
    elif num_byes == 3: bye_positions = [1, next_pow - 1, 3]
    else: bye_positions = list(range(1, num_byes * 2, 2))

    for pos in bye_positions: slots[pos] = "BYE (Freilos)"
    for p in shuffled:
        for idx in range(len(slots)):
            if slots[idx] == "TBD":
                slots[idx] = p
                break

    num_rounds = int(math.log2(next_pow))
    winner_rounds = []
    
    # WINNER RUNDE 1
    r1_matches = []
    for i in range(0, len(slots), 2):
        p1, p2 = slots[i], slots[i+1]
        winner = None
        if p1 == "BYE (Freilos)": winner = p2
        elif p2 == "BYE (Freilos)": winner = p1
        m_id = f"W1M{len(r1_matches)+1}"
        r1_matches.append({"id": m_id, "p1": p1, "p2": p2, "winner": winner, "p1_origin": None, "p2_origin": None})
    winner_rounds.append(r1_matches)
    
    # WINNER FOLGERUNDEN
    for r in range(2, num_rounds + 1):
        prev_matches = winner_rounds[-1]
        r_matches = []
        for m_idx in range(len(prev_matches) // 2):
            m1_id = prev_matches[m_idx * 2]["id"]
            m2_id = prev_matches[m_idx * 2 + 1]["id"]
            m_id = f"W{r}M{m_idx+1}"
            r_matches.append({
                "id": m_id, 
                "p1": "TBD", "p2": "TBD", 
                "p1_origin": f"Gewinner {m1_id}", "p2_origin": f"Gewinner {m2_id}",
                "winner": None
            })
        winner_rounds.append(r_matches)
        
    bracket = {
        "game_name": game_name, "cover": cover, "rules": rules, "link": link,
        "type": b_type, "created_at": get_now_str(), "champion": None, "rounds": winner_rounds
    }

    # KORREKTES 3-RUNDEN LOSER-BRACKET FÜR 6 SPIELER
    if b_type == "double":
        losers_rounds = []
        
        # L-Runde 1: Einziges echtes Spiel der W1-Verlierer (z.B. Sascha vs. Alexander)
        losers_rounds.append([{
            "id": "L1M1", "p1": "TBD", "p2": "TBD",
            "p1_origin": "Verlierer W1M2", "p2_origin": "Verlierer W1M3", "winner": None
        }])
        
        # L-Runde 2: Die beiden Verlierer des Winner-Halbfinals treffen auf den L1M1 Sieger!
        losers_rounds.append([
            {"id": "L2M1", "p1": "TBD", "p2": "TBD", "p1_origin": "Sieger L1M1", "p2_origin": "Verlierer W2M1", "winner": None},
            {"id": "L2M2", "p1": "TBD", "p2": "BYE (Freilos)", "p1_origin": "Verlierer W2M2", "p2_origin": "Freilos", "winner": None}
        ])
        
        # L-Runde 3 (Loser Finale): Überlebender L2 vs Verlierer Winner Finale (W3M1)
        losers_rounds.append([{
            "id": "L3M1", "p1": "TBD", "p2": "TBD",
            "p1_origin": "Sieger L2M1", "p2_origin": "Verlierer W3M1", "winner": None
        }])

        bracket["losers_rounds"] = losers_rounds
        bracket["grand_final"] = {
            "id": "GF_M1", "p1": "TBD", "p2": "TBD", 
            "p1_origin": "Winner Champ", "p2_origin": "Loser Champ", "winner": None
        }
        bracket["grand_final_reset"] = {
            "id": "GF_RESET", "p1": "TBD", "p2": "TBD", 
            "p1_origin": "Winner Champ", "p2_origin": "Loser Champ", "winner": None, "active": False
        }

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
            w = match.get("winner")
            target_match = next_round[m_idx // 2]
            slot_key = "p1" if (m_idx % 2 == 0) else "p2"
            
            if w: target_match[slot_key] = w
            else: target_match[slot_key] = "TBD"

    if b_type == "single":
        final_m = rounds[-1][0]
        if final_m.get("winner"): bracket["champion"] = final_m["winner"]

    # 2. DOUBLE ELIMINATION ADVANCEMENT
    if b_type == "double":
        l_rounds = bracket.get("losers_rounds", [])
        
        for r_idx, r_matches in enumerate(rounds):
            for m in r_matches:
                w = m.get("winner")
                if w:
                    loser = m["p2"] if m["p1"] == w else m["p1"]
                    if loser not in ["TBD", "BYE (Freilos)"]:
                        for lr in l_rounds:
                            for lm in lr:
                                if lm["p1_origin"] == f"Verlierer {m['id']}": lm["p1"] = loser
                                if lm["p2_origin"] == f"Verlierer {m['id']}": lm["p2"] = loser

        for lr_idx, curr_lr in enumerate(l_rounds):
            for lm in curr_lr:
                p1, p2 = lm["p1"], lm["p2"]
                
                # Auto-Advance NUR bei echtem Freilos (Niemals bei TBD!)
                if p1 not in ["TBD", "BYE (Freilos)"] and p2 == "BYE (Freilos)":
                    lm["winner"] = p1
                elif p2 not in ["TBD", "BYE (Freilos)"] and p1 == "BYE (Freilos)":
                    lm["winner"] = p2
                elif p1 == "TBD" or p2 == "TBD":
                    pass
                    
                w = lm.get("winner")
                if w and lr_idx < len(l_rounds) - 1:
                    for next_lr in l_rounds[lr_idx + 1:]:
                        for next_lm in next_lr:
                            if next_lm["p1_origin"] == f"Sieger {lm['id']}": next_lm["p1"] = w
                            if next_lm["p2_origin"] == f"Sieger {lm['id']}": next_lm["p2"] = w

        gf = bracket.setdefault("grand_final", {"id": "GF_M1", "p1": "TBD", "p2": "TBD", "winner": None})
        w_champ = rounds[-1][0].get("winner")
        l_champ = l_rounds[-1][0].get("winner") if l_rounds else None
        
        if w_champ: gf["p1"] = w_champ
        if l_champ: gf["p2"] = l_champ

        gf_w = gf.get("winner")
        gf_reset = bracket.setdefault("grand_final_reset", {"id": "GF_RESET", "p1": "TBD", "p2": "TBD", "winner": None, "active": False})

        if gf_w:
            if gf_w == gf["p1"]:
                bracket["champion"] = gf_w
                gf_reset["active"] = False
            elif gf_w == gf["p2"]:
                gf_reset["active"] = True
                gf_reset["p1"] = gf["p1"]
                gf_reset["p2"] = gf["p2"]
                if gf_reset.get("winner"): bracket["champion"] = gf_reset["winner"]

def get_current_active_matches(bracket):
    if not bracket or bracket.get("champion"): return []
    active = []
    
    for r_idx, r in enumerate(bracket["rounds"]):
        for m in r:
            p1, p2, w = m["p1"], m["p2"], m.get("winner")
            if not w and p1 not in ["TBD", "BYE (Freilos)"] and p2 not in ["TBD", "BYE (Freilos)"]:
                r_label = get_round_name(r_idx, len(bracket["rounds"]))
                active.append((r_label, m))

    if bracket.get("type") == "double" and bracket.get("losers_rounds"):
        for lr_idx, lr in enumerate(bracket["losers_rounds"]):
            for m in lr:
                p1, p2, w = m["p1"], m["p2"], m.get("winner")
                if not w and p1 not in ["TBD", "BYE (Freilos)"] and p2 not in ["TBD", "BYE (Freilos)"]:
                    r_label = get_round_name(lr_idx, len(bracket["losers_rounds"]), is_loser=True)
                    active.append((f"💀 {r_label}", m))

    if bracket.get("type") == "double":
        gf = bracket.get("grand_final", {})
        if not gf.get("winner") and gf.get("p1") not in ["TBD", "BYE (Freilos)"] and gf.get("p2") not in ["TBD", "BYE (Freilos)"]:
            active.append(("👑 Grand Final", gf))
            
        gf_reset = bracket.get("grand_final_reset", {})
        if gf_reset.get("active") and not gf_reset.get("winner"):
            active.append(("🔄 Grand Final RESET", gf_reset))

    return active

if "db" not in st.session_state: st.session_state.db = load_data()
def update_db(): save_data(st.session_state.db)
db = st.session_state.db

# ------------------------------------------------------------------------------
# 4. NAVIGATION & APP RENDER
# ------------------------------------------------------------------------------
st.sidebar.markdown("# ⚔️ COMPETUS")
st.sidebar.markdown("### MAXIMUS")
st.sidebar.caption(f"DEUTSCHLAND (BERLIN) | {get_now_str()}")
st.sidebar.markdown("<div class='glowing-divider' style='margin: 15px 0;'></div>", unsafe_allow_html=True)

page = st.sidebar.radio("NAVIGATION", ["📰 News", "🏆 Turniere & Brackets", "👑 King of the Hill", "🎯 Challenges", "⚙️ Admin-Bereich"])

# ------------------------------------------------------------------------------
# 5. TURNIERE & BRACKETS (INLINE BUTTONS DIREKT AN DEN KARTEN)
# ------------------------------------------------------------------------------
if page == "🏆 Turniere & Brackets":
    st.title("🏆 TURNIERE & BRACKETS")
    
    tab_double, tab_single = st.tabs(["⚡ Double Elimination", "🔥 Single Elimination"])
    brackets_data = db.setdefault("brackets", {"single": None, "double": None})
    
    def render_bracket_view(b_data, b_key):
        if not b_data:
            st.info("Aktuell ist kein Turnier in dieser Kategorie aktiv.")
            return

        update_bracket_advancements(b_data)
        
        # CHAMPION BANNER
        if b_data.get("champion"):
            st.markdown(f"""
            <div class="winner-champion-banner">
                <h1 style="color: #fbbf24 !important; margin: 0; font-size: 2.2em;">👑 TURNIERSIEGER 👑</h1>
                <h2 style="color: #ffffff !important; margin: 10px 0 0 0; font-size: 2.8em; text-shadow: 0 0 15px #f59e0b;">{b_data['champion']}</h2>
                <p style="color: #fde68a; font-size: 1.1em; margin-top: 5px;">Hat das Turnier <b>"{b_data['game_name']}"</b> triumphal gewonnen!</p>
            </div>
            """, unsafe_allow_html=True)

        active_matches = get_current_active_matches(b_data)
        active_match_ids = [m['id'] for _, m in active_matches]

        col_img, col_detail = st.columns([1, 2])
        with col_img: st.image(b_data.get('cover', 'https://via.placeholder.com/460x215/1e293b/00f0ff?text=KEIN+COVER'), use_container_width=True)
        with col_detail:
            st.markdown(f"## {b_data['game_name']}")
            st.caption(f"Erstellt am: {b_data['created_at']}")
            if b_data.get('rules'): st.markdown(f"<div class='rules-blue-box'>📜 <b>Turnier-Regeln:</b> {b_data['rules']}</div>", unsafe_allow_html=True)

        def render_match_box(m, is_loser=False):
            p1, p2, w = m['p1'], m['p2'], m.get('winner')
            is_active = m['id'] in active_match_ids
            active_cls = "bracket-match-card-active" if is_active else ""
            
            st.markdown(f"""
            <div class="bracket-match-card {active_cls}">
                <div style="font-size:0.75em; color:{'#f59e0b' if is_loser else '#64748b'}; font-weight:800; margin-bottom:4px;">MATCH {m['id']}</div>
            """, unsafe_allow_html=True)

            # Slot 1
            if p1 == "BYE (Freilos)":
                st.markdown('<div class="bracket-slot slot-bye"><span>🟦 Freilos</span> <span>✓</span></div>', unsafe_allow_html=True)
            elif p1 in ["TBD", "KEIN GEGNER"] or not p1:
                st.markdown(f'<div class="bracket-slot slot-placeholder"><span>📍 {m.get("p1_origin", "Warten...")}</span></div>', unsafe_allow_html=True)
            else:
                w_cls = "slot-winner" if w == p1 else ""
                st.markdown(f'<div class="bracket-slot {w_cls}"><span>👤 <b>{p1}</b></span>{" 🏆" if w == p1 else ""}</div>', unsafe_allow_html=True)

            st.markdown('<div style="text-align:center; font-size:0.7em; color:#475569; margin:1px 0;">VS</div>', unsafe_allow_html=True)

            # Slot 2
            if p2 == "BYE (Freilos)":
                st.markdown('<div class="bracket-slot slot-bye"><span>🟦 Freilos</span> <span>✓</span></div>', unsafe_allow_html=True)
            elif p2 in ["TBD", "KEIN GEGNER"] or not p2:
                st.markdown(f'<div class="bracket-slot slot-placeholder"><span>📍 {m.get("p2_origin", "Warten...")}</span></div>', unsafe_allow_html=True)
            else:
                w_cls = "slot-winner" if w == p2 else ""
                st.markdown(f'<div class="bracket-slot {w_cls}"><span>👤 <b>{p2}</b></span>{" 🏆" if w == p2 else ""}</div>', unsafe_allow_html=True)

            # INLINE SIEGER BUTTONS DIREKT AN DER KARTE! ⚡
            if is_active and not w:
                st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
                bc1, bc2 = st.columns(2)
                if bc1.button(f"🏆 {p1}", key=f"btn_inline_p1_{m['id']}"):
                    m['winner'] = p1
                    update_bracket_advancements(b_data)
                    update_db()
                    st.rerun()
                if bc2.button(f"🏆 {p2}", key=f"btn_inline_p2_{m['id']}"):
                    m['winner'] = p2
                    update_bracket_advancements(b_data)
                    update_db()
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # 1. WINNER BRACKET
        st.markdown("### 📊 Winner Bracket (Ungeschlagen)")
        rounds = b_data["rounds"]
        cols = st.columns(len(rounds))
        for r_idx, r_matches in enumerate(rounds):
            with cols[r_idx]:
                st.markdown(f"#### {get_round_name(r_idx, len(rounds))}")
                for m in r_matches: render_match_box(m, is_loser=False)

        # 2. LOSERS BRACKET
        if b_data.get("type") == "double" and b_data.get("losers_rounds"):
            st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
            st.markdown("### 💀 Losers Bracket (1 Niederlage — 2. Chance)")
            l_rounds = b_data["losers_rounds"]
            l_cols = st.columns(len(l_rounds))
            for lr_idx, lr_matches in enumerate(l_rounds):
                with l_cols[lr_idx]:
                    st.markdown(f"#### {get_round_name(lr_idx, len(l_rounds), is_loser=True)}")
                    for m in lr_matches: render_match_box(m, is_loser=True)

            # GRAND FINALS
            st.markdown("<div class='glowing-divider'></div>", unsafe_allow_html=True)
            st.markdown("### 👑 GRAND FINALS")
            gf_cols = st.columns(2)
            with gf_cols[0]:
                st.markdown("#### 🥇 Grand Final")
                render_match_box(b_data.get("grand_final", {}), is_loser=False)
            with gf_cols[1]:
                st.markdown("#### 🔄 Grand Final Reset")
                gf_reset = b_data.get("grand_final_reset", {})
                if gf_reset.get("active"):
                    st.warning("⚠️ BRACKET RESET ACTIVE!")
                    render_match_box(gf_reset, is_loser=True)
                else:
                    st.caption("Aktiviert sich nur, wenn der Loser Champ Match 1 gewinnt.")

    with tab_double: render_bracket_view(brackets_data.get("double"), "doub")
    with tab_single: render_bracket_view(brackets_data.get("single"), "sing")

# ------------------------------------------------------------------------------
# RESTLICHE TABS (NEWS, KOTH, CHALLENGES, ADMIN)
# ------------------------------------------------------------------------------
elif page == "📰 News":
    st.title("📰 ARENA NEWS")
    for item in reversed(db.get("news", [])):
        st.markdown(f"<div class='news-card'><h4>{item['title']}</h4><p>{item.get('content_html', item.get('content',''))}</p></div>", unsafe_allow_html=True)

elif page == "⚙️ Admin-Bereich":
    st.title("⚙️ ADMIN CONTROL PANEL")
    admin_pw = st.secrets.get("ADMIN_PASSWORD", "zm1234")
    if st.text_input("Admin Password", type="password") == admin_pw:
        st.success("Authentifiziert.")
        player_list = list(db["players"].keys())
        st.subheader("Neues Double Elimination Turnier starten")
        with st.form("admin_create_doub"):
            g_name = st.text_input("Spielname")
            sel_p = st.multiselect("Spieler wählen", player_list, default=player_list)
            if st.form_submit_button("Turnier Generieren") and g_name and len(sel_p) >= 2:
                db["brackets"]["double"] = generate_bracket_data(g_name, sel_p, "", "", "", b_type="double")
                update_db()
                st.success("Turnier gestartet!")
                st.rerun()
