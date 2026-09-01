import streamlit as st
import requests
import pandas as pd
import json
import base64

# Set Streamlit page configuration
st.set_page_config(
    page_title="Card Kaizoku - OPTCG Deck Builder",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Pirate-themed Dark Mode Accent)
st.markdown("""
<style>
    .main-title {
        color: #FF4B4B;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .card-container {
        border: 1px solid #333;
        border-radius: 10px;
        padding: 10px;
        background-color: #1E1E1E;
        margin-bottom: 15px;
        text-align: center;
    }
    .card-title {
        font-size: 14px;
        font-weight: bold;
        margin-top: 5px;
        color: #FFF;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .deck-stats {
        background-color: #111;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# CDN Endpoints
PACKS_URL = "https://cdn.jsdelivr.net/gh/michalkiral/optcg-data@main/data/packs.json"
PRICES_URL = "https://cdn.jsdelivr.net/gh/michalkiral/optcg-data@main/data/prices/summary.json"

@st.cache_data(show_spinner="กำลังโหลดรายชื่อชุดการ์ดจาก CDN...")
def fetch_packs():
    try:
        response = requests.get(PACKS_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to fetch sets: {e}")
    return []

@st.cache_data(show_spinner="กำลังโหลดข้อมูลการ์ดในชุด...")
def fetch_cards(set_code):
    url = f"https://cdn.jsdelivr.net/gh/michalkiral/optcg-data@main/data/cards/{set_code}.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to fetch cards for {set_code}: {e}")
    return []

@st.cache_data(show_spinner="กำลังดึงราคากลางล่าสุด...")
def fetch_prices():
    try:
        response = requests.get(PRICES_URL, timeout=10)
        if response.status_code == 200:
            return response.json().get("cards", {})
    except Exception as e:
        pass
    return {}

# Bypassing Bandai Image Hotlink Block (403 Forbidden)
# We fetch image via Streamlit Server and cache it, then serve directly
@st.cache_data(show_spinner=False, max_entries=500)
def get_image_bytes(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.content
    except:
        pass
    return None

def get_image_base64(url):
    img_bytes = get_image_bytes(url)
    if img_bytes:
        encoded = base64.b64encode(img_bytes).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    return url  # Fallback to direct URL if download fails

# Hypergeometric Distribution for Searcher % Odds Calculation
def calculate_hypergeometric_probability(N, K, n, k):
    """
    N: Total cards in deck (usually 50)
    K: Total targets of the searcher card in deck
    n: Cards looked at (e.g., Look at top 5 cards)
    k: Minimum successes desired (usually 1)
    """
    import math
    def combination(n, r):
        if r < 0 or r > n:
            return 0
        return math.comb(n, r)
    
    # Probability of drawing EXACTLY x targets
    total_ways = combination(N, n)
    if total_ways == 0:
        return 0
        
    prob_exact_zero = (combination(K, 0) * combination(N - K, n - 0)) / total_ways
    return round((1 - prob_exact_zero) * 100, 2)

# Load Initial Data
packs = fetch_packs()
prices = fetch_prices()

# Initialize Session States for Deck Builder
if "deck" not in st.session_state:
    st.session_state.deck = {}  # {card_id: count}
if "leader" not in st.session_state:
    st.session_state.leader = None  # Full card object of leader

# Sidebar: Controls & Options
st.sidebar.image("https://en.onepiece-cardgame.com/images/logo.png", use_container_width=True)
st.sidebar.title("🏴‍☠️ ควบคุมระบบจัดเด็ค")

# Set Selection
pack_options = {p['code']: f"{p['code']} - {p['name']}" for p in packs}
selected_set_code = st.sidebar.selectbox(
    "เลือกชุดการ์ด (Set/Expansion)",
    options=list(pack_options.keys()),
    format_func=lambda x: pack_options[x],
    index=0 if "OP-01" in pack_options else 0
)

# Load Cards for selected set
all_cards_in_set = fetch_cards(selected_set_code)

# Sidebar Filters
st.sidebar.header("🔍 ค้นหาละเอียด")
search_query = st.sidebar.text_input("ค้นหาชื่อการ์ด / เอฟเฟกต์ / รหัสการ์ด", "").strip().lower()

color_filter = st.sidebar.multiselect(
    "เลือกสีการ์ด",
    options=["Red", "Blue", "Green", "Yellow", "Black", "Purple"]
)

category_filter = st.sidebar.multiselect(
    "ประเภทการ์ด",
    options=["Leader", "Character", "Event", "Stage", "Don"]
)

cost_filter = st.sidebar.multiselect(
    "ค่าร่าย (Cost)",
    options=list(range(0, 11)),
    format_func=lambda x: f"Cost {x}"
)

# Apply filtering logic
filtered_cards = []
for c in all_cards_in_set:
    # Text Search
    name_match = search_query in c.get('name', '').lower()
    effect_match = search_query in c.get('effect', '').lower() if c.get('effect') else False
    id_match = search_query in c.get('id', '').lower()
    text_match = name_match or effect_match or id_match
    
    # Color Identity Match
    card_colors = c.get('colors', [])
    color_match = not color_filter or any(col in color_filter for col in card_colors)
    
    # Category Match
    cat_match = not category_filter or c.get('category') in category_filter
    
    # Cost Match
    cost_match = True
    if cost_filter:
        cost_match = c.get('cost') in cost_filter or (c.get('cost') is None and 0 in cost_filter)

    if text_match and color_match and cat_match and cost_match:
        filtered_cards.append(c)

# Main Web App Layout (Split view)
col_deck, col_finder = st.columns([2, 3])

with col_deck:
    st.markdown("<h2 class='main-title'>🏴‍☠️ MY DECK</h2>", unsafe_allow_html=True)
    
    # Leader Slot
    st.markdown("### 👑 การ์ดหัวหน้า (Leader)")
    if st.session_state.leader:
        l = st.session_state.leader
        st.write(f"**[{l['id']}] {l['name']}** ({'/'.join(l['colors'])})")
        
        # Display Leader Image (Using Cached Bytes to bypass 403)
        leader_img_bytes = get_image_bytes(l['image'])
        if leader_img_bytes:
            st.image(leader_img_bytes, width=150)
        else:
            st.image(l['image'], width=150) # Fallback
            
        if st.button("เปลี่ยน Leader ❌", key="remove_leader_btn"):
            st.session_state.leader = None
            st.rerun()
    else:
        st.info("💡 กรุณาเลือก Leader เพื่อล็อกขอบเขตสีเด็ค (หาปุ่ม 'Set as Leader 👑' จากฝั่งขวา)")

    # Deck list cards
    st.markdown("### 🗃️ รายชื่อการ์ดในเด็ค")
    
    total_cards = sum(st.session_state.deck.values())
    st.markdown(f"**จำนวนการ์ดในเด็คหลัก: {total_cards} / 50 ใบ**")
    
    # Validation displays
    if total_cards > 50:
        st.error("⚠️ เด็คของคุณมีการ์ดเกิน 50 ใบ!")
    elif total_cards < 50:
        st.warning("ℹ️ ต้องใส่การ์ดให้ครบ 50 ใบพอดีสำหรับการแข่งขันจริง")
    else:
        st.success("✅ เด็คหลักสมบูรณ์ครบ 50 ใบเรียบร้อย!")

    if st.session_state.deck:
        for card_id, count in list(st.session_state.deck.items()):
            # Find card details
            card_info = next((c for c in all_cards_in_set if c['id'] == card_id), None)
            if not card_info:
                card_info = {"name": card_id, "id": card_id, "colors": []}
            
            # Color identity check
            color_warning = ""
            if st.session_state.leader:
                leader_colors = st.session_state.leader.get('colors', [])
                card_colors = card_info.get('colors', [])
                if card_colors and not any(col in leader_colors for col in card_colors):
                    color_warning = " ❌ (สีไม่ตรงกับ Leader!)"
            
            c_price = prices.get(card_id, {}).get("usd", None)
            price_str = f" (${c_price:.2f})" if c_price else " (N/A)"

            col_name, col_actions = st.columns([3, 2])
            with col_name:
                st.write(f"**{count}x** {card_info['name']} ({card_info['id']}){price_str}{color_warning}")
            with col_actions:
                col_sub, col_add = st.columns(2)
                with col_sub:
                    if st.button("➖", key=f"sub_deck_{card_id}"):
                        st.session_state.deck[card_id] -= 1
                        if st.session_state.deck[card_id] <= 0:
                            del st.session_state.deck[card_id]
                        st.rerun()
                with col_add:
                    if st.button("➕", key=f"add_deck_{card_id}"):
                        if st.session_state.deck[card_id] < 4:
                            st.session_state.deck[card_id] += 1
                            st.rerun()
                        else:
                            st.error("ใส่ซ้ำได้ไม่เกิน 4 ใบ!")
    else:
        st.write("*เด็คว่างเปล่า เริ่มต้นเลือกการ์ดจากฝั่งขวา*")

    # Interactive Analytical Cost Curve (Mana Curve)
    if st.session_state.deck:
        st.markdown("### 📊 วิเคราะห์โครงสร้างเด็ค (Cost Curve)")
        cost_data = []
        for card_id, count in st.session_state.deck.items():
            card_info = next((c for c in all_cards_in_set if c['id'] == card_id), None)
            if card_info and card_info.get('cost') is not None:
                cost_data.append({"Cost": int(card_info['cost']), "Count": count})
        
        if cost_data:
            df = pd.DataFrame(cost_data)
            curve_df = df.groupby("Cost").sum().reset_index()
            # Ensure costs from 0 to 10 are represented
            full_range = pd.DataFrame({"Cost": range(0, 11)})
            curve_df = pd.merge(full_range, curve_df, on="Cost", how="left").fillna(0)
            
            # Plot Streamlit native Bar chart
            st.bar_chart(curve_df.set_index("Cost")["Count"])

    # Searcher Odds Calculator (Searcher %)
    st.markdown("### 🧮 คำนวณโอกาสจั่วการ์ดขึ้นมือ (Searcher %)")
    with st.expander("เปิดใช้งานตัวคำนวณสถิติ"):
        search_targets = st.number_input("จำนวนเป้าหมายที่จั่วได้ในเด็ค (เช่น มีการ์ดเป้าหมาย 8 ใบ)", min_value=1, max_value=50, value=8)
        search_look = st.number_input("ดูการ์ดจากยอดเด็คกี่ใบ (เช่น เอฟเฟกต์ให้ดู 5 ใบ)", min_value=1, max_value=10, value=5)
        
        prob = calculate_hypergeometric_probability(50, search_targets, search_look, 1)
        st.metric("โอกาสเปิดเจอเป้าหมายอย่างน้อย 1 ใบ", f"{prob}%")
        st.caption("อ้างอิงสถิติตามหลักคณิตศาสตร์ Hypergeometric Distribution")

    # Export Section
    st.markdown("### 📤 ส่งออกรายชื่อเด็ค (Export)")
    if st.session_state.deck:
        export_lines = []
        if st.session_state.leader:
            export_lines.append(f"1x {st.session_state.leader['id']}")
        for card_id, count in st.session_state.deck.items():
            export_lines.append(f"{count}x {card_id}")
        
        export_text = "\n".join(export_lines)
        st.text_area("คัดลอกรหัสนี้เพื่อนำไปใช้นำเข้าเล่นใน Sim ได้ทันที:", value=export_text, height=120)
    
    if st.button("ล้างเด็คทั้งหมด 🧹"):
        st.session_state.deck = {}
        st.session_state.leader = None
        st.rerun()

with col_finder:
    st.markdown("<h2 class='main-title'>🔍 คลังค้นหาการ์ด</h2>", unsafe_allow_html=True)
    st.write(f"พบการ์ดที่ตรงตามฟิลเตอร์ทั้งหมด **{len(filtered_cards)}** ใบ ในชุด {selected_set_code}")
    
    # Render cards in a responsive grid (3 columns)
    grid_cols = st.columns(3)
    for index, card in enumerate(filtered_cards):
        col_idx = index % 3
        with grid_cols[col_idx]:
            card_id = card['id']
            card_name = card['name']
            card_img = card.get('image', 'https://en.onepiece-cardgame.com/images/cardlist/card/OP01-001.png')
            card_category = card.get('category', 'Character')
            
            # Fetch Price
            card_price = prices.get(card_id, {}).get("usd", None)
            price_display = f"${card_price:.2f}" if card_price else "N/A"
            
            # Convert official image link to base64 dynamically to bypass 403 block!
            base64_img_src = get_image_base64(card_img)
            
            # Container for Card Markup with bypass attributes
            st.markdown(f"""
            <div class="card-container">
                <img src="{base64_img_src}" referrerpolicy="no-referrer" style="width:100%; border-radius:5px;" />
                <div class="card-title">{card_name}</div>
                <div style="font-size:12px; color:#aaa;">{card_id} | {card_category}</div>
                <div style="font-size:12px; color:#FF4B4B; font-weight:bold;">{price_display}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Card Actions
            if card_category == "Leader":
                if st.button("เลือกเป็น Leader 👑", key=f"set_leader_{card_id}"):
                    st.session_state.leader = card
                    st.success(f"เลือก {card_name} เรียบร้อย!")
                    st.rerun()
            else:
                curr_count = st.session_state.deck.get(card_id, 0)
                if st.button(f"ใส่เด็ค (+{curr_count})", key=f"add_finder_{card_id}"):
                    # Color check before adding
                    can_add = True
                    if st.session_state.leader:
                        leader_colors = st.session_state.leader.get('colors', [])
                        card_colors = card.get('colors', [])
                        if card_colors and not any(col in leader_colors for col in card_colors):
                            st.warning(f"คำเตือน: {card_name} มีสีไม่ตรงกับ Leader")
                    
                    if curr_count >= 4:
                        st.error("ไม่สามารถใส่การ์ดใบนี้เกิน 4 ใบได้!")
                    else:
                        st.session_state.deck[card_id] = curr_count + 1
                        st.success(f"เพิ่ม {card_name} สำเร็จ!")
                        st.rerun()
