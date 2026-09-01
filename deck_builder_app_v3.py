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
            packs = response.json()
            return packs
    except Exception:
        pass
    
    # Fallback default packs list
    return [
        {"code": "OP-01", "name": "ROMANCE DAWN"},
        {"code": "OP-02", "name": "PARAMOUNT WAR"},
        {"code": "OP-03", "name": "PILLARS OF STRENGTH"},
        {"code": "OP-04", "name": "KINGDOMS OF INTRIGUE"},
        {"code": "OP-05", "name": "AWAKENING OF THE NEW ERA"},
        {"code": "OP-06", "name": "WINGS OF THE CAPTAIN"},
        {"code": "OP-07", "name": "500 YEARS IN THE FUTURE"},
        {"code": "OP-08", "name": "TWO LEGENDS"},
        {"code": "OP-09", "name": "EMPERORS IN THE NEW WORLD"},
        {"code": "OP-10", "name": "ROYAL ROYAL MEMBER"},
        {"code": "EB-01", "name": "MEMORIAL COLLECTION"}
    ]

# Curated Fallback Static Cards for Newer Sets
NEW_SETS_FALLBACK_DATA = {
    "OP-16": [
        {
            "id": "OP16-001",
            "set": "OP-16",
            "name": "Portgas.D.Ace",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Red"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Special"],
            "types": ["Whitebeard Pirates"],
            "effect": "[DON!! x1] [Your Turn] All of your Whitebeard Pirates Characters gain +1000 power.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP16-001.png"
        },
        {
            "id": "OP16-002",
            "set": "OP-16",
            "name": "Monkey.D.Luffy",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Red", "Blue"],
            "cost": 4,
            "power": 5000,
            "attributes": ["Strike"],
            "types": ["Straw Hat Crew", "Impel Down"],
            "effect": "[Your Turn] When one of your Characters is returned to your hand, you may play 1 'Impel Down' type Character card from your hand.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP16-002.png"
        },
        {
            "id": "OP16-003",
            "set": "OP-16",
            "name": "Sengoku",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Black"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Wisdom"],
            "types": ["Navy"],
            "effect": "[Your Turn] Reduce the cost of Navy attribute Character cards in your hand by 1.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP16-003.png"
        },
        {
            "id": "OP16-004",
            "set": "OP-16",
            "name": "Buggy",
            "rarity": "Rare",
            "category": "Character",
            "colors": ["Red"],
            "cost": 1,
            "power": 3000,
            "attributes": ["Slash"],
            "types": ["Impel Down", "Buggy's Delivery"],
            "effect": "[On Play] Look at the top 5 cards of your deck. Reveal up to 1 'Impel Down' type card and add it to your hand.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP16-004.png"
        },
        {
            "id": "OP16-005",
            "set": "OP-16",
            "name": "Edward.Newgate",
            "rarity": "SuperRare",
            "category": "Character",
            "colors": ["Red"],
            "cost": 9,
            "power": 10000,
            "attributes": ["Slash"],
            "types": ["Whitebeard Pirates"],
            "effect": "[On Play] Draw 1 card. Your Leader gains +2000 power until the start of your next turn.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP16-005.png"
        }
    ],
    "OP-17": [
        {
            "id": "OP17-001",
            "set": "OP-17",
            "name": "Edward.Newgate",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Red"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Slash"],
            "types": ["Four Emperors", "Whitebeard Pirates"],
            "effect": "[Opponent's Turn] Trash 1 card from your hand: Give your Leader or up to 1 of your Characters +4000 power during this battle.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP17-001.png"
        },
        {
            "id": "OP17-020",
            "set": "OP-17",
            "name": "Shanks",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Green"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Slash"],
            "types": ["Four Emperors", "Red Hair Pirates"],
            "effect": "[Activate: Main] Rest 1 of your Characters: Up to 1 of your opponent's rested Characters does not active during their next active phase.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP17-020.png"
        },
        {
            "id": "OP17-039",
            "set": "OP-17",
            "name": "Rocks.D.Xebec",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Blue"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Slash"],
            "types": ["Rocks Pirates"],
            "effect": "[Activate: Main] Trash 1 card from your hand: Reveal the top card of your deck. If it is a Rocks Pirates type card, draw 2 cards.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP17-039.png"
        },
        {
            "id": "OP17-058",
            "set": "OP-17",
            "name": "Kaido",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Purple"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Strike"],
            "types": ["Four Emperors", "Animal Kingdom Pirates"],
            "effect": "[Once Per Turn] [DON!! -1] When this Leader attacks or is attacked, reduce the power of 1 of your opponent's Characters by -2000 during this turn.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP17-058.png"
        },
        {
            "id": "OP17-079",
            "set": "OP-17",
            "name": "Monkey.D.Luffy",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Black"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Strike"],
            "types": ["Straw Hat Crew", "Elbaf"],
            "effect": "[Your Turn] Give [Blocker] to all of your Character cards with a cost of 12 or more.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP17-079.png"
        },
        {
            "id": "OP17-099",
            "set": "OP-17",
            "name": "Charlotte Linlin",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Yellow"],
            "cost": 5,
            "power": 5000,
            "attributes": ["Slash"],
            "types": ["Four Emperors", "Big Mom Pirates"],
            "effect": "[Your Turn] Trash 1 card from your hand: Your opponent chooses to either add 1 card from the top of their deck to their Life, or discard 1 card.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP17-099.png"
        },
        {
            "id": "OP17-118",
            "set": "OP-17",
            "name": "Rocks.D.Xebec",
            "rarity": "SecretRare",
            "category": "Character",
            "colors": ["Blue"],
            "cost": 10,
            "power": 12000,
            "attributes": ["Slash"],
            "types": ["Rocks Pirates"],
            "effect": "[On Play] Draw 1 card. Play up to 2 'Rocks Pirates' type Character cards with different names and a combined cost of 9 or less from your hand.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/OP17-118.png"
        }
    ],
    "EB-04": [
        {
            "id": "EB04-001",
            "set": "EB-04",
            "name": "Jewelry Bonney",
            "rarity": "Leader",
            "category": "Leader",
            "colors": ["Red", "Yellow"],
            "cost": 4,
            "power": 5000,
            "attributes": ["Special"],
            "types": ["Egghead", "Bonney Pirates"],
            "effect": "[Opponent's Turn] If you have 1 or less Life, this Leader gains +1000 power during battles.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/EB04-001.png"
        },
        {
            "id": "EB04-005",
            "set": "EB-04",
            "name": "Trafalgar Law",
            "rarity": "Common",
            "category": "Character",
            "colors": ["Red"],
            "cost": 3,
            "power": 5000,
            "attributes": ["Slash"],
            "types": ["Supernovas", "Heart Pirates", "Seven Warlords"],
            "effect": "[DON!! x1] Give up to 1 of your opponent's Characters -2000 power during this turn.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/EB04-005.png"
        },
        {
            "id": "EB04-052",
            "set": "EB-04",
            "name": "Sanji",
            "rarity": "Rare",
            "category": "Character",
            "colors": ["Blue"],
            "cost": 4,
            "power": 6000,
            "attributes": ["Strike"],
            "types": ["Straw Hat Crew", "Egghead"],
            "effect": "[Blocker] When blocking an attack, you may draw 1 card.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/EB04-052.png"
        },
        {
            "id": "EB04-058",
            "set": "EB-04",
            "name": "Borsalino",
            "rarity": "Rare",
            "category": "Character",
            "colors": ["Black"],
            "cost": 5,
            "power": 6000,
            "attributes": ["Special"],
            "types": ["Navy", "Egghead"],
            "effect": "[On Play] K.O. up to 1 of your opponent's Characters with a cost of 3 or less.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/EB04-058.png"
        },
        {
            "id": "EB04-061",
            "set": "EB-04",
            "name": "Monkey.D.Luffy",
            "rarity": "SecretRare",
            "category": "Character",
            "colors": ["Red"],
            "cost": 5,
            "power": 7000,
            "attributes": ["Strike"],
            "types": ["Straw Hat Crew", "Egghead"],
            "effect": "[On Play] If you have 2 or less Life, this Character gains +2000 power and [Rush] during this turn.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/EB04-061.png"
        },
        {
            "id": "EB04-044",
            "set": "EB-04",
            "name": "Koby",
            "rarity": "SuperRare",
            "category": "Character",
            "colors": ["Black"],
            "cost": 4,
            "power": 5000,
            "attributes": ["Strike"],
            "types": ["Navy", "Egghead"],
            "effect": "[On Play] K.O. up to 1 of your opponent's Characters with a cost of 2 or less.",
            "image": "https://en.onepiece-cardgame.com/images/cardlist/card/EB04-044.png"
        }
    ]
}

