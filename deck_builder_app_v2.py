import streamlit as st
import requests
import pandas as pd
import json
import math

# Set Streamlit page configuration
st.set_page_config(
    page_title="Card Kaizoku - OPTCG Deck Builder & Analytics",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Pirate-themed Dark Mode Accent with Red)
st.markdown("""
<style>
    .main-title {
        color: #FF4B4B;
        font-family: 'Courier New', monospace;
        font-weight: bold;
        text-align: center;
        margin-bottom: 5px;
    }
    .subtitle {
        color: #888;
        text-align: center;
        margin-bottom: 25px;
        font-size: 14px;
    }
    .card-container {
        border: 1px solid #333;
        border-radius: 10px;
        padding: 10px;
        background-color: #1E1E1E;
        margin-bottom: 15px;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .card-container:hover {
        transform: scale(1.03);
        border-color: #FF4B4B;
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
    .stats-panel {
        background-color: #111;
        border-radius: 8px;
        padding: 15px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 20px;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# CDN Endpoints
PACKS_URL = "https://cdn.jsdelivr.net/gh/michalkiral/optcg-data@main/data/packs.json"
PRICES_URL = "https://cdn.jsdelivr.net/gh/michalkiral/optcg-data@main/data/prices/summary.json"

@st.cache_data(show_spinner="⚓ Loading set list from CDN...")
def fetch_packs():
    try:
        response = requests.get(PACKS_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to fetch sets: {e}")
    return []

@st.cache_data(show_spinner="🃏 Loading cards for selected set...")
def fetch_cards(set_code):
    url = f"https://cdn.jsdelivr.net/gh/michalkiral/optcg-data@main/data/cards/{set_code}.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Failed to fetch cards for {set_code}: {e}")
    return []

@st.cache_data(show_spinner="💰 Loading real-time market prices...")
def fetch_prices():
    try:
        response = requests.get(PRICES_URL, timeout=10)
        if response.status_code == 200:
            return response.json().get("cards", {})
    except Exception as e:
        pass
    return {}

# Hypergeometric Probability Calculator (Searcher % formula)
def calculate_searcher_prob(deck_size, targets, cards_looked_at):
    if deck_size <= 0 or targets < 0 or cards_looked_at < 0 or cards_looked_at > deck_size or targets > deck_size:
        return 0.0
    # Probability of seeing 0 targets in the sampled cards:
    # P(X=0) = (comb(targets, 0) * comb(deck_size - targets, cards_looked_at)) / comb(deck_size, cards_looked_at)
    try:
        ways_no_targets = math.comb(deck_size - targets, cards_looked_at)
        total_ways = math.comb(deck_size, cards_looked_at)
        p_zero = ways_no_targets / total_ways
        return (1.0 - p_zero) * 100
    except Exception:
        return 0.0

# Ingest initial static data
packs = fetch_packs()
prices = fetch_prices()

# Initialize session state variables
if "deck" not in st.session_state:
    st.session_state.deck = {}  # {card_id: count}
if "leader" not in st.session_state:
    st.session_state.leader = None  # Full Leader card dictionary

# Sidebar Design
st.sidebar.image("https://en.onepiece-cardgame.com/images/logo.png", use_container_width=True)
st.sidebar.title("🏴‍☠️ Kaizoku Control Room")

# Expansion / Set Selector
pack_options = {p['code']: f"{p['code']} - {p['name']}" for p in packs}
selected_set_code = st.sidebar.selectbox(
    "Set/Expansion Pack",
    options=list(pack_options.keys()),
    format_func=lambda x: pack_options[x],
    index=0 if "OP-01" in pack_options else 0
)

# Fetch card metadata of the selected set
all_cards_in_set = fetch_cards(selected_set_code)

st.sidebar.header("🔍 Filters")
search_query = st.sidebar.text_input("Name, Card ID, or Text Search", "").strip().lower()

color_filter = st.sidebar.multiselect(
    "Filter by Color",
    options=["Red", "Blue", "Green", "Yellow", "Black", "Purple"]
)

category_filter = st.sidebar.multiselect(
    "Card Category",
    options=["Leader", "Character", "Event", "Stage", "Don"]
)

cost_filter = st.sidebar.multiselect(
    "Cost Value",
    options=list(range(0, 11)),
    format_func=lambda x: f"Cost {x}"
)

# Apply filter processing
filtered_cards = []
for c in all_cards_in_set:
    name_match = search_query in c.get('name', '').lower()
    effect_match = search_query in c.get('effect', '').lower() if c.get('effect') else False
    id_match = search_query in c.get('id', '').lower()
    text_match = name_match or effect_match or id_match
    
    card_colors = c.get('colors', [])
    color_match = not color_filter or any(col in color_filter for col in card_colors)
    
    cat_match = not category_filter or c.get('category') in category_filter
    
    cost_match = True
    if cost_filter:
        cost_match = c.get('cost') in cost_filter or (c.get('cost') is None and 0 in cost_filter)

    if text_match and color_match and cat_match and cost_match:
        filtered_cards.append(c)

# Main Multi-column layout: Deck Sheet (Left) & Card Database View (Right)
col_deck, col_finder = st.columns([2, 3])

with col_deck:
    st.markdown("<h2 class='main-title'>🏴‍☠️ MY DECK SHEET</h2>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Manage your list and see real-time price totals</p>", unsafe_allow_html=True)
    
    # Leader Selection Container
    st.markdown("#### 👑 Selected Leader")
    if st.session_state.leader:
        l = st.session_state.leader
        lead_col1, lead_col2 = st.columns([1, 2])
        with lead_col1:
            st.image(l['image'], use_container_width=True)
        with lead_col2:
            st.write(f"**{l['name']}**")
            st.write(f"ID: `{l['id']}`")
            st.write(f"Colors: {', '.join(l['colors'])}")
            if st.button("Change Leader", key="remove_leader_action"):
                st.session_state.leader = None
                st.rerun()
    else:
        st.info("No Leader active. Choose 'Set as Leader' from any Leader card on the right-hand panel.")

    # Main Deck Grid & Validation Logic
    st.markdown("#### 🗃️ Deck Cards")
    total_cards = sum(st.session_state.deck.values())
    
    # Render interactive progress bar for 50 card target
    progress_val = min(total_cards / 50.0, 1.0)
    st.progress(progress_val, text=f"Deck Size: {total_cards} / 50 cards")
    
    # Display actionable warning flags
    if total_cards > 50:
        st.error(f"⚠️ Your deck contains {total_cards} cards. It exceeds the 50-card legal limit!")
    elif total_cards < 50:
        st.warning(f"ℹ️ Deck currently has {total_cards} cards. Add exactly {50 - total_cards} more Character, Event, or Stage cards.")
    else:
        st.success("✅ Perfect! Your deck has exactly 50 cards and is legal for tournament play.")

    # Calculate Deck Prices and render List
    deck_total_price = 0.0
    deck_items_to_display = []
    
    if st.session_state.deck:
        for card_id, count in list(st.session_state.deck.items()):
            # Find in current set, fallback to empty card model
            card_info = next((c for c in all_cards_in_set if c['id'] == card_id), None)
            if not card_info:
                card_info = {"name": card_id, "id": card_id, "colors": [], "cost": 0}
            
            c_price = prices.get(card_id, {}).get("usd", 0.0) or 0.0
            subtotal = c_price * count
            deck_total_price += subtotal
            
            # Validation: Color Identity check
            color_mismatch = False
            if st.session_state.leader:
                leader_colors = st.session_state.leader.get('colors', [])
                card_colors = card_info.get('colors', [])
                if card_colors and not any(col in leader_colors for col in card_colors):
                    color_mismatch = True

            deck_items_to_display.append({
                "id": card_id,
                "name": card_info['name'],
                "count": count,
                "price": c_price,
                "mismatch": color_mismatch,
                "cost": card_info.get('cost', 0)
            })

        # Display deck rows
        for item in deck_items_to_display:
            mismatch_label = " ❌ Color Error" if item['mismatch'] else ""
            price_label = f"(${item['price']:.2f} ea)" if item['price'] > 0 else "($N/A)"
            
            row_col1, row_col2 = st.columns([3, 1])
            with row_col1:
                st.markdown(f"**{item['count']}x** {item['name']} (`{item['id']}`) {price_label} {mismatch_label}")
            with row_col2:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("➖", key=f"minus_{item['id']}", help="Reduce count"):
                        st.session_state.deck[item['id']] -= 1
                        if st.session_state.deck[item['id']] <= 0:
                            del st.session_state.deck[item['id']]
                        st.rerun()
                with btn_col2:
                    if st.button("➕", key=f"plus_{item['id']}", help="Increase count"):
                        if st.session_state.deck[item['id']] < 4:
                            st.session_state.deck[item['id']] += 1
                            st.rerun()
                        else:
                            st.error("Max 4 copies of any card in a deck!")
    else:
        st.write("*Your deck is empty. Browse the card base and start adding characters!*")

    # Financial Total
    if deck_total_price > 0:
        st.markdown(f"##### 💰 Estimated Market Value: **${deck_total_price:.2f} USD**")

    # Visual Analytics: Cost Curve
    if deck_items_to_display:
        st.markdown("#### 📊 Deck Cost Curve")
        curve_data = {}
        for item in deck_items_to_display:
            cost_val = str(item['cost']) if item['cost'] is not None else "0"
            curve_data[cost_val] = curve_data.get(cost_val, 0) + item['count']
        
        df_curve = pd.DataFrame(list(curve_data.items()), columns=["Cost", "Quantity"]).sort_values("Cost")
        st.bar_chart(df_curve.set_index("Cost"), height=180, color="#FF4B4B")

    # Analytical Tools: Searcher Odds
    st.markdown("#### 🧮 Searcher % Odds Calculator")
    with st.expander("Calculate the probability of drawing card search targets"):
        target_count = st.number_input("Number of target cards left in deck:", min_value=1, max_value=50, value=4)
        look_count = st.number_input("Cards looked at (e.g. searcher effect says top 5):", min_value=1, max_value=10, value=5)
        
        current_deck_size = max(total_cards, 50) # Use 50 as standard reference if deck not built yet
        prob_percent = calculate_searcher_prob(current_deck_size, target_count, look_count)
        st.metric(label="Success Probability", value=f"{prob_percent:.2f}%")
        st.caption(f"Based on a current reference deck size of {current_deck_size} cards.")

    # Export Area
    st.markdown("#### 💾 Export Configuration")
    if st.session_state.deck:
        export_text_lines = []
        if st.session_state.leader:
            export_text_lines.append(f"1x {st.session_state.leader['id']}")
        for card_id, count in st.session_state.deck.items():
            export_text_lines.append(f"{count}x {card_id}")
            
        export_val = "\n".join(export_text_lines)
        st.text_area("TCGPlayer Mass Entry Format:", value=export_val, height=120)
        
    if st.button("Reset Entire Deck Sheet 🧹"):
        st.session_state.deck = {}
        st.session_state.leader = None
        st.rerun()

with col_finder:
    st.markdown("<h2 class='main-title'>🔍 CARD DATABASE</h2>", unsafe_allow_html=True)
    st.write(f"Showing **{len(filtered_cards)}** match(es) from **{selected_set_code}**")
    
    # Render Responsive Grid of Cards
    cols_per_row = 3
    for i in range(0, len(filtered_cards), cols_per_row):
        row_cards = filtered_cards[i:i+cols_per_row]
        cols = st.columns(cols_per_row)
        for idx, card in enumerate(row_cards):
            with cols[idx]:
                card_id = card['id']
                card_name = card['name']
                card_img = card.get('image', 'https://en.onepiece-cardgame.com/images/cardlist/card/OP01-001.png')
                card_category = card.get('category', 'Character')
                
                # Fetch live USD price
                card_price = prices.get(card_id, {}).get("usd", None)
                price_display = f"${card_price:.2f}" if card_price else "N/A"
                
                # HTML card rendering container
                st.markdown(f"""
                <div class="card-container">
                    <img src="{card_img}" style="width:100%; border-radius:5px;" />
                    <div class="card-title">{card_name}</div>
                    <div style="font-size:11px; color:#aaa;">{card_id} | {card_category}</div>
                    <div style="font-size:12px; color:#FF4B4B; font-weight:bold; margin-top:3px;">{price_display}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Context-aware actions
                if card_category == "Leader":
                    if st.button("Set as Leader 👑", key=f"set_lead_{card_id}"):
                        st.session_state.leader = card
                        st.rerun()
                else:
                    curr_count = st.session_state.deck.get(card_id, 0)
                    if st.button(f"Add to Deck (+{curr_count})", key=f"add_{card_id}"):
                        if curr_count >= 4:
                            st.error("Maximum limit is 4!")
                        else:
                            st.session_state.deck[card_id] = curr_count + 1
                            st.rerun()
