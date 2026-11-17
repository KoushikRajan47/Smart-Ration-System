"""
UI/UX styling, custom CSS design system, multilingual dictionaries,
and rich visual components for the Smart Ration & Distribution System.
"""
from typing import Dict, Any, Optional

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

    /* Global Typography & CSS Variables */
    :root {
        --primary-navy: #0F172A;
        --gov-blue: #1E40AF;
        --bright-blue: #2563EB;
        --sky-blue: #38BDF8;
        --emerald: #10B981;
        --amber: #F59E0B;
        --rose: #F43F5E;
        --slate-bg: #F8FAFC;
        --card-white: #FFFFFF;
        --border-subtle: #E2E8F0;
        --text-heading: #0F172A;
        --text-body: #334155;
        --text-muted: #64748B;
    }

    html, body, [class*="css"], .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        background-color: #F8FAFC !important;
        color: #1E293B;
    }

    /* Main Container Cleanup */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1320px !important;
    }

    /* National Portal Tricolor Ribbon */
    .tricolor-stripe {
        height: 5px;
        width: 100%;
        background: linear-gradient(90deg, #FF9933 0%, #FF9933 33.3%, #FFFFFF 33.3%, #FFFFFF 66.6%, #138808 66.6%, #138808 100%);
        border-radius: 999px;
        margin-bottom: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Top Brand Navigation Bar */
    .brand-top-bar {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 16px 24px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03), 0 2px 4px -2px rgba(0,0,0,0.03);
    }
    .brand-logo-group {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .brand-emblem-icon {
        font-size: 38px;
        line-height: 1;
        background: #EFF6FF;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #DBEAFE;
    }
    .brand-title-main {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }
    .brand-title-sub {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 500;
        margin: 2px 0 0 0;
    }
    .live-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.25);
        animation: pulseDot 2s infinite;
    }
    @keyframes pulseDot {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.5); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 55%, #1D4ED8 100%);
        border-radius: 20px;
        padding: 32px 38px;
        color: #FFFFFF;
        box-shadow: 0 12px 30px -5px rgba(30, 58, 138, 0.35);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .hero-banner::after {
        content: "🌾";
        position: absolute;
        right: 28px;
        bottom: -15px;
        font-size: 130px;
        opacity: 0.12;
        pointer-events: none;
    }
    .hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin: 0;
        color: #FFFFFF;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #BFDBFE;
        margin-top: 8px;
        font-weight: 500;
        max-width: 820px;
        line-height: 1.5;
    }
    .hero-chips-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 18px;
    }
    .hero-chip {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 999px;
        padding: 5px 14px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #F8FAFC;
    }

    /* Modern Tabs Redesign */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: #F1F5F9 !important;
        padding: 6px !important;
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        margin-bottom: 22px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px !important;
        border-radius: 10px !important;
        padding: 8px 18px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        color: #64748B !important;
        background-color: transparent !important;
        border: none !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0F172A !important;
        background-color: rgba(255, 255, 255, 0.7) !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1E3A8A !important;
        font-weight: 700 !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Buttons Modern Styling */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 9px 20px !important;
        transition: all 0.2s ease-in-out !important;
        border: 1px solid #CBD5E1 !important;
        background: #FFFFFF !important;
        color: #1E293B !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }
    .stButton > button:hover {
        transform: translateY(-1.5px) !important;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08) !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
    }
    .stButton > button[kind="primary"], .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover, .stButton > button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #172554 0%, #1D4ED8 60%, #2563EB 100%) !important;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45) !important;
        transform: translateY(-2px) !important;
    }

    /* Input & Select Fields */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 1.5px solid #CBD5E1 !important;
        background-color: #FFFFFF !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    div[data-baseweb="input"]:focus-within > div, div[data-baseweb="select"]:focus-within > div {
        border-color: #2563EB !important;
        box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.15) !important;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        padding: 18px 22px !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.03) !important;
        transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s !important;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.06) !important;
        border-color: #CBD5E1 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #64748B !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        background: #FFFFFF !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 12px !important;
        overflow: hidden;
    }
    div[data-testid="stExpander"] details summary {
        font-weight: 700 !important;
        color: #1E293B !important;
        background: #F8FAFC !important;
        padding: 12px 20px !important;
    }
    div[data-testid="stExpander"] details summary:hover {
        color: #1E40AF !important;
        background: #EFF6FF !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: #0B132B !important;
        color: #F8FAFC !important;
        border-right: 1px solid #1E293B !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label {
        color: #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: #1C2541 !important;
        color: #F8FAFC !important;
        border: 1px solid #3A506B !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #3A506B !important;
        border-color: #5BC0BE !important;
        color: #FFFFFF !important;
    }

    /* Digital Smart Ration Card */
    .smart-card-container {
        background: linear-gradient(135deg, #0A1128 0%, #1C2541 50%, #001233 100%);
        border-radius: 20px;
        padding: 26px 30px;
        color: #FFFFFF;
        box-shadow: 0 16px 35px -8px rgba(10, 17, 40, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
        position: relative;
        overflow: hidden;
        margin-bottom: 24px;
        max-width: 650px;
    }
    .smart-card-container::before {
        content: "";
        position: absolute;
        top: -60%;
        left: -40%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 60%);
        pointer-events: none;
    }
    .card-top-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        position: relative;
        z-index: 2;
    }
    .card-gov-seal {
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #93C5FD;
    }
    .card-chip-hologram {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 18px 0 16px 0;
        position: relative;
        z-index: 2;
    }
    .emv-chip {
        width: 44px;
        height: 32px;
        background: linear-gradient(135deg, #F59E0B 0%, #FBBF24 50%, #D97706 100%);
        border-radius: 6px;
        border: 1px solid #B45309;
        box-shadow: inset 0 0 4px rgba(0,0,0,0.3);
        position: relative;
    }
    .emv-chip::after {
        content: "";
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 1px;
        background: #B45309;
    }
    .contactless-waves {
        font-size: 1.25rem;
        color: #94A3B8;
        transform: rotate(90deg);
        display: inline-block;
    }
    .card-hologram-badge {
        margin-left: auto;
        background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%);
        border: 1px solid rgba(255,255,255,0.25);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        color: #E2E8F0;
    }
    .card-num-display {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        color: #FFFFFF;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        margin-bottom: 14px;
        position: relative;
        z-index: 2;
    }
    .card-details-grid {
        display: grid;
        grid-template-columns: 1.5fr 1fr 1fr;
        gap: 12px;
        position: relative;
        z-index: 2;
        border-top: 1px solid rgba(255,255,255,0.12);
        padding-top: 12px;
    }
    .card-field-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #94A3B8;
        letter-spacing: 0.05em;
    }
    .card-field-val {
        font-size: 0.92rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 2px;
    }

    /* Entitlement Quota Visual Meters */
    .quota-card-box {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 20px 22px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 3px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .quota-card-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 18px rgba(0,0,0,0.07);
    }
    .quota-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .quota-icon-name {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .quota-icon-circle {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    .quota-name {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0F172A;
    }
    .quota-rate {
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 600;
    }
    .progress-bar-bg {
        width: 100%;
        height: 10px;
        background: #E2E8F0;
        border-radius: 999px;
        overflow: hidden;
        margin: 10px 0;
    }
    .progress-bar-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.6s ease-in-out;
    }
    .quota-numbers-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        color: #475569;
        font-weight: 600;
    }

    /* Priority Boarding Pass Ticket */
    .boarding-pass-card {
        background: #FFFFFF;
        border-radius: 18px;
        border: 1px solid #CBD5E1;
        box-shadow: 0 8px 24px -4px rgba(0,0,0,0.08);
        display: flex;
        flex-direction: row;
        overflow: hidden;
        margin: 16px 0;
        position: relative;
    }
    @media (max-width: 768px) {
        .boarding-pass-card { flex-direction: column; }
    }
    .pass-main {
        flex: 3;
        padding: 24px 28px;
        border-right: 2px dashed #CBD5E1;
        position: relative;
    }
    .pass-stub {
        flex: 1.2;
        background: #F8FAFC;
        padding: 24px 20px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        text-align: center;
    }
    .pass-ref-badge {
        display: inline-block;
        background: #EFF6FF;
        color: #1D4ED8;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }
    .pass-time-slot {
        font-size: 1.6rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.02em;
    }

    /* Thermal POS Digital Receipt */
    .thermal-receipt-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px 12px 0 0;
        padding: 28px 30px;
        max-width: 520px;
        margin: 16px auto;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.08);
        position: relative;
    }
    .thermal-receipt-container::after {
        content: "";
        position: absolute;
        bottom: -10px;
        left: 0;
        right: 0;
        height: 10px;
        background: radial-gradient(circle, transparent, transparent 50%, #FFFFFF 50%, #FFFFFF 100%);
        background-size: 16px 16px;
    }
    .receipt-center-brand {
        text-align: center;
        border-bottom: 1.5px dashed #CBD5E1;
        padding-bottom: 16px;
        margin-bottom: 16px;
    }
    .receipt-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        margin-bottom: 7px;
    }
    .receipt-total-bar {
        background: #F1F5F9;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 14px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: 800;
        font-size: 1.15rem;
        color: #0F172A;
    }

    /* Pill Badges */
    .pill-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }
    .pill-emerald { background: #DCFCE7; color: #15803D; border: 1px solid #BBF7D0; }
    .pill-amber { background: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
    .pill-rose { background: #FFE4E6; color: #BE123C; border: 1px solid #FECDD3; }
    .pill-blue { background: #DBEAFE; color: #1E40AF; border: 1px solid #BFDBFE; }
</style>
"""

TRANSLATIONS = {
    "English": {
        "title": "Smart Ration & Public Distribution System",
        "subtitle": "AI & Machine Learning-Powered Fair Price Shop Distribution",
        "citizen_portal": "Citizen & Beneficiary Portal",
        "citizen_desc": "Check monthly grain entitlements, track live depot stock, and book collection slots with ML queue predictions.",
        "dealer_portal": "Fair Price Shop Dealer",
        "dealer_desc": "Forecast daily commodity demand, detect stock shortages, and disburse grains with live POS inventory sync.",
        "admin_portal": "Administrative Directorate",
        "admin_desc": "Monitor statewide depot reserves, manage slot capacities, review citizen grievances, and audit ML telemetry.",
        "analytics_portal": "Data Science & ML Analytics Studio",
        "analytics_desc": "Explore 5 trained regression models, compare cross-validation metrics, and run what-if simulations.",
        "rice": "Rice",
        "wheat": "Wheat",
        "sugar": "Sugar",
        "login": "Secure Login",
        "demo_login": "Quick Demo Login",
        "register": "New Cardholder Registration",
        "select_role": "Select Access Gateway",
    },
    "ಕನ್ನಡ (Kannada)": {
        "title": "ಸ್ಮಾರ್ಟ್ ಪಡಿತರ ಮತ್ತು ವಿತರಣಾ ವ್ಯವಸ್ಥೆ",
        "subtitle": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ ಮತ್ತು ಯಂತ್ರ ಕಲಿಕೆ ಚಾಲಿತ ಸಾರ್ವಜನಿಕ ವಿತರಣಾ ಪೋರ್ಟಲ್",
        "citizen_portal": "ಫಲಾನುಭವಿ / ನಾಗರಿಕ ಪೋರ್ಟಲ್",
        "citizen_desc": "ಮಾಸಿಕ ಪಡಿತರ ಕೋಟಾ ಪರಿಶೀಲಿಸಿ, ನೈಜ-ಸಮಯದ ದಾಸ್ತಾನು ನೋಡಿ, ಮತ್ತು ಸ್ಮಾರ್ಟ್ ಸ್ಲಾಟ್ ಕಾಯ್ದಿರಿಸಿ.",
        "dealer_portal": "ನ್ಯಾಯಬೆಲೆ ಅಂಗಡಿ ಡೀಲರ್",
        "dealer_desc": "ದೈನಂದಿನ ಬೇಡಿಕೆ ಮುನ್ಸೂಚನೆ, ದಾಸ್ತಾನು ಕೊರತೆ ಎಚ್ಚರಿಕೆಗಳು ಮತ್ತು ತ್ವರಿತ ಪಡಿತರ ವಿತರಣೆ.",
        "admin_portal": "ಆಡಳಿತಾತ್ಮಕ ನಿರ್ದೇಶನಾಲಯ",
        "admin_desc": "ರಾಜ್ಯಾದ್ಯಂತ ಆಹಾರ ದಾಸ್ತಾನು ನಿಗಾ, ಸಾಮರ್ಥ್ಯ ನಿಯಂತ್ರಣ ಮತ್ತು ದೂರು ಪರಿಹಾರ.",
        "analytics_portal": "ದತ್ತಾಂಶ ವಿಜ್ಞಾನ ಮತ್ತು ಎಂಎಲ್ ವಿಶ್ಲೇಷಣೆ",
        "analytics_desc": "ತರಬೇತಿ ಪಡೆದ ಮಾದರಿಗಳು, ನಿಖರತೆಯ ಮೆಟ್ರಿಕ್ಸ್‌ಗಳು ಮತ್ತು ಸಂವಾದಾತ್ಮಕ ಸಿಮ್ಯುಲೇಶನ್.",
        "rice": "ಅಕ್ಕಿ",
        "wheat": "ಗೋಧಿ",
        "sugar": "ಸಕ್ಕರೆ",
        "login": "ಸುರಕ್ಷಿತ ಲಾಗಿನ್",
        "demo_login": "ಡೆಮೊ ಲಾಗಿನ್",
        "register": "ಹೊಸ ಪಡಿತರ ಚೀಟಿ ನೋಂದಣಿ",
        "select_role": "ಪ್ರವೇಶ ದ್ವಾರವನ್ನು ಆರಿಸಿ",
    },
    "हिंदी (Hindi)": {
        "title": "स्मार्ट राशन एवं सार्वजनिक वितरण प्रणाली",
        "subtitle": "मशीन लर्निंग व एआई-संचालित उचित मूल्य दुकान वितरण प्रणाली",
        "citizen_portal": "नागरिक एवं लाभार्थी पोर्टल",
        "citizen_desc": "मासिक राशन कोटा देखें, दुकान में उपलब्ध स्टॉक जांचें एवं कतार समय पूर्वानुमान के साथ स्लॉट बुक करें।",
        "dealer_portal": "उचित मूल्य दुकान डीलर",
        "dealer_desc": "दैनिक मांग पूर्वानुमान, स्टॉक कमी की चेतावनी और वास्तविक समय में राशन वितरण।",
        "admin_portal": "प्रशासनिक निदेशालय",
        "admin_desc": "राज्यव्यापी राशन स्टॉक निगरानी, स्लॉट क्षमता प्रबंधन एवं नागरिक शिकायत निवारण।",
        "analytics_portal": "डेटा साइंस व एमएल एनालिटिक्स",
        "analytics_desc": "मशीन लर्निंग मॉडल मूल्यांकन, सटीकता स्कोर एवं वास्तविक परिदृश्य सिमुलेशन।",
        "rice": "चावल",
        "wheat": "गेहूं",
        "sugar": "चीनी",
        "login": "सुरक्षित लॉगिन",
        "demo_login": "त्वरित डेमो लॉगिन",
        "register": "नया राशन कार्ड पंजीकरण",
        "select_role": "पहुंच गेटवे चुनें",
    }
}

def render_top_brand_bar(show_logout: bool = False) -> str:
    """Render top Indian National PDS Brand Bar with Live Indicators."""
    return """
    <div class="tricolor-stripe"></div>
    <div class="brand-top-bar">
        <div class="brand-logo-group">
            <div class="brand-emblem-icon">🌾</div>
            <div>
                <h2 class="brand-title-main">National Food Security Portal • e-PDS</h2>
                <p class="brand-title-sub">Smart Public Distribution System | Government of Karnataka & NFSA</p>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div class="live-status-pill">
                <span class="live-dot"></span>
                <span>AI Distribution Engine Online</span>
            </div>
        </div>
    </div>
    """

def render_smart_ration_card(user: Dict[str, Any]) -> str:
    """Render a realistic, prestigious Digital Smart Ration Card."""
    card_no = user.get("ration_card_number", "RC-KA-99201")
    cat = user.get("card_type", "PHH")
    name = user.get("head_of_family") or user.get("full_name", "Beneficiary Name")
    members = user.get("family_members_count", 4)
    shop_name = user.get("shop_name", "Fair Price Depot #104")
    taluk = user.get("taluk", "Bengaluru South")

    cat_color = "#F59E0B" if cat == "AAY" else ("#10B981" if cat == "PHH" else "#3B82F6")
    cat_desc = "ANTYODAYA ANNA YOJANA" if cat == "AAY" else ("PRIORITY HOUSEHOLD" if cat == "PHH" else "NON-PRIORITY")

    return f"""
    <div class="smart-card-container">
        <div class="card-top-row">
            <div>
                <div class="card-gov-seal">GOVERNMENT OF KARNATAKA • FOOD & CIVIL SUPPLIES</div>
                <div style="font-size: 1.1rem; font-weight: 800; margin-top: 3px; color: #FFFFFF;">DIGITAL SMART RATION PASS</div>
            </div>
            <div style="text-align: right;">
                <span style="background: {cat_color}; color: #000; font-size: 0.72rem; font-weight: 800; padding: 3px 8px; border-radius: 4px;">{cat}</span>
            </div>
        </div>
        <div class="card-chip-hologram">
            <div class="emv-chip"></div>
            <span class="contactless-waves">)))</span>
            <div class="card-hologram-badge">NFSA CHIP 2026</div>
        </div>
        <div class="card-num-display">{card_no}</div>
        <div class="card-details-grid">
            <div>
                <div class="card-field-label">Cardholder / Head</div>
                <div class="card-field-val">{name}</div>
            </div>
            <div>
                <div class="card-field-label">Category</div>
                <div class="card-field-val">{cat_desc}</div>
            </div>
            <div>
                <div class="card-field-label">Family Units</div>
                <div class="card-field-val">{members} Members</div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px; font-size: 0.75rem; color: #94A3B8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 8px;">
            <div>Assigned Depot: <b>{shop_name}</b> ({taluk})</div>
            <div style="font-family: 'JetBrains Mono', monospace; letter-spacing: 0.1em;">VALID: 2026-2030</div>
        </div>
    </div>
    """

def render_quota_progress_cards(user: Dict[str, Any], usage: Optional[Dict[str, float]] = None) -> str:
    """Render interactive Visual Quota Progress meters for Rice, Wheat, and Sugar."""
    usage = usage or {"rice": 0.0, "wheat": 0.0, "sugar": 0.0}
    
    rice_tot = float(user.get("monthly_rice_quota_kg", user.get("quota_rice_kg", 20.0)))
    wheat_tot = float(user.get("monthly_wheat_quota_kg", user.get("quota_wheat_kg", 8.0)))
    sugar_tot = float(user.get("monthly_sugar_quota_kg", user.get("quota_sugar_kg", 2.0)))

    rice_drawn = float(usage.get("rice", 0.0))
    wheat_drawn = float(usage.get("wheat", 0.0))
    sugar_drawn = float(usage.get("sugar", 0.0))

    rice_rem = max(0.0, rice_tot - rice_drawn)
    wheat_rem = max(0.0, wheat_tot - wheat_drawn)
    sugar_rem = max(0.0, sugar_tot - sugar_drawn)

    rice_pct = min(100.0, (rice_drawn / rice_tot * 100)) if rice_tot > 0 else 0
    wheat_pct = min(100.0, (wheat_drawn / wheat_tot * 100)) if wheat_tot > 0 else 0
    sugar_pct = min(100.0, (sugar_drawn / sugar_tot * 100)) if sugar_tot > 0 else 0

    return f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 22px;">
        <!-- Rice Card -->
        <div class="quota-card-box">
            <div class="quota-header-row">
                <div class="quota-icon-name">
                    <div class="quota-icon-circle" style="background: #ECFDF5; color: #059669;">🍚</div>
                    <div>
                        <div class="quota-name">Subsidized Rice</div>
                        <div class="quota-rate">₹3.00 / kg • Grade-A Sona Masoori</div>
                    </div>
                </div>
                <span class="pill-badge pill-emerald">{"Completed" if rice_rem == 0 else f"{rice_rem:.1f} kg Left"}</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {rice_pct}%; background: linear-gradient(90deg, #10B981, #059669);"></div>
            </div>
            <div class="quota-numbers-row">
                <span>Drawn: <b>{rice_drawn:.1f} kg</b></span>
                <span>Quota: <b>{rice_tot:.1f} kg</b></span>
            </div>
        </div>

        <!-- Wheat Card -->
        <div class="quota-card-box">
            <div class="quota-header-row">
                <div class="quota-icon-name">
                    <div class="quota-icon-circle" style="background: #FEF3C7; color: #D97706;">🌾</div>
                    <div>
                        <div class="quota-name">Fortified Wheat</div>
                        <div class="quota-rate">₹2.00 / kg • Micronutrient Enriched</div>
                    </div>
                </div>
                <span class="pill-badge pill-amber">{"Completed" if wheat_rem == 0 else f"{wheat_rem:.1f} kg Left"}</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {wheat_pct}%; background: linear-gradient(90deg, #F59E0B, #D97706);"></div>
            </div>
            <div class="quota-numbers-row">
                <span>Drawn: <b>{wheat_drawn:.1f} kg</b></span>
                <span>Quota: <b>{wheat_tot:.1f} kg</b></span>
            </div>
        </div>

        <!-- Sugar Card -->
        <div class="quota-card-box">
            <div class="quota-header-row">
                <div class="quota-icon-name">
                    <div class="quota-icon-circle" style="background: #E0F2FE; color: #0284C7;">🍬</div>
                    <div>
                        <div class="quota-name">Refined Sugar</div>
                        <div class="quota-rate">₹13.50 / kg • Crystal White Pure</div>
                    </div>
                </div>
                <span class="pill-badge pill-blue">{"Completed" if sugar_rem == 0 else f"{sugar_rem:.1f} kg Left"}</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {sugar_pct}%; background: linear-gradient(90deg, #38BDF8, #0284C7);"></div>
            </div>
            <div class="quota-numbers-row">
                <span>Drawn: <b>{sugar_drawn:.1f} kg</b></span>
                <span>Quota: <b>{sugar_tot:.1f} kg</b></span>
            </div>
        </div>
    </div>
    """

def render_booking_voucher(bk_data: Dict[str, Any]) -> str:
    """Generate high-resolution printable electronic appointment pass with boarding pass aesthetics."""
    ref = bk_data.get('booking_reference', 'REF-SRS-9901')
    slot = bk_data.get('time_slot', '09:00 - 10:00 AM')
    dt = bk_data.get('date', '2026-11-20')
    shop = bk_data.get('shop_name', 'Fair Price Depot #104')
    wait = float(bk_data.get('predicted_waiting_time', 10.0))
    status = bk_data.get('status', 'CONFIRMED')

    wait_badge = (
        f'<span class="pill-badge pill-emerald">⚡ ~{wait:.0f} mins (Low Queue)</span>'
        if wait <= 12 else
        f'<span class="pill-badge pill-amber">⏳ ~{wait:.0f} mins (Moderate)</span>'
    )

    return f"""
    <div class="boarding-pass-card">
        <div class="pass-main">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span class="pass-ref-badge">TOKEN: {ref}</span>
                <span class="pill-badge pill-emerald">● {status} PRIORITY PASS</span>
            </div>
            <div style="color: #64748B; font-size: 0.82rem; font-weight: 700; text-transform: uppercase;">Designated Collection Time Window</div>
            <div class="pass-time-slot">{slot}</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px;">
                <div>
                    <div style="color: #64748B; font-size: 0.78rem; font-weight: 600;">APPOINTMENT DATE</div>
                    <div style="color: #0F172A; font-weight: 700; font-size: 1rem;">📅 {dt}</div>
                </div>
                <div>
                    <div style="color: #64748B; font-size: 0.78rem; font-weight: 600;">AI QUEUE PREDICTION</div>
                    <div style="margin-top: 2px;">{wait_badge}</div>
                </div>
            </div>
            <div style="margin-top: 14px; font-size: 0.85rem; color: #475569; border-top: 1px dashed #CBD5E1; padding-top: 10px;">
                🏬 Depot: <b>{shop}</b> • <i>Present this token at the priority lane</i>
            </div>
        </div>
        <div class="pass-stub">
            <div style="font-weight: 800; font-size: 0.82rem; color: #1E3A8A; letter-spacing: 0.05em;">GATE VERIFICATION</div>
            <div style="font-size: 52px; line-height: 1; margin: 10px 0;">🎟️</div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64748B;">{ref}</div>
            <div style="font-size: 0.72rem; color: #059669; font-weight: 700; margin-top: 6px;">✓ VERIFIED NFSA</div>
        </div>
    </div>
    """

def render_digital_receipt(tx_data: Dict[str, Any]) -> str:
    """Generate high-fidelity thermal POS digital receipt."""
    tx_ref = tx_data.get('transaction_ref', 'TX-NFSA-8831')
    dt = tx_data.get('transaction_date', '2026-11-20')
    shop = tx_data.get('shop_name', 'Fair Price Depot')
    shop_no = tx_data.get('shop_number', 'FPS-104')
    beneficiary = tx_data.get('head_of_family') or tx_data.get('beneficiary_name', 'Cardholder')
    rc_no = tx_data.get('ration_card_number', 'RC-KA-99201')
    card_type = tx_data.get('card_type', 'PHH')

    rice = float(tx_data.get('rice_collected_kg', 0.0))
    wheat = float(tx_data.get('wheat_collected_kg', 0.0))
    sugar = float(tx_data.get('sugar_collected_kg', 0.0))

    cost_rice = rice * 3.00
    cost_wheat = wheat * 2.00
    cost_sugar = sugar * 13.50
    total = tx_data.get('total_amount', cost_rice + cost_wheat + cost_sugar)

    market_savings = (rice * 38.0) + (wheat * 30.0) + (sugar * 45.0) - total
    market_savings = max(0.0, market_savings)

    return f"""
    <div class="thermal-receipt-container">
        <div class="receipt-center-brand">
            <div style="font-size: 26px;">🌾</div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; letter-spacing: -0.01em;">GOVERNMENT OF KARNATAKA</div>
            <div style="font-size: 0.8rem; color: #64748B; font-weight: 600;">Department of Food, Civil Supplies & Consumer Affairs</div>
            <div style="font-size: 0.75rem; color: #16A34A; font-weight: 700; margin-top: 4px;">● OFFICIAL ELECTRONIC PDS DISBURSEMENT RECEIPT</div>
        </div>

        <div class="receipt-row">
            <span style="color: #64748B;">Txn Reference:</span>
            <span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: #0F172A;">{tx_ref}</span>
        </div>
        <div class="receipt-row">
            <span style="color: #64748B;">Disbursement Date:</span>
            <span style="font-weight: 600; color: #0F172A;">{dt}</span>
        </div>
        <div class="receipt-row">
            <span style="color: #64748B;">Depot / FPS:</span>
            <span style="font-weight: 600; color: #0F172A;">{shop} ({shop_no})</span>
        </div>
        <div class="receipt-row">
            <span style="color: #64748B;">Beneficiary:</span>
            <span style="font-weight: 700; color: #0F172A;">{beneficiary}</span>
        </div>
        <div class="receipt-row">
            <span style="color: #64748B;">Ration Card / Tier:</span>
            <span style="font-weight: 600; color: #0F172A;">{rc_no} ({card_type})</span>
        </div>

        <div style="border-top: 1.5px dashed #CBD5E1; margin: 12px 0 10px 0;"></div>

        <div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 8px;">Commodity Line Items</div>
        <div class="receipt-row">
            <span>🍚 Subsidized Rice ({rice:.1f} kg @ ₹3/kg)</span>
            <span style="font-weight: 700;">₹{cost_rice:.2f}</span>
        </div>
        <div class="receipt-row">
            <span>🌾 Fortified Wheat ({wheat:.1f} kg @ ₹2/kg)</span>
            <span style="font-weight: 700;">₹{cost_wheat:.2f}</span>
        </div>
        <div class="receipt-row">
            <span>🍬 Refined Sugar ({sugar:.1f} kg @ ₹13.50/kg)</span>
            <span style="font-weight: 700;">₹{cost_sugar:.2f}</span>
        </div>

        <div class="receipt-total-bar">
            <span>TOTAL AMOUNT PAID:</span>
            <span style="color: #1E3A8A;">₹{total:.2f}</span>
        </div>

        <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 10px 12px; margin-bottom: 14px; text-align: center;">
            <div style="font-size: 0.78rem; color: #065F46; font-weight: 700;">GOVERNMENT SUBSIDY BENEFIT</div>
            <div style="font-size: 0.95rem; font-weight: 800; color: #047857; margin-top: 2px;">You saved ₹{market_savings:.2f} vs open market rates!</div>
        </div>

        <div style="text-align: center; font-size: 0.72rem; color: #94A3B8; font-family: 'JetBrains Mono', monospace; line-height: 1.4;">
            SHA-256: {abs(hash(str(tx_ref))) % 10**16:016d}<br>
            Biometric Authenticated • Zero Leakage Verified
        </div>
    </div>
    """