def normalize_api_cards(api_cards, set_code):
    normalized = []
    for c in api_cards:
        card_id = c.get('id') or c.get('card_id')
        colors = c.get('colors') or c.get('color') or []
        if isinstance(colors, str):
            colors = [colors]
        elif not isinstance(colors, list):
            colors = []
            
        normalized_card = {
            "id": card_id,
            "set": c.get('set_id') or set_code,
            "name": c.get('name', 'Unknown Card'),
            "rarity": c.get('rarity', 'Common'),
            "category": c.get('category') or c.get('type') or 'Character',
            "colors": colors,
            "cost": c.get('cost') or 0,
            "power": c.get('power'),
            "counter": c.get('counter'),
            "attributes": c.get('attributes') or c.get('attribute', []),
            "types": c.get('types') or c.get('tags', []),
            "effect": c.get('effect') or c.get('ability', ''),
            "trigger": c.get('trigger'),
            "image": c.get('image') or f"https://en.onepiece-cardgame.com/images/cardlist/card/{card_id}.png"
        }
        normalized.append(normalized_card)
    return normalized

@st.cache_data(show_spinner="🃏 Loading cards for selected set...")
def fetch_cards(set_code):
    # Try 1: michalkiral/optcg-data CDN
    url = f"https://cdn.jsdelivr.net/gh/michalkiral/optcg-data@main/data/cards/{set_code}.json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass

    # Try 2: arjunkai REST API (Cloudflare Workers CDN)
    api_url = f"https://optcg-api.arjunbansal-ai.workers.dev/sets/{set_code}/cards"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            cards_data = response.json()
            if isinstance(cards_data, list):
                return normalize_api_cards(cards_data, set_code)
    except Exception:
        pass

    # Try 3: arjunkai REST API query parameter filter
    api_url_filter = f"https://optcg-api.arjunbansal-ai.workers.dev/cards?set_id={set_code}"
    try:
        response = requests.get(api_url_filter, timeout=10)
        if response.status_code == 200:
            cards_data = response.json()
            if isinstance(cards_data, dict) and "cards" in cards_data:
                cards_data = cards_data["cards"]
            if isinstance(cards_data, list):
                return normalize_api_cards(cards_data, set_code)
    except Exception:
        pass

    # Try 4: Hardcoded Static fallback database for newer sets
    if set_code in NEW_SETS_FALLBACK_DATA:
        return NEW_SETS_FALLBACK_DATA[set_code]

    return []

@st.cache_data(show_spinner="💰 Loading real-time market prices...")
def fetch_prices():
    try:
        response = requests.get(PRICES_URL, timeout=10)
        if response.status_code == 200:
            return response.json().get("cards", {})
    except Exception:
        pass
    return {}

# Hypergeometric Probability Calculator (Searcher % formula)
def calculate_searcher_prob(deck_size, targets, cards_looked_at):
    if deck_size <= 0 or targets < 0 or cards_looked_at < 0 or cards_looked_at > deck_size or targets > deck_size:
        return 0.0
    try:
        ways_no_targets = math.comb(deck_size - targets, cards_looked_at)
        total_ways = math.comb(deck_size, cards_looked_at)
        p_zero = ways_no_targets / total_ways
        return (1.0 - p_zero) * 100
    except Exception:
        return 0.0

# Ingest initial static data
packs = fetch_packs()

# Dynamically inject OP-16, OP-17, and EB-04 into packs if they are missing
existing_codes = [p['code'] for p in packs] if packs else []
target_new_sets = [
    {"code": "OP-16", "name": "THE TIME OF BATTLE"},
    {"code": "OP-17", "name": "THE WORLD'S STRONGEST WARRIORS"},
    {"code": "EB-04", "name": "EGGHEAD CRISIS"}
]
for ns in target_new_sets:
    if ns['code'] not in existing_codes:
        packs.append(ns)

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
    index=list(pack_options.keys()).index("OP-17") if "OP-17" in pack_options else 0
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
            # Bulletproof Referrer Bypass for Leader image display
            st.markdown(f'<img src="{l["image"]}" referrerpolicy="no-referrer" style="width:100%; border-radius:5px;" />', unsafe_allow_html=True)
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
            # Find card in current set or fallback sets
            card_info = next((c for c in all_cards_in_set if c['id'] == card_id), None)
            if not card_info:
                # Scan fallback sets manually
                for f_set in NEW_SETS_FALLBACK_DATA.values():
                    card_info = next((c for c in f_set if c['id'] == card_id), None)
                    if card_info:
                        break
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
                
                # HTML card rendering container with double bypass headers
                st.markdown(f"""
                <div class="card-container">
                    <img src="{card_img}" referrerpolicy="no-referrer" style="width:100%; border-radius:5px;" />
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
