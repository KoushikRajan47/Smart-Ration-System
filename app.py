"""
Smart Ration and Distribution System - Full-Stack Interactive Streamlit Application.
Engineered with role-dedicated login gateways, modern UI styling, multilingual support,
digital receipt generation, SMS alert dispatching, and machine learning analytics.
"""
import sys
import os
import subprocess
from pathlib import Path

# Auto-detect bare python execution (e.g. `python app.py` or VS Code Run button)
# and seamlessly redirect to `streamlit run app.py`
if __name__ == "__main__":
    if "SMART_RATION_SPAWNED" not in os.environ:
        try:
            from streamlit.runtime import exists as streamlit_runtime_exists
            if not streamlit_runtime_exists():
                os.environ["SMART_RATION_SPAWNED"] = "1"
                cmd = [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve()), "--server.headless=true", "--server.port=8501"] + sys.argv[1:]
                subprocess.run(cmd)
                sys.exit(0)
        except Exception:
            pass

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json

# Add root directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib
import config.settings
importlib.reload(config.settings)
import database.db
importlib.reload(database.db)
import services.auth_service
importlib.reload(services.auth_service)
import services.prediction_service
importlib.reload(services.prediction_service)
import services.stock_service
importlib.reload(services.stock_service)
import services.recommendation_service
importlib.reload(services.recommendation_service)
import services.ui_components
importlib.reload(services.ui_components)
import services.communication_service
importlib.reload(services.communication_service)

from config.settings import (
    OPERATIONAL_SLOTS,
    SLOT_HOUR_MAP,
    COMMODITY_QUOTAS,
    REPORTS_DIR,
    METRICS_REPORT_PATH,
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_SENDER_EMAIL
)
from database.db import (
    get_user_by_username,
    get_beneficiary_details,
    get_dealer_details,
    get_all_shops,
    get_shop_by_id,
    get_shop_inventory,
    update_stock,
    get_day_slot_capacities,
    create_booking,
    cancel_booking,
    get_beneficiary_bookings,
    get_shop_bookings_for_date,
    record_transaction,
    get_beneficiary_transactions,
    get_shop_transactions,
    list_all_beneficiaries,
    get_recent_prediction_logs,
    register_new_beneficiary,
    create_notification,
    get_user_notifications,
    get_all_complaints,
    get_beneficiary_complaints,
    get_beneficiary_monthly_usage,
    resolve_complaint,
    get_transaction_by_ref,
    get_connection
)
from services.auth_service import authenticate_user
from services.prediction_service import (
    predict_slot_comprehensive,
    predict_crowd,
    predict_rice_demand,
    predict_wheat_demand,
    predict_sugar_demand,
    predict_waiting_time
)
from services.stock_service import analyze_shop_stock_shortages
from services.recommendation_service import get_slot_recommendations
from services.ui_components import (
    CUSTOM_CSS,
    TRANSLATIONS,
    render_digital_receipt,
    render_booking_voucher,
    render_top_brand_bar,
    render_smart_ration_card,
    render_quota_progress_cards
)
from services.communication_service import (
    send_email,
    send_booking_reminder_email,
    send_purchase_receipt_email,
    send_instant_sms,
    send_whatsapp_message
)

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Smart Ration & Distribution System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "selected_role_tab" not in st.session_state:
    st.session_state.selected_role_tab = "citizen"
if "language" not in st.session_state:
    st.session_state.language = "English"
if "guest_analytics" not in st.session_state:
    st.session_state.guest_analytics = False

# Live Communication Gateway Credentials
if "smtp_server" not in st.session_state:
    st.session_state.smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
if "smtp_port" not in st.session_state:
    st.session_state.smtp_port = int(os.environ.get("SMTP_PORT", 587))
if "smtp_user" not in st.session_state:
    st.session_state.smtp_user = os.environ.get("SMTP_USERNAME", "")
if "smtp_pass" not in st.session_state:
    st.session_state.smtp_pass = os.environ.get("SMTP_PASSWORD", "")
if "fast2sms_key" not in st.session_state:
    st.session_state.fast2sms_key = os.environ.get("FAST2SMS_API_KEY", "")
if "twilio_sid" not in st.session_state:
    st.session_state.twilio_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
if "twilio_token" not in st.session_state:
    st.session_state.twilio_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
if "twilio_from" not in st.session_state:
    st.session_state.twilio_from = os.environ.get("TWILIO_FROM_NUMBER", "")
if "callmebot_key" not in st.session_state:
    st.session_state.callmebot_key = os.environ.get("CALLMEBOT_API_KEY", "")

def app_send_sms(to_phone: str, message: str, user_id: Optional[int] = None) -> Tuple[bool, str]:
    """Helper to dispatch SMS or WhatsApp using active session credentials."""
    # If CallMeBot key is configured, also deliver directly via WhatsApp
    if st.session_state.get("callmebot_key"):
        ok_w, msg_w = send_whatsapp_message(
            to_phone=to_phone,
            message=message,
            callmebot_apikey=st.session_state.get("callmebot_key"),
            user_id=user_id
        )
        if ok_w:
            return True, f"Live WhatsApp message delivered to +91-{to_phone}!"

    return send_instant_sms(
        to_phone=to_phone,
        message=message,
        user_id=user_id,
        fast2sms_key=st.session_state.get("fast2sms_key"),
        twilio_sid=st.session_state.get("twilio_sid"),
        twilio_token=st.session_state.get("twilio_token"),
        twilio_from=st.session_state.get("twilio_from")
    )

def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.guest_analytics = False
    st.rerun()

# Multilingual Dictionary Shortcut
T = TRANSLATIONS.get(st.session_state.language, TRANSLATIONS["English"])

# --- TOP BRAND & REGULATORY BAR ---
st.markdown(render_top_brand_bar(), unsafe_allow_html=True)

# Secondary Language & Quick Status Bar
col_lang, col_status = st.columns([3, 1])
with col_lang:
    selected_lang = st.selectbox(
        "🌐 Language / ಭಾಷೆ / भाषा",
        ["English", "ಕನ್ನಡ (Kannada)", "हिंदी (Hindi)"],
        index=["English", "ಕನ್ನಡ (Kannada)", "हिंदी (Hindi)"].index(st.session_state.language),
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

with col_status:
    if st.session_state.authenticated:
        role_title = st.session_state.user.get("role", "user").upper()
        st.markdown(f"<div style='text-align: right; margin-top: 4px;'><span class='pill-badge pill-emerald'>● {role_title} ACTIVE</span></div>", unsafe_allow_html=True)
    elif st.session_state.guest_analytics:
        st.markdown("<div style='text-align: right; margin-top: 4px;'><span class='pill-badge pill-amber'>● ANALYST EXPLORER</span></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: right; margin-top: 4px;'><span class='pill-badge pill-blue'>● SYSTEM ONLINE</span></div>", unsafe_allow_html=True)

# ==============================================================================
# LANDING PAGE: MODERN GOVTECH SAAS PORTAL
# ==============================================================================
def render_landing_portal():
    # Hero Section
    st.markdown("""
    <div class="hero-banner">
        <h1 class="hero-title">🌾 Smart Public Distribution & Ration Allocation System</h1>
        <div class="hero-subtitle">
            Next-Generation Fair Price Shop Platform • Machine Learning Queue Optimization • Real-Time Grain Inventory Telemetry • Zero Leakage Digital Entitlements
        </div>
        <div class="hero-chips-row">
            <span class="hero-chip">🤖 5 Scikit-Learn Regression Models</span>
            <span class="hero-chip">⏱️ Smart Waiting Time Minimization</span>
            <span class="hero-chip">📲 SMS & WhatsApp Priority Digital Passes</span>
            <span class="hero-chip">⚖️ 100% Transparent Citizen Redressal</span>
            <span class="hero-chip">🛡️ Biometric e-KYC Verified</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([5, 6], gap="large")

    with col_left:
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 18px; padding: 22px 24px; border: 1px solid #E2E8F0; box-shadow: 0 4px 14px rgba(0,0,0,0.03); margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #0F172A; font-weight: 800; font-size: 1.2rem;">⚡ 1-Click Fast Track Demo Portals</h3>
                <span class="pill-badge pill-blue">INSTANT ACCESS</span>
            </div>
            <p style="color: #64748B; font-size: 0.88rem; margin: 0; line-height: 1.5;">
                Test all interactive features with full permissions using the pre-configured role personas below:
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Citizen Persona
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 14px; padding: 16px 20px; border: 1px solid #E2E8F0; box-shadow: 0 2px 6px rgba(0,0,0,0.02); margin-bottom: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 26px;">👤</span>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; font-size: 1.02rem;">Anand Kumar (Beneficiary)</div>
                        <div style="font-size: 0.78rem; color: #64748B;">Card: <b>RC-KA-99201</b> • Bengaluru South</div>
                    </div>
                </div>
                <span class="pill-badge pill-amber">AAY Antyodaya</span>
            </div>
            <div style="font-size: 0.82rem; color: #475569; line-height: 1.4; margin-bottom: 8px;">
                Check 20kg rice & 8kg wheat entitlements, book collection slot with AI queue predictions, and download digital passes.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Sign In as Citizen Anand", key="fast_ben_btn", type="primary", use_container_width=True):
            ctx = authenticate_user("citizen1", "citizenpassword")
            if ctx:
                st.session_state.authenticated = True
                st.session_state.user = ctx
                st.rerun()

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

        # Dealer Persona
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 14px; padding: 16px 20px; border: 1px solid #E2E8F0; box-shadow: 0 2px 6px rgba(0,0,0,0.02); margin-bottom: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 26px;">🏪</span>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; font-size: 1.02rem;">Ramesh Gowda (Depot Dealer)</div>
                        <div style="font-size: 0.78rem; color: #64748B;">Depot #104 • 4 Active Counters</div>
                    </div>
                </div>
                <span class="pill-badge pill-emerald">FPS Operator</span>
            </div>
            <div style="font-size: 0.82rem; color: #475569; line-height: 1.4; margin-bottom: 8px;">
                Forecast daily demand, disburse rations at e-POS with real-time stock deductions, and dispatch SMS collection receipts.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏪 Sign In as Dealer Ramesh", key="fast_dlr_btn", use_container_width=True):
            ctx = authenticate_user("dealer1", "dealerpassword")
            if ctx:
                st.session_state.authenticated = True
                st.session_state.user = ctx
                st.rerun()

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

        # Admin Persona
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 14px; padding: 16px 20px; border: 1px solid #E2E8F0; box-shadow: 0 2px 6px rgba(0,0,0,0.02); margin-bottom: 12px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 26px;">🏛️</span>
                    <div>
                        <div style="font-weight: 800; color: #0F172A; font-size: 1.02rem;">Dr. Rajesh Sharma (Director)</div>
                        <div style="font-size: 0.78rem; color: #64748B;">State Food & Civil Supplies Directorate</div>
                    </div>
                </div>
                <span class="pill-badge pill-blue">Directorate HQ</span>
            </div>
            <div style="font-size: 0.82rem; color: #475569; line-height: 1.4; margin-bottom: 8px;">
                Monitor statewide depot network, tune slot capacity limits, resolve citizen grievances with 1 click, and audit ML telemetry.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏛️ Sign In as Director Sharma", key="fast_adm_btn", use_container_width=True):
            ctx = authenticate_user("admin", "adminpassword")
            if ctx:
                st.session_state.authenticated = True
                st.session_state.user = ctx
                st.rerun()

    with col_right:
        landing_tabs = st.tabs([
            "🔐 Official Sign In",
            "📝 Apply for Digital Card",
            "📊 Public ML Studio"
        ])

        # TAB 1: OFFICIAL CREDENTIAL LOGIN
        with landing_tabs[0]:
            st.markdown("""
            <div style="margin-bottom: 14px;">
                <h4 style="margin: 0; color: #0F172A; font-weight: 800;">Portal Sign In</h4>
                <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.88rem;">
                    Sign in with your username or 12-character Ration Card Number (e.g. <code>RC-KA-99201</code>).
                </p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("unified_login_form"):
                u_in = st.text_input("Username or Ration Card Number", placeholder="e.g. citizen1, dealer1, admin, or RC-KA-99201")
                p_in = st.text_input("Account Password", type="password", placeholder="Enter your password")
                
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                submit_btn = st.form_submit_button("🔑 Secure Sign In to Portal", type="primary", use_container_width=True)

                if submit_btn:
                    if u_in.strip() and p_in.strip():
                        ctx = authenticate_user(u_in.strip(), p_in.strip())
                        if ctx:
                            st.session_state.authenticated = True
                            st.session_state.user = ctx
                            st.toast(f"Welcome, {ctx['full_name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Please verify your username and password, or use the 1-click demo buttons on the left.")
                    else:
                        st.warning("Please provide both username and password.")

            st.markdown("""
            <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 14px 18px; margin-top: 16px;">
                <div style="font-size: 0.8rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Standard Test Credentials</div>
                <div style="font-size: 0.85rem; color: #334155; margin-top: 4px; line-height: 1.5;">
                    • <b>Citizen:</b> <code>citizen1</code> / <code>citizenpassword</code> (or card <code>RC-KA-99201</code>)<br>
                    • <b>Dealer:</b> <code>dealer1</code> / <code>dealerpassword</code><br>
                    • <b>Admin:</b> <code>admin</code> / <code>adminpassword</code>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # TAB 2: SELF REGISTRATION
        with landing_tabs[1]:
            st.markdown("""
            <div style="margin-bottom: 14px;">
                <h4 style="margin: 0; color: #0F172A; font-weight: 800;">Digital Ration Card Self-Registration</h4>
                <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.88rem;">
                    Apply for an electronic digital ration card under the National Food Security Act (NFSA).
                </p>
            </div>
            """, unsafe_allow_html=True)

            shops = get_all_shops()
            shop_dict = {f"{s['shop_name']} ({s['shop_number']}) - {s['taluk']}": s["id"] for s in shops}

            with st.form("self_reg_form"):
                r_c1, r_c2 = st.columns(2)
                with r_c1:
                    new_username = st.text_input("Choose Username *", placeholder="e.g. suresh_k")
                    full_name = st.text_input("Full Name *", placeholder="e.g. Suresh Kumar")
                    card_no = st.text_input("Ration Card Number *", placeholder="e.g. RC-KA-77312")
                    phone = st.text_input("Mobile Phone (for SMS Token) *", placeholder="10-digit mobile")
                with r_c2:
                    new_password = st.text_input("Choose Password *", type="password", placeholder="Minimum 6 characters")
                    head_family = st.text_input("Head of Family Name *", placeholder="e.g. Suresh Kumar")
                    email = st.text_input("Email Address", placeholder="user@domain.com")
                    card_type = st.selectbox("Category *", ["PHH (Priority Household)", "AAY (Antyodaya Anna Yojana)", "NPHH (Non-Priority Household)"])

                m_c1, m_c2 = st.columns(2)
                with m_c1:
                    members_count = st.number_input("Total Family Members Count *", min_value=1, max_value=15, value=4)
                with m_c2:
                    assigned_shop = st.selectbox("Designated Fair Price Depot *", list(shop_dict.keys()))

                address = st.text_area("Residential Address *", placeholder="Door No, Street Name, Ward, Taluk, Bengaluru")

                # Live Entitlement Calculation Preview
                card_code = "AAY" if "AAY" in card_type else ("PHH" if "PHH" in card_type else "NPHH")
                if card_code == "AAY":
                    e_rice, e_wheat, e_sugar = 20.0, 8.0, 2.0
                elif card_code == "PHH":
                    e_rice, e_wheat, e_sugar = members_count * 4.0, members_count * 2.0, 1.0
                else:
                    e_rice, e_wheat, e_sugar = 10.0, 4.0, 1.0

                st.markdown(f"""
                <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 10px; padding: 12px 16px; margin: 12px 0;">
                    <div style="font-size: 0.78rem; font-weight: 700; color: #065F46; text-transform: uppercase;">Authorized Monthly Quota Preview ({card_code})</div>
                    <div style="font-size: 0.95rem; font-weight: 800; color: #047857; margin-top: 2px;">
                        🍚 Rice: {e_rice:.1f} kg | 🌾 Wheat: {e_wheat:.1f} kg | 🍬 Sugar: {e_sugar:.1f} kg
                    </div>
                </div>
                """, unsafe_allow_html=True)

                submit_reg = st.form_submit_button("📋 Submit Application & Activate Card", type="primary", use_container_width=True)
                if submit_reg:
                    if not (new_username and new_password and full_name and card_no and phone and address):
                        st.error("Please fill in all mandatory fields marked with (*).")
                    else:
                        target_shop_id = shop_dict[assigned_shop]
                        ok, msg = register_new_beneficiary(
                            username=new_username,
                            raw_password=new_password,
                            full_name=full_name,
                            email=email,
                            phone=phone,
                            ration_card_number=card_no,
                            card_type=card_code,
                            head_of_family=head_family,
                            family_members_count=int(members_count),
                            shop_id=target_shop_id,
                            address=address
                        )
                        if ok:
                            st.success(f"🎉 {msg}")
                            st.info("Your digital ration card is active! You can now switch to 'Official Sign In' tab to log in.")
                        else:
                            st.error(msg)

        # TAB 3: PUBLIC ML STUDIO GUEST EXPLORER
        with landing_tabs[2]:
            st.markdown("""
            <div style="margin-bottom: 16px;">
                <h4 style="margin: 0; color: #0F172A; font-weight: 800;">Public Data Science & ML Studio</h4>
                <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.88rem;">
                    Inspect our 5 trained machine learning models, cross-validation metrics, and interactive what-if simulation sandbox without signing in.
                </p>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 18px 20px; margin-bottom: 18px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div>
                        <div style="font-size: 0.75rem; color: #64748B; font-weight: 700;">TRAINED MODELS</div>
                        <div style="font-weight: 800; color: #0F172A; font-size: 1.1rem;">5 Regressors</div>
                    </div>
                    <div>
                        <div style="font-size: 0.75rem; color: #64748B; font-weight: 700;">MODEL ACCURACY</div>
                        <div style="font-weight: 800; color: #059669; font-size: 1.1rem;">R² > 0.94</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 Launch Data Science & ML Analytics Studio", type="primary", use_container_width=True):
                st.session_state.guest_analytics = True
                st.rerun()

# ==============================================================================
# VIEW: BENEFICIARY PORTAL (LOGGED IN)
# ==============================================================================
def render_authenticated_beneficiary():
    user = dict(st.session_state.user) if st.session_state.user else {}
    ben_id = user.get("beneficiary_id") or user.get("id") or 1
    shop_id = user.get("shop_id", 1)
    my_bks = [dict(b) for b in get_beneficiary_bookings(ben_id)]
    monthly_usage = get_beneficiary_monthly_usage(ben_id)

    # Top Section: Smart Ration Card + Live Overview Deck
    col_card, col_metrics = st.columns([1.1, 1], gap="medium")
    with col_card:
        st.markdown(render_smart_ration_card(user), unsafe_allow_html=True)
    with col_metrics:
        active_bks = [b for b in my_bks if b.get("status") == "CONFIRMED"]
        next_bk = active_bks[0] if active_bks else None
        
        st.markdown(f"""
        <div style="background: #FFFFFF; border-radius: 18px; padding: 22px 24px; border: 1px solid #E2E8F0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #64748B; letter-spacing: 0.05em;">BENEFICIARY ACCOUNT DASHBOARD</span>
                    <span class="pill-badge pill-emerald">● e-KYC VERIFIED</span>
                </div>
                <h3 style="margin: 0; color: #0F172A; font-weight: 800; font-size: 1.35rem;">{user.get('full_name', 'Beneficiary')}</h3>
                <p style="margin: 4px 0 14px 0; color: #64748B; font-size: 0.88rem;">
                    Registered Mobile: <b>+91-{user.get('phone', 'N/A')}</b> • Ward: <b>{user.get('taluk', 'Central')}</b>
                </p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px;">
                    <div style="background: #F8FAFC; padding: 10px 14px; border-radius: 10px; border: 1px solid #E2E8F0;">
                        <div style="font-size: 0.72rem; color: #64748B; font-weight: 700;">ASSIGNED DEPOT</div>
                        <div style="font-weight: 700; color: #1E3A8A; font-size: 0.92rem; margin-top: 2px;">{user.get('shop_name', 'Fair Price Depot')}</div>
                    </div>
                    <div style="background: #F8FAFC; padding: 10px 14px; border-radius: 10px; border: 1px solid #E2E8F0;">
                        <div style="font-size: 0.72rem; color: #64748B; font-weight: 700;">FAMILY ENTITLEMENT</div>
                        <div style="font-weight: 700; color: #0F172A; font-size: 0.92rem; margin-top: 2px;">{user.get('family_members_count', 4)} Registered Units</div>
                    </div>
                </div>
            </div>
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 0.72rem; color: #1E40AF; font-weight: 700;">NEXT APPOINTMENT PASS</div>
                    <div style="font-weight: 800; color: #1E3A8A; font-size: 0.92rem; margin-top: 2px;">
                        {"📅 " + next_bk['date'] + " (" + next_bk['time_slot'] + ")" if next_bk else "No active slot reserved"}
                    </div>
                </div>
                <div>
                    {"<span class='pill-badge pill-emerald'>CONFIRMED</span>" if next_bk else "<span class='pill-badge pill-amber'>PENDING</span>"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Visual Quota Progress Section
    st.markdown("#### 🌾 Monthly Foodgrain Entitlements & Allocation Quota")
    st.markdown(render_quota_progress_cards(user, monthly_usage), unsafe_allow_html=True)

    ben_tabs = st.tabs([
        "📅 Smart Slot Booking & Predictions",
        "🎟️ Active Appointments & Passes",
        "🌾 Monthly Entitlements & Depot Stock",
        "📜 Collection Receipts",
        "🔔 Notifications & SMS Hub",
        "✍️ Grievance Redressal"
    ])

    # 1. SMART SLOT BOOKING & PREDICTIONS (PRIMARY TAB)
    with ben_tabs[0]:
        st.subheader("Smart Collection Slot Reservation & AI Queue Predictions")
        st.caption("Gradient Boosting machine learning models evaluate predicted customer volume and counter speeds to minimize your queue wait time.")

        c_date, c_status = st.columns([1, 2])
        with c_date:
            sel_date = st.date_input(
                "Select Collection Date",
                min_value=date.today(),
                max_value=date.today() + timedelta(days=7),
                value=date.today() + timedelta(days=1),
                key="ben_book_date"
            )
            d_name = sel_date.strftime("%A")
            is_wknd = 1 if d_name in ["Saturday", "Sunday"] else 0

        with c_status:
            with st.spinner("Analyzing queue patterns with Gradient Boosting models..."):
                recs = get_slot_recommendations(
                    shop_id=shop_id,
                    target_date_str=str(sel_date),
                    day_name=d_name,
                    is_weekend=is_wknd,
                    is_holiday=0
                )
            best = recs.get("best_slot")
            if best:
                st.markdown(f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 14px; padding: 18px 22px;">
                    <div style="color: #166534; font-weight: 800; font-size: 1.15rem;">⭐ AI Recommends: {best['time_slot']} (Optimal Window)</div>
                    <div style="color: #15803D; font-size: 0.95rem; margin-top: 6px;">
                        Expected Waiting Time: <b>~{best['predicted_waiting_time_min']:.1f} mins</b> | Expected Crowd: <b>{best['predicted_customers']:.0f} citizens</b> | Capacity: <b>{best['available_capacity']} slots available</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Interactive Dual-Metric ML Prediction Chart
        fig_pred = go.Figure()
        slot_names = [s["time_slot"] for s in recs["all_slots"]]
        crowds = [s["predicted_customers"] for s in recs["all_slots"]]
        waits = [s["predicted_waiting_time_min"] for s in recs["all_slots"]]
        colors = ["#10B981" if s["time_slot"] == (best["time_slot"] if best else "") else "#3B82F6" for s in recs["all_slots"]]

        fig_pred.add_trace(go.Bar(
            x=slot_names,
            y=crowds,
            name="Expected Footfall (Citizens)",
            marker_color=colors,
            yaxis="y"
        ))
        fig_pred.add_trace(go.Scatter(
            x=slot_names,
            y=waits,
            name="Predicted Queue Wait (Mins)",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=3),
            marker=dict(size=8, color="#D97706"),
            yaxis="y2"
        ))
        fig_pred.update_layout(
            title="AI Slot Telemetry: Customer Footfall & Queue Waiting Time Projections",
            xaxis=dict(title="Operational Time Window"),
            yaxis=dict(title="Expected Footfall (Citizens)"),
            yaxis2=dict(title="Predicted Wait Time (Minutes)", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=340,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(fig_pred, use_container_width=True)

        st.markdown("#### Operational Slots Breakdown")
        slots_df = pd.DataFrame([
            {
                "Time Slot": s["time_slot"],
                "Expected Footfall": f"{s['predicted_customers']:.0f} customers",
                "Predicted Wait": f"{s['predicted_waiting_time_min']:.1f} mins",
                "Booked / Capacity": f"{s['booked_count']} / {s['max_capacity']}",
                "Status": s["tag"],
                "Availability": "🟢 Available" if s["eligible"] else "🔴 Full / Closed"
            }
            for s in recs["all_slots"]
        ])
        st.dataframe(slots_df, use_container_width=True)

        # Check if citizen already has a confirmed booking for this selected date
        existing_user_booking = [dict(b) for b in my_bks if str(b.get("date")) == str(sel_date) and b.get("status") == "CONFIRMED"]

        if existing_user_booking:
            ex = dict(existing_user_booking[0])
            st.markdown(f"""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 18px 22px; margin-top: 15px;">
                <div style="color: #1E40AF; font-weight: 800; font-size: 1.05rem;">ℹ️ Active Reservation Already Exists for {sel_date}</div>
                <div style="color: #1E3A8A; font-size: 0.95rem; margin-top: 6px; line-height: 1.5;">
                    You already have a confirmed appointment on <b>{sel_date}</b> during <b>{ex.get('time_slot', 'N/A')}</b> (Ref: <b>{ex.get('booking_reference', 'N/A')}</b>) at <b>{ex.get('shop_name', user.get('shop_name', 'Fair Price Depot'))}</b>.<br>
                    To select a different time window for this date, please visit the <b>'Active Appointments & Passes'</b> tab to cancel or reschedule your existing slot.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            eligible_slots = [s["time_slot"] for s in recs["all_slots"] if s["eligible"]]
            if eligible_slots:
                st.markdown("#### Confirm Booking")
                c_sel, c_btn = st.columns([2, 1])
                with c_sel:
                    chosen_slot = st.selectbox("Choose Slot to Book", eligible_slots)
                    slot_obj = [s for s in recs["all_slots"] if s["time_slot"] == chosen_slot][0]
                with c_btn:
                    st.write("")
                    st.write("")
                    if st.button("Confirm Slot Reservation", type="primary", use_container_width=True):
                        ok, res = create_booking(
                            beneficiary_id=ben_id,
                            shop_id=shop_id,
                            date_str=str(sel_date),
                            time_slot=chosen_slot,
                            predicted_wait=slot_obj["predicted_waiting_time_min"]
                        )
                        if ok:
                            # Automated Email & SMS Dispatch
                            target_mail = user.get("email") or f"citizen_{user.get('ration_card_number')}@smartration.gov.in"
                            target_phone = user.get("phone", "9876543210")
                            send_booking_reminder_email(
                                beneficiary_email=target_mail,
                                beneficiary_user_id=user["user_id"],
                                head_of_family=user["full_name"],
                                booking_ref=res,
                                date_str=str(sel_date),
                                time_slot=chosen_slot,
                                shop_name=user.get("shop_name", "Fair Price Depot"),
                                predicted_wait=slot_obj["predicted_waiting_time_min"],
                                smtp_user=st.session_state.get("smtp_user"),
                                smtp_pass=st.session_state.get("smtp_pass")
                            )
                            app_send_sms(
                                to_phone=target_phone,
                                message=f"PDS Alert: Slot Confirmed! Ref: {res} for {sel_date} ({chosen_slot}) at {user.get('shop_name')}. Est Wait: {slot_obj['predicted_waiting_time_min']:.0f}m.",
                                user_id=user["user_id"]
                            )
                            st.success(f"🎉 Slot booked successfully! Booking Reference: **{res}**")
                            st.info(f"📧 Confirmation email dispatched to **{target_mail}** and SMS token sent to **+91-{target_phone}**.")
                            st.rerun()
                        else:
                            st.error(res)
            else:
                st.warning("⚠️ All collection slots for this date are currently fully booked or closed. Please select an alternate date above.")

    # 2. ACTIVE APPOINTMENTS & PASSES
    with ben_tabs[1]:
        st.subheader("Your Active & Past Appointments")
        if my_bks:
            for idx, b in enumerate(my_bks):
                b_dict = dict(b)
                b_dict["shop_name"] = user.get("shop_name", "Fair Price Depot")
                status_color = "#15803D" if b_dict["status"] == "CONFIRMED" else ("#2563EB" if b_dict["status"] == "COLLECTED" else "#94A3B8")
                
                # Only auto-expand the first confirmed booking to avoid clutter
                is_first_confirmed = (idx == 0 and b_dict["status"] == "CONFIRMED")
                with st.expander(f"Booking {b_dict['booking_reference']} | {b_dict['date']} ({b_dict['time_slot']}) - {b_dict['status']}", expanded=is_first_confirmed):
                    st.markdown(render_booking_voucher(b_dict), unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("##### 📲 Notification Actions & Controls")
                    c_mail_in, c_mail_btn, c_sms_btn, c_cxl = st.columns([3, 2, 2, 2])
                    
                    with c_mail_in:
                        custom_mail = st.text_input(
                            "Destination Email",
                            value=user.get("email") or "citizen@smartration.gov.in",
                            key=f"b_email_{b_dict['id']}",
                            label_visibility="collapsed"
                        )
                    with c_mail_btn:
                        if st.button("📧 Email Reminder Voucher", key=f"btn_mail_{b_dict['id']}", use_container_width=True):
                            ok_e, msg_e = send_booking_reminder_email(
                                beneficiary_email=custom_mail,
                                beneficiary_user_id=user["user_id"],
                                head_of_family=user["full_name"],
                                booking_ref=b_dict["booking_reference"],
                                date_str=b_dict["date"],
                                time_slot=b_dict["time_slot"],
                                shop_name=user.get("shop_name", "Fair Price Depot"),
                                predicted_wait=float(b_dict.get("predicted_waiting_time") or 0.0),
                                smtp_user=st.session_state.get("smtp_user"),
                                smtp_pass=st.session_state.get("smtp_pass")
                            )
                            if ok_e:
                                st.toast(f"📧 Reminder voucher emailed to {custom_mail}!")
                                st.success(msg_e)
                            else:
                                st.error(msg_e)
                    with c_sms_btn:
                        if st.button("📱 Resend SMS Token", key=f"btn_sms_{b_dict['id']}", use_container_width=True):
                            phone_target = user.get("phone", "9876543210")
                            ok_s, msg_s = app_send_sms(
                                to_phone=phone_target,
                                message=f"PDS Reminder: Slot Ref {b_dict['booking_reference']} on {b_dict['date']} ({b_dict['time_slot']}) at {user.get('shop_name')}.",
                                user_id=user["user_id"]
                            )
                            st.toast(f"📱 SMS token dispatched to +91-{phone_target}!")
                            st.info(msg_s)
                    with c_cxl:
                        if b_dict["status"] == "CONFIRMED":
                            if st.button("❌ Cancel Slot", key=f"cxl_{b_dict['id']}", type="secondary", use_container_width=True):
                                ok_cxl, msg_cxl = cancel_booking(b_dict["id"], ben_id)
                                if ok_cxl:
                                    st.toast("Appointment cancelled and slot released.")
                                    st.success(msg_cxl)
                                    st.rerun()
                                else:
                                    st.error(msg_cxl)
                        else:
                            st.write(f"Status: **{b_dict['status']}**")
        else:
            st.info("No bookings recorded for your account yet. Use the 'Smart Slot Booking & Predictions' tab to reserve your collection window!")

    # 3. ENTITLEMENT & STOCK
    with ben_tabs[2]:
        st.subheader("Your Monthly Statutory Entitlements & Usage")
        st.caption("Entitlement quotas are constitutionally allocated under the National Food Security Act (NFSA) based on your card category.")

        # Real-time monthly usage calculation
        usage = get_beneficiary_monthly_usage(ben_id)
        rice_quota = float(user.get("monthly_rice_quota_kg") or user.get("quota_rice_kg") or 35.0)
        wheat_quota = float(user.get("monthly_wheat_quota_kg") or user.get("quota_wheat_kg") or 15.0)
        sugar_quota = float(user.get("monthly_sugar_quota_kg") or user.get("quota_sugar_kg") or 3.0)

        rice_left = max(0.0, rice_quota - usage["rice_collected"])
        wheat_left = max(0.0, wheat_quota - usage["wheat_collected"])
        sugar_left = max(0.0, sugar_quota - usage["sugar_collected"])

        q1, q2, q3 = st.columns(3)
        with q1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">🍚 Subsidized Rice</div>
                <div class="stat-value">{rice_left:,.1f} <span style="font-size: 1rem; color: #64748B;">/ {rice_quota:.0f} kg</span></div>
                <div style="font-size: 0.85rem; color: #475569; margin: 4px 0;">Collected this month: <b>{usage['rice_collected']:.1f} kg</b></div>
                <div class="stat-badge-success">₹ 2.00 / kg subsidized</div>
            </div>
            """, unsafe_allow_html=True)
        with q2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">🌾 Fortified Wheat</div>
                <div class="stat-value">{wheat_left:,.1f} <span style="font-size: 1rem; color: #64748B;">/ {wheat_quota:.0f} kg</span></div>
                <div style="font-size: 0.85rem; color: #475569; margin: 4px 0;">Collected this month: <b>{usage['wheat_collected']:.1f} kg</b></div>
                <div class="stat-badge-success">₹ 3.00 / kg subsidized</div>
            </div>
            """, unsafe_allow_html=True)
        with q3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">🍬 Refined Sugar</div>
                <div class="stat-value">{sugar_left:,.1f} <span style="font-size: 1rem; color: #64748B;">/ {sugar_quota:.0f} kg</span></div>
                <div style="font-size: 0.85rem; color: #475569; margin: 4px 0;">Collected this month: <b>{usage['sugar_collected']:.1f} kg</b></div>
                <div class="stat-badge-success">₹ 13.50 / kg subsidized</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader(f"Current Stock Reserves at {user.get('shop_name', 'Your Assigned Depot')}")
        inv = get_shop_inventory(shop_id)
        if inv and len(inv) > 0:
            c_inv = st.columns(len(inv))
            for idx, item in enumerate(inv):
                with c_inv[idx]:
                    stock_qty = item["current_stock_kg"]
                    thresh = item["safety_threshold_kg"]
                    badge_cls = "stat-badge-success" if stock_qty > thresh else "stat-badge-warning"
                    badge_lbl = "Adequate Supply" if stock_qty > thresh else "Low Stock"
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-label">{item['commodity_name']}</div>
                        <div class="stat-value">{stock_qty:,.1f} <span style="font-size: 1rem; color: #64748B;">{item['unit']}</span></div>
                        <span class="{badge_cls}">{badge_lbl}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No live inventory records currently available for this shop depot.")

    # 4. DIGITAL RECEIPTS
    with ben_tabs[3]:
        st.subheader("Ration Collection History & Digital Receipts")
        txs = get_beneficiary_transactions(ben_id)
        if txs:
            for t in txs:
                t_dict = dict(t)
                t_dict["shop_name"] = user.get("shop_name", "Fair Price Depot")
                t_dict["head_of_family"] = user["full_name"]
                t_dict["ration_card_number"] = user.get("ration_card_number", "N/A")
                t_dict["card_type"] = user.get("card_type", "BPL")
                
                with st.expander(f"🧾 Receipt {t_dict['transaction_ref']} - {t_dict['transaction_date']} (Paid: Rs. {t_dict['total_amount']:.2f})", expanded=False):
                    st.markdown(render_digital_receipt(t_dict), unsafe_allow_html=True)
                    
                    st.markdown("---")
                    c_rcpt_mail, c_rcpt_mail_btn, c_rcpt_sms_btn = st.columns([3, 2, 2])
                    with c_rcpt_mail:
                        rcpt_email_target = st.text_input(
                            "Send Receipt to Email Address:",
                            value=user.get("email") or "citizen@smartration.gov.in",
                            key=f"inp_rcpt_{t_dict['id']}",
                            label_visibility="collapsed"
                        )
                    with c_rcpt_mail_btn:
                        if st.button("📧 Email e-Receipt", key=f"btn_send_rcpt_{t_dict['id']}", type="primary", use_container_width=True):
                            ok_r, msg_r = send_purchase_receipt_email(
                                beneficiary_email=rcpt_email_target,
                                beneficiary_user_id=user["user_id"],
                                head_of_family=user["full_name"],
                                ration_card_no=user.get("ration_card_number", "N/A"),
                                card_type=user.get("card_type", "BPL"),
                                tx_ref=t_dict["transaction_ref"],
                                date_str=t_dict["transaction_date"],
                                shop_name=user.get("shop_name", "Fair Price Depot"),
                                rice_kg=t_dict["rice_collected_kg"],
                                wheat_kg=t_dict["wheat_collected_kg"],
                                sugar_kg=t_dict["sugar_collected_kg"],
                                total_amount=t_dict["total_amount"],
                                payment_mode=t_dict.get("payment_mode", "SUBSIDIZED_FREE"),
                                smtp_user=st.session_state.get("smtp_user"),
                                smtp_pass=st.session_state.get("smtp_pass")
                            )
                            if ok_r:
                                st.toast(f"📧 Receipt dispatched to {rcpt_email_target}!")
                                st.success(f"Official Electronic Receipt sent to **{rcpt_email_target}**! {msg_r}")
                            else:
                                st.error(msg_r)
                    with c_rcpt_sms_btn:
                        if st.button("📱 SMS Receipt Token", key=f"btn_sms_rcpt_{t_dict['id']}", use_container_width=True):
                            phone_target = user.get("phone", "9876543210")
                            ok_s, msg_s = app_send_sms(
                                to_phone=phone_target,
                                message=f"PDS Receipt: {t_dict['transaction_ref']} on {t_dict['transaction_date']}. Grains: Rice {t_dict['rice_collected_kg']}kg, Wheat {t_dict['wheat_collected_kg']}kg, Sugar {t_dict['sugar_collected_kg']}kg. Total: Rs {t_dict['total_amount']:.2f}.",
                                user_id=user["user_id"]
                            )
                            st.toast(f"📱 Receipt summary SMS sent to +91-{phone_target}!")
                            st.info(msg_s)
        else:
            st.info("No transaction collection records found yet. Official electronic collection receipts are generated whenever you collect your grains at the Fair Price Depot.")
            c_demo_rcpt, _ = st.columns([1, 2])
            with c_demo_rcpt:
                if st.button("🧪 Generate Sample Demonstration Receipt", key="btn_gen_demo_receipt", use_container_width=True):
                    record_transaction(
                        beneficiary_id=ben_id,
                        shop_id=shop_id,
                        date_str=str(date.today()),
                        rice_kg=15.0,
                        wheat_kg=5.0,
                        sugar_kg=1.0,
                        payment_mode="SUBSIDIZED_FREE",
                        remarks="Sample Demonstration Receipt"
                    )
                    st.toast("Sample demonstration receipt generated!")
                    st.rerun()

    # 5. SMS & NOTIFICATIONS (INTERACTIVE COMMUNICATION HUB)
    with ben_tabs[4]:
        st.subheader("Interactive Communication Hub & Gateway Configuration")
        st.caption("Verify and test real-time alerts. Deliver actual live emails to inboxes (Gmail/Outlook) and real cellular SMS to mobile numbers (Fast2SMS / Twilio).")

        # Live Gateway Status Cards
        c_stat_e, c_stat_s = st.columns(2)
        has_smtp = bool(st.session_state.get("smtp_user") and st.session_state.get("smtp_pass"))
        has_sms = bool(st.session_state.get("fast2sms_key") or (st.session_state.get("twilio_sid") and st.session_state.get("twilio_token")))

        with c_stat_e:
            if has_smtp:
                st.markdown(f"""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 12px 16px;">
                    <b style="color: #166534;">🟢 Live Email Gateway Active</b><br>
                    <small style="color: #15803D;">Connected via {st.session_state.get('smtp_user')} (TLS Port {st.session_state.get('smtp_port', 587)})</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 12px 16px;">
                    <b style="color: #92400E;">📦 Email: Local Sandbox Capture Mode</b><br>
                    <small style="color: #B45309;">Emails logged to SQLite. To send to your real inbox, enter your App Password below.</small>
                </div>
                """, unsafe_allow_html=True)

        with c_stat_s:
            if has_sms:
                st.markdown("""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 12px 16px;">
                    <b style="color: #166534;">🟢 Live Cellular SMS Gateway Active</b><br>
                    <small style="color: #15803D;">Connected to Telecom Cellular Network (Fast2SMS / Twilio)</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 10px; padding: 12px 16px;">
                    <b style="color: #92400E;">📦 SMS: Local Sandbox Capture Mode</b><br>
                    <small style="color: #B45309;">SMS logged to SQLite. To deliver real SMS to your phone, enter a Fast2SMS key below.</small>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Gateway Setup Drawer
        with st.expander("⚙️ Connect Live Gateways (Real Gmail & Real Mobile SMS)", expanded=(not has_smtp and not has_sms)):
            tab_cfg_email, tab_cfg_sms = st.tabs(["📧 Real Email Setup (Gmail / Outlook)", "📱 Real Mobile SMS Setup (Fast2SMS / Twilio)"])

            with tab_cfg_email:
                st.markdown("""
                **Send Real Emails to Any Inbox in 4 Steps:**
                1. Go to your **Google Account** → **Security** → Enable **2-Step Verification**.
                2. Search for **App Passwords** (or open [Google App Passwords](https://myaccount.google.com/apppasswords)).
                3. Create an app password named **Smart Ration** (Google generates a 16-character code like `abcd efgh ijkl mnop`).
                4. Paste your Gmail and that 16-character password below and click **Save Email Setup**.
                """)
                ce1, ce2 = st.columns(2)
                with ce1:
                    cfg_smtp_host = st.text_input("SMTP Server", value=st.session_state.get("smtp_server", "smtp.gmail.com"), key="hub_smtp_host")
                    cfg_smtp_port = st.number_input("SMTP Port", value=int(st.session_state.get("smtp_port", 587)), key="hub_smtp_port")
                with ce2:
                    cfg_smtp_user = st.text_input("Your Gmail / Outlook Address", value=st.session_state.get("smtp_user", ""), placeholder="e.g. yourname@gmail.com", key="hub_smtp_user")
                    cfg_smtp_pass = st.text_input("16-Character App Password", value=st.session_state.get("smtp_pass", ""), type="password", placeholder="Paste 16-character code", key="hub_smtp_pass")

                if st.button("💾 Save Email Setup & Verify", key="btn_save_email_hub", type="primary"):
                    st.session_state["smtp_server"] = cfg_smtp_host
                    st.session_state["smtp_port"] = cfg_smtp_port
                    st.session_state["smtp_user"] = cfg_smtp_user.strip()
                    st.session_state["smtp_pass"] = cfg_smtp_pass.strip().replace(" ", "")
                    if cfg_smtp_user.strip() and cfg_smtp_pass.strip():
                        ok_test, msg_test = send_email(
                            to_email=cfg_smtp_user.strip(),
                            subject="🌾 Smart Ration: Live Email Connection Verified!",
                            html_content="<h3>Connection Verified!</h3><p>Your Smart Ration System is now connected to live mail servers and delivering real emails to inboxes.</p>",
                            smtp_user=cfg_smtp_user.strip(),
                            smtp_pass=cfg_smtp_pass.strip().replace(" ", "")
                        )
                        if ok_test:
                            st.success(f"🎉 Verified! A live test email has landed in your inbox at **{cfg_smtp_user.strip()}**.")
                        else:
                            st.error(f"Authentication failed: {msg_test}. Please verify your 16-character App Password.")
                    else:
                        st.info("Operating in Local Simulation Sandbox.")
                    st.rerun()

            with tab_cfg_sms:
                st.markdown("""
                **Send Real Mobile Alerts to Indian Numbers (e.g. +91-7010411496):**
                
                > 💡 **Notice on Fast2SMS:** Due to TRAI DLT regulations in India, Fast2SMS now asks for a ₹100 recharge. **Do NOT pay ₹100!** Instead, use the **100% Free WhatsApp Alert** option below or **Gmail Push Alerts**—they deliver live messages to your phone completely free of charge.
                """)

                st.markdown("##### 🟢 Option 1 (100% Free): Direct WhatsApp Message to Mobile")
                st.markdown("""
                Receive live alerts on WhatsApp for free using CallMeBot:
                1. In WhatsApp, send a message to **`+34 623 78 64 49`** with text: `I allow callmebot to send me messages`
                2. CallMeBot will reply instantly with your free **API Key**.
                3. Paste that key below and click **Save Mobile Gateway & Verify**.
                """)
                cfg_cmb = st.text_input("CallMeBot Free WhatsApp API Key", value=st.session_state.get("callmebot_key", ""), type="password", placeholder="e.g. 123456", key="hub_cmb_key")

                st.markdown("##### 📱 Option 2: Telecom Cellular SMS (Fast2SMS / Twilio)")
                cfg_f2s = st.text_input("Fast2SMS Authorization API Key", value=st.session_state.get("fast2sms_key", ""), type="password", placeholder="Paste Fast2SMS API Key (Optional)", key="hub_f2s_key")
                
                with st.expander("Twilio Alternative (International SMS)", expanded=False):
                    cfg_tw_sid = st.text_input("Twilio Account SID", value=st.session_state.get("twilio_sid", ""), key="hub_tw_sid")
                    cfg_tw_token = st.text_input("Twilio Auth Token", value=st.session_state.get("twilio_token", ""), type="password", key="hub_tw_token")
                    cfg_tw_from = st.text_input("Twilio Sender Phone", value=st.session_state.get("twilio_from", ""), placeholder="+1XXXXXXXXXX", key="hub_tw_from")

                if st.button("💾 Save Mobile Gateway & Verify", key="btn_save_sms_hub", type="primary"):
                    st.session_state["callmebot_key"] = cfg_cmb.strip()
                    st.session_state["fast2sms_key"] = cfg_f2s.strip()
                    st.session_state["twilio_sid"] = cfg_tw_sid.strip()
                    st.session_state["twilio_token"] = cfg_tw_token.strip()
                    st.session_state["twilio_from"] = cfg_tw_from.strip()

                    test_phone = user.get("phone", "7010411496")
                    if cfg_cmb.strip() or cfg_f2s.strip() or (cfg_tw_sid.strip() and cfg_tw_token.strip()):
                        ok_s_test, msg_s_test = app_send_sms(
                            to_phone=test_phone,
                            message=f"Smart Ration: Live mobile alert verified! Your gateway is active."
                        )
                        if ok_s_test and ("Live" in msg_s_test or "delivered" in msg_s_test):
                            st.success(f"🎉 Verified! A live notification has been transmitted to your phone at **+91-{test_phone}**.")
                        else:
                            st.info(f"Gateway status: {msg_s_test}")
                    else:
                        st.info("Operating in Local Simulation Sandbox.")
                    st.rerun()

        # Live Interactive Dispatch Sandbox
        with st.expander("⚡ Live Interactive Email & SMS Dispatch Sandbox", expanded=True):
            st.markdown("""
            Test the notification engine in real time. Choose a template, enter your destination email and phone, and click dispatch.
            """)
            
            c_test1, c_test2 = st.columns(2)
            with c_test1:
                test_mail = st.text_input("Destination Email Address", value=user.get("email") or "citizen@smartration.gov.in", key="dispatch_test_email")
                test_template = st.selectbox(
                    "Select Notification Alert Template",
                    [
                        "Booking Reminder Voucher",
                        "2-Hour Advance Slot Alert",
                        "Depot Stock Fresh Inflow Notice",
                        "Official Purchase Receipt (e-Invoice)"
                    ],
                    key="dispatch_template_sel"
                )
            with c_test2:
                test_mobile = st.text_input("Destination Mobile Number (+91)", value=user.get("phone", "7010411496"), key="dispatch_test_mobile")
                delivery_channel = st.radio("Delivery Mode", ["Both Email & SMS", "Email Only", "SMS Only"], horizontal=True, key="dispatch_channel_radio")
                
            if st.button("🚀 Dispatch Notification Test Now", type="primary", key="btn_dispatch_test"):
                results = []
                if "Email" in delivery_channel:
                    if "Booking" in test_template or "Advance" in test_template:
                        ok_m, res_m = send_booking_reminder_email(
                            beneficiary_email=test_mail,
                            beneficiary_user_id=user["user_id"],
                            head_of_family=user["full_name"],
                            booking_ref="BK-TEST-789",
                            date_str=str(date.today()),
                            time_slot="10-11 AM",
                            shop_name=user.get("shop_name", "Fair Price Depot"),
                            predicted_wait=12.5,
                            smtp_user=st.session_state.get("smtp_user"),
                            smtp_pass=st.session_state.get("smtp_pass")
                        )
                    elif "Receipt" in test_template:
                        ok_m, res_m = send_purchase_receipt_email(
                            beneficiary_email=test_mail,
                            beneficiary_user_id=user["user_id"],
                            head_of_family=user["full_name"],
                            ration_card_no=user.get("ration_card_number", "RC-TEST"),
                            card_type=user.get("card_type", "BPL"),
                            tx_ref="TX-TEST-555",
                            date_str=str(date.today()),
                            shop_name=user.get("shop_name", "Fair Price Depot"),
                            rice_kg=15.0,
                            wheat_kg=10.0,
                            sugar_kg=2.0,
                            total_amount=57.0,
                            payment_mode="SUBSIDIZED_CASH",
                            smtp_user=st.session_state.get("smtp_user"),
                            smtp_pass=st.session_state.get("smtp_pass")
                        )
                    else:
                        ok_m, res_m = send_email(
                            to_email=test_mail,
                            subject="🌾 PDS Stock Inflow Alert: Fresh Grain Shipment Arrived",
                            html_content=f"<h3>Smart Ration System</h3><p>Dear {user['full_name']}, fresh buffer stock has arrived at {user.get('shop_name')}. Book your slot now!</p>",
                            smtp_user=st.session_state.get("smtp_user"),
                            smtp_pass=st.session_state.get("smtp_pass")
                        )
                    results.append(("Email", ok_m, res_m))

                if "SMS" in delivery_channel:
                    ok_s, res_s = app_send_sms(
                        to_phone=test_mobile,
                        message=f"PDS Alert [{test_template}]: Dear {user['full_name']}, your ration notification has been dispatched successfully.",
                        user_id=user["user_id"]
                    )
                    results.append(("SMS", ok_s, res_s))

                for ch, ok, msg in results:
                    if ok:
                        if "Live" in msg or "delivered to" in msg:
                            st.success(f"🎉 **{ch} Delivered to Real Device:** {msg}")
                        else:
                            st.info(f"📦 **{ch} (Local Simulation Sandbox):** {msg}")
                            st.caption("ℹ️ To deliver live notifications to your actual phone or email inbox, configure your App Password or Fast2SMS key in the setup drawer above.")
                    else:
                        st.error(f"❌ **{ch} Delivery Failed:** {msg}")
                st.toast("⚡ Notification test completed!")
                st.rerun()

        st.markdown("---")
        st.markdown("##### 📬 Official Notification History & Dispatch Logs")
        notifs = [dict(n) for n in get_user_notifications(user["user_id"])]
        if notifs:
            for n in notifs:
                st.markdown(f"""
                <div class="notification-item">
                    <div style="display: flex; justify-content: space-between;">
                        <b style="color: #1E3A8A;">📲 [{n.get('channel', 'SMS')}] {n['title']}</b>
                        <span style="font-size: 0.8rem; color: #94A3B8;">{n['created_at']}</span>
                    </div>
                    <div style="color: #334155; margin-top: 4px; font-size: 0.92rem;">{n['message']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No notifications in your inbox.")

    # 6. GRIEVANCE REDRESSAL
    with ben_tabs[5]:
        st.subheader("Grievance Redressal & Food Inspector Direct Escalation")
        st.caption("Citizens can directly escalate service quality, stock irregularities, or biometric authentication delays to the Civil Supplies Officer.")

        col_g_form, col_g_list = st.columns([1, 1])

        with col_g_form:
            st.markdown("#### ✍️ Lodge a New Grievance")
            with st.form("beneficiary_grievance_form", clear_on_submit=True):
                subj = st.text_input("Grievance Subject *", placeholder="e.g. Stock shortage or counter delay")
                desc = st.text_area("Detailed Report *", placeholder="Describe date, time, and occurrence in detail...")
                submit_gr = st.form_submit_button("Submit Official Grievance", type="primary", use_container_width=True)

                if submit_gr:
                    if subj.strip() and desc.strip():
                        with get_connection() as conn:
                            conn.execute(
                                "INSERT INTO complaints (beneficiary_id, shop_id, subject, description) VALUES (?, ?, ?, ?)",
                                (ben_id, shop_id, subj.strip(), desc.strip())
                            )
                            conn.commit()
                        create_notification(
                            user_id=user["user_id"],
                            title="Grievance Lodged",
                            message=f"Your grievance '{subj.strip()}' has been submitted and assigned to the Taluk Civil Supplies Officer.",
                            channel="SMS"
                        )
                        st.toast("✅ Grievance submitted successfully!")
                        st.success("Grievance lodged successfully. It has been routed to the Taluk Civil Supplies Officer.")
                        st.rerun()
                    else:
                        st.warning("Please provide both subject and description.")

        with col_g_list:
            st.markdown("#### 📋 Track Your Submitted Grievances")
            my_complaints = [dict(c) for c in get_beneficiary_complaints(ben_id)]
            if my_complaints:
                for c in my_complaints:
                    status_badge = "stat-badge-success" if c["status"] == "RESOLVED" else "stat-badge-warning"
                    status_lbl = "🟢 RESOLVED" if c["status"] == "RESOLVED" else "🟡 UNDER INVESTIGATION (OPEN)"
                    st.markdown(f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 700; color: #0F172A;">{c['subject']}</span>
                            <span class="{status_badge}">{status_lbl}</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #64748B; margin-top: 4px;">Depot: {c['shop_name']} | Filed: {c['created_at']}</div>
                        <div style="font-size: 0.9rem; color: #334155; margin-top: 8px;">{c['description']}</div>
                        {f'<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 8px; padding: 8px 12px; margin-top: 8px; font-size: 0.85rem; color: #166534;"><b>Inspector Notes:</b> {c.get("resolution_notes")}</div>' if c.get("resolution_notes") else ''}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("You have no filed grievances on record.")

# ==============================================================================
# VIEW: SHOP DEALER PORTAL (LOGGED IN)
# ==============================================================================
def render_authenticated_dealer():
    user = dict(st.session_state.user) if st.session_state.user else {}
    shop_id = user.get("shop_id", 1)

    # Dealer Top Banner
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-radius: 18px; padding: 24px 28px; color: #FFFFFF; box-shadow: 0 4px 16px rgba(0,0,0,0.1); margin-bottom: 22px; border: 1px solid rgba(255,255,255,0.08);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">FAIR PRICE SHOP OPERATIONAL TERMINAL</div>
                <h2 style="margin: 4px 0; color: #FFFFFF; font-weight: 800; font-size: 1.55rem;">{user.get('shop_name', 'Fair Price Depot')} ({user.get('shop_number', 'FPS-104')})</h2>
                <div style="color: #CBD5E1; font-size: 0.88rem;">
                    Licensed Dealer: <b>{user.get('full_name')}</b> • License: <b>{user.get('license_number', 'FPS-LIC-2026')}</b>
                </div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <span class="pill-badge pill-emerald">● POS ONLINE</span>
                <span class="pill-badge pill-blue">{user.get('counters_count', 2)} Active Counters</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    dlr_tabs = st.tabs([
        "🏪 Operations & Live Roster",
        "📈 Daily Demand Forecast & Shortages",
        "💳 Disburse Ration (POS Checkout)",
        "📦 Depot Inventory & Delivery Inflow",
        "📥 Data Export Suite"
    ])

    # 1. OPERATIONS & ROSTER
    with dlr_tabs[0]:
        st.subheader("Depot Daily Snapshot")
        inv = get_shop_inventory(shop_id)
        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.metric("Staff on Duty", f"{user.get('staff_count', 3)}")
        with d2:
            st.metric("Active Distribution Counters", f"{user.get('counters_count', 2)}")
        with d3:
            r_stk = next((i["current_stock_kg"] for i in inv if i["commodity_code"] == "RICE"), 0.0)
            st.metric("Available Rice Stock", f"{r_stk:,.1f} kg")
        with d4:
            w_stk = next((i["current_stock_kg"] for i in inv if i["commodity_code"] == "WHEAT"), 0.0)
            st.metric("Available Wheat Stock", f"{w_stk:,.1f} kg")

        st.markdown("---")
        st.subheader("Today's Slot Booking Roster")
        today_str = str(date.today())
        b_today = get_shop_bookings_for_date(shop_id, today_str)
        if b_today:
            df_b = pd.DataFrame([dict(b) for b in b_today])
            st.dataframe(df_b[["booking_reference", "ration_card_number", "head_of_family", "card_type", "time_slot", "status"]], use_container_width=True)
            
            col_b_info, col_b_btn = st.columns([2, 1])
            with col_b_info:
                st.caption(f"Total scheduled appointments for today: **{len(b_today)} cardholders**.")
            with col_b_btn:
                if st.button("📢 Dispatch Reminders to Today's Roster", type="secondary", use_container_width=True):
                    rem_count = 0
                    for b in b_today:
                        b_dict = dict(b)
                        if b_dict.get("status") == "CONFIRMED":
                            b_mail = b_dict.get("email") or f"citizen_{b_dict.get('ration_card_number')}@smartration.gov.in"
                            send_booking_reminder_email(
                                beneficiary_email=b_mail,
                                beneficiary_user_id=b_dict.get("user_id", 1),
                                head_of_family=b_dict.get("head_of_family", "Cardholder"),
                                booking_ref=b_dict.get("booking_reference", "BK-REM"),
                                date_str=today_str,
                                time_slot=b_dict.get("time_slot", "9-10 AM"),
                                shop_name=user.get("shop_name", "Fair Price Depot"),
                                predicted_wait=float(b_dict.get("predicted_waiting_time", 15.0)),
                                smtp_user=st.session_state.get("smtp_user"),
                                smtp_pass=st.session_state.get("smtp_pass")
                            )
                            send_instant_sms(
                                to_phone=b_dict.get("phone", "9876543210"),
                                message=f"PDS Reminder: You have an appointment today {today_str} ({b_dict.get('time_slot')}) at {user.get('shop_name')}. Ref: {b_dict.get('booking_reference')}.",
                                user_id=b_dict.get("user_id", 1)
                            )
                            rem_count += 1
                    st.success(f"✓ Dispatched email and SMS reminders to {rem_count} confirmed beneficiaries!")
                    st.toast("Batch reminders dispatched!")
        else:
            st.info("No slot bookings scheduled for today.")

    # 2. DEMAND FORECAST & SHORTAGE ANALYZER
    with dlr_tabs[1]:
        st.subheader("Machine Learning Daily Demand & Shortage Analysis")
        st.caption("Forecasts cumulative commodity consumption and flags impending stockouts before slots begin.")

        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            fc_date = st.date_input("Target Operational Date", value=date.today() + timedelta(days=1), key="dlr_eval_date")
            fc_day = fc_date.strftime("%A")
            fc_wknd = 1 if fc_day in ["Saturday", "Sunday"] else 0
            fc_hol = st.checkbox("Public Holiday Schedule", value=False)

        with f_col2:
            with st.spinner("Computing multi-model Gradient Boosting demand projections..."):
                shortage_res = analyze_shop_stock_shortages(
                    shop_id=shop_id,
                    target_date_str=str(fc_date),
                    day_name=fc_day,
                    is_weekend=fc_wknd,
                    is_holiday=1 if fc_hol else 0
                )
            st.markdown(f"""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 14px 18px;">
                <b style="color: #1E40AF;">Projected Daily Customer Footfall:</b> {shortage_res['total_predicted_customers']:.0f} Beneficiaries across 7 operating hours.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### Supply vs Demand Comparison Table")
        comm_df = pd.DataFrame([
            {
                "Commodity": c["name"],
                "Available Depot Stock (kg)": c["current_stock_kg"],
                "Forecasted Demand (kg)": c["predicted_demand_kg"],
                "Projected Balance (kg)": c["projected_closing_stock_kg"],
                "Expected Shortage (kg)": c["shortage_kg"],
                "Recommended Replenishment (kg)": c["recommended_replenishment_kg"],
                "Supply Status": c["status"]
            }
            for c in shortage_res["commodities"]
        ])
        st.dataframe(comm_df, use_container_width=True)

        # Plotly Stock vs Demand Chart
        fig = go.Figure(data=[
            go.Bar(name='Available Stock (kg)', x=[c['name'] for c in shortage_res['commodities']], y=[c['current_stock_kg'] for c in shortage_res['commodities']], marker_color='#2563EB'),
            go.Bar(name='Forecasted Demand (kg)', x=[c['name'] for c in shortage_res['commodities']], y=[c['predicted_demand_kg'] for c in shortage_res['commodities']], marker_color='#EF4444')
        ])
        fig.update_layout(barmode='group', title=f"Stock vs Predicted Demand for {fc_date}", height=360)
        st.plotly_chart(fig, use_container_width=True)

    # 3. DISBURSE RATION (POS CHECKOUT)
    with dlr_tabs[2]:
        st.subheader("Electronic Point-of-Sale (e-POS) Disbursement")
        st.caption("Verify cardholder identity, disburse grains, update depot inventory in real-time, and issue a digital receipt.")

        v_mode = st.radio("Verification Mode", ["Verify by Ration Card Number", "Verify by Booking Reference"], horizontal=True)
        search_card = ""
        search_ref = ""
        found_ben = None
        linked_booking_id = None

        if "Ration Card" in v_mode:
            search_card = st.text_input("Scan / Enter Ration Card Number", placeholder="e.g. RC-KA-99201")
            if search_card.strip():
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM beneficiaries WHERE ration_card_number = ?", (search_card.strip(),))
                    found_ben = cursor.fetchone()
        else:
            search_ref = st.text_input("Scan / Enter Booking Reference", placeholder="e.g. BK-20261116-A1B2C3")
            if search_ref.strip():
                with get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        """SELECT b.id as booking_id, b.status as booking_status, bn.*
                           FROM bookings b
                           JOIN beneficiaries bn ON b.beneficiary_id = bn.id
                           WHERE b.booking_reference = ?""",
                        (search_ref.strip(),)
                    )
                    res = cursor.fetchone()
                    if res:
                        found_ben = res
                        linked_booking_id = res["booking_id"]

        if found_ben:
            found_ben = dict(found_ben)
            st.success(f"Verified: **{found_ben['head_of_family']}** | Card: **{found_ben['ration_card_number']}** ({found_ben['card_type']})")

            with st.form("pos_disburse_form"):
                st.write(f"**Authorized Monthly Quotas:** Rice: {found_ben['monthly_rice_quota_kg']} kg | Wheat: {found_ben['monthly_wheat_quota_kg']} kg | Sugar: {found_ben['monthly_sugar_quota_kg']} kg")
                r_c1, r_c2, r_c3 = st.columns(3)
                r_qty = r_c1.number_input("Rice Disbursed (kg)", min_value=0.0, max_value=60.0, value=float(found_ben['monthly_rice_quota_kg']), step=1.0)
                w_qty = r_c2.number_input("Wheat Disbursed (kg)", min_value=0.0, max_value=40.0, value=float(found_ben['monthly_wheat_quota_kg']), step=1.0)
                s_qty = r_c3.number_input("Sugar Disbursed (kg)", min_value=0.0, max_value=15.0, value=float(found_ben['monthly_sugar_quota_kg']), step=0.5)

                pay_type = st.selectbox("Subsidy Payment Mode", ["SUBSIDIZED_FREE", "CASH", "UPI"])
                notes = st.text_input("Biometric Authentication Notes", value="e-KYC verified via thumbprint scanner")
                notify_citizen = st.checkbox("📲 Automatically dispatch Electronic Receipt via Email & SMS to beneficiary", value=True)

                submit_tx = st.form_submit_button("Authorize Disbursement & Generate Receipt", type="primary", use_container_width=True)
                if submit_tx:
                    ok, tx_id = record_transaction(
                        beneficiary_id=found_ben["id"],
                        shop_id=shop_id,
                        date_str=str(date.today()),
                        rice_kg=r_qty,
                        wheat_kg=w_qty,
                        sugar_kg=s_qty,
                        booking_id=linked_booking_id,
                        payment_mode=pay_type,
                        dealer_user_id=user["user_id"],
                        remarks=notes
                    )
                    if ok:
                        st.success(f"🎉 Disbursement Completed! Reference: **{tx_id}**")
                        # Fetch full receipt data
                        tx_rec = get_transaction_by_ref(tx_id)
                        if tx_rec:
                            st.markdown(render_digital_receipt(dict(tx_rec)), unsafe_allow_html=True)

                        # Automatic Email & SMS Notification Dispatch
                        if notify_citizen:
                            ben_email = found_ben["email"] if ("email" in found_ben.keys() and found_ben["email"]) else f"citizen_{found_ben['ration_card_number']}@smartration.gov.in"
                            ben_phone = found_ben["phone"] if ("phone" in found_ben.keys() and found_ben["phone"]) else "9876543210"
                            total_paid = float(tx_rec["total_amount"]) if tx_rec else 0.0

                            ok_mail, msg_mail = send_purchase_receipt_email(
                                beneficiary_email=ben_email,
                                beneficiary_user_id=found_ben.get("user_id", 1),
                                head_of_family=found_ben["head_of_family"],
                                ration_card_no=found_ben["ration_card_number"],
                                card_type=found_ben["card_type"],
                                tx_ref=tx_id,
                                date_str=str(date.today()),
                                shop_name=user.get("shop_name", "Fair Price Depot"),
                                rice_kg=r_qty,
                                wheat_kg=w_qty,
                                sugar_kg=s_qty,
                                total_amount=total_paid,
                                payment_mode=pay_type,
                                smtp_user=st.session_state.get("smtp_user"),
                                smtp_pass=st.session_state.get("smtp_pass")
                            )
                            send_instant_sms(
                                to_phone=ben_phone,
                                message=f"PDS Official Receipt: Tx {tx_id}. Issued: Rice {r_qty}kg, Wheat {w_qty}kg, Sugar {s_qty}kg. Paid: Rs {total_paid:.2f}. Thank you!",
                                user_id=found_ben.get("user_id", 1)
                            )
                            st.toast(f"📧 Receipt emailed to {ben_email} & SMS sent to {ben_phone}!")
                            st.info(f"Notification status: {msg_mail}")
                    else:
                        st.error("Transaction failed.")
        elif search_card.strip() or search_ref.strip():
            st.warning("Beneficiary card or booking reference could not be found.")

    # 4. INVENTORY & INFLOW
    with dlr_tabs[3]:
        st.subheader("Depot Stock Ledger & Delivery Receipts")
        inv_curr = get_shop_inventory(shop_id)
        if inv_curr:
            df_curr = pd.DataFrame([dict(i) for i in inv_curr])
            st.dataframe(df_curr[["commodity_name", "commodity_code", "current_stock_kg", "safety_threshold_kg", "last_updated"]], use_container_width=True)

        st.markdown("#### Record Depot Delivery / Central Inflow")
        with st.form("inflow_form"):
            inflow_comm = st.selectbox("Commodity Received", ["RICE", "WHEAT", "SUGAR"])
            inflow_val = st.number_input("Delivered Quantity (kg)", min_value=10.0, max_value=10000.0, value=500.0, step=25.0)
            challan_no = st.text_input("Delivery Challan / Warehousing Ref", value="CWC-BLR-2026-9912")

            if st.form_submit_button("Record Inflow & Replenish Stock", type="primary"):
                if update_stock(shop_id, inflow_comm, inflow_val, "INFLOW", challan_no):
                    st.success(f"Successfully added {inflow_val} kg of {inflow_comm} to depot inventory.")
                    st.rerun()

    # 5. DATA EXPORT SUITE
    with dlr_tabs[4]:
        st.subheader("Data Export Suite (CSV Downloads)")
        st.caption("Download depot transactional records and inventory logs for statutory reporting.")

        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            st.markdown("##### Download Recent Distribution Transactions")
            dlr_txs = get_shop_transactions(shop_id, limit=500)
            if dlr_txs:
                df_dlr_tx = pd.DataFrame([dict(t) for t in dlr_txs])
                csv_tx = df_dlr_tx.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Transactions CSV",
                    data=csv_tx,
                    file_name=f"shop_{shop_id}_transactions_{date.today()}.csv",
                    mime="text/csv"
                )
        with c_exp2:
            st.markdown("##### Download Inventory Status")
            if inv_curr:
                csv_inv = pd.DataFrame([dict(i) for i in inv_curr]).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Inventory CSV",
                    data=csv_inv,
                    file_name=f"shop_{shop_id}_inventory_{date.today()}.csv",
                    mime="text/csv"
                )

# ==============================================================================
# VIEW: ADMINISTRATOR CONSOLE (LOGGED IN)
# ==============================================================================
def render_authenticated_admin():
    user = dict(st.session_state.user) if st.session_state.user else {}
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0A1128 0%, #1C2541 100%); border-radius: 18px; padding: 24px 28px; color: #FFFFFF; box-shadow: 0 4px 16px rgba(0,0,0,0.12); margin-bottom: 22px; border: 1px solid rgba(255,255,255,0.08);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #93C5FD; text-transform: uppercase; letter-spacing: 0.08em;">STATEWIDE PDS COMMAND & GOVERNANCE DESK</div>
                <h2 style="margin: 4px 0; color: #FFFFFF; font-weight: 800; font-size: 1.55rem;">🏛️ Directorate of Food, Civil Supplies & Consumer Affairs</h2>
                <div style="color: #CBD5E1; font-size: 0.88rem;">
                    Officer In-Charge: <b>{user.get('full_name', 'State Director')}</b> • Region: <b>Karnataka Central Zone</b>
                </div>
            </div>
            <div>
                <span class="pill-badge pill-emerald">● 42 DEPOTS MONITORED</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM ration_shops")
        n_shops = c.fetchone()["count"]
        c.execute("SELECT COUNT(*) as count FROM beneficiaries")
        n_bens = c.fetchone()["count"]
        c.execute("SELECT COUNT(*) as count FROM transactions")
        n_tx = c.fetchone()["count"]
        c.execute("SELECT SUM(rice_collected_kg + wheat_collected_kg + sugar_collected_kg) as total_kg FROM transactions")
        row_kg = c.fetchone()["total_kg"]
        tot_disbursed = row_kg if row_kg else 0.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Fair Price Shops", f"{n_shops}")
    k2.metric("Registered Beneficiaries", f"{n_bens:,}")
    k3.metric("Total Completed Collections", f"{n_tx:,}")
    k4.metric("Total Grains Disbursed", f"{tot_disbursed:,.1f} kg")

    adm_tabs = st.tabs([
        "🌐 Statewide Depot Surveillance",
        "🏪 Fair Price Shops Directory",
        "📇 Beneficiary Registry",
        "⚖️ Slot Capacity Governance",
        "📝 Grievance Redressal",
        "📢 Broadcast & Communication Center",
        "📡 ML Telemetry & Audit",
        "📊 ML Analytics Studio"
    ])

    # 1. STATEWIDE SURVEILLANCE
    with adm_tabs[0]:
        st.subheader("Statewide Multi-Depot Supply Health Monitor")
        eval_dt = st.date_input("Audit Date", value=date.today() + timedelta(days=1), key="adm_audit_dt")
        shops = get_all_shops()

        all_records = []
        for s in shops:
            res = analyze_shop_stock_shortages(
                shop_id=s["id"],
                target_date_str=str(eval_dt),
                day_name=eval_dt.strftime("%A"),
                is_weekend=1 if eval_dt.weekday() >= 5 else 0,
                is_holiday=0
            )
            for cm in res["commodities"]:
                all_records.append({
                    "Shop Name": s["shop_name"],
                    "Shop No": s["shop_number"],
                    "Commodity": cm["name"],
                    "Current Stock": f"{cm['current_stock_kg']} kg",
                    "Predicted Demand": f"{cm['predicted_demand_kg']} kg",
                    "Shortage": f"{cm['shortage_kg']} kg",
                    "Replenishment": f"{cm['recommended_replenishment_kg']} kg",
                    "Alert Status": cm["status"]
                })

        df_state = pd.DataFrame(all_records)
        st.dataframe(df_state, use_container_width=True)

        csv_state = df_state.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Statewide Supply Audit (CSV)",
            data=csv_state,
            file_name=f"statewide_supply_audit_{eval_dt}.csv",
            mime="text/csv"
        )

    # 2. SHOPS DIRECTORY
    with adm_tabs[1]:
        st.subheader("Registered Fair Price Shops")
        st.dataframe(pd.DataFrame([dict(s) for s in shops]), use_container_width=True)

    # 3. BENEFICIARY REGISTRY
    with adm_tabs[2]:
        st.subheader("Statewide Beneficiary Registry")
        all_bens = list_all_beneficiaries()
        st.dataframe(pd.DataFrame([dict(b) for b in all_bens]), use_container_width=True)

    # 4. CAPACITY GOVERNANCE
    with adm_tabs[3]:
        st.subheader("Hourly Time-Slot Capacity Governance")
        shop_map = {s["shop_name"]: s["id"] for s in shops}
        gov_sname = st.selectbox("Choose Depot", list(shop_map.keys()), key="gov_s_key")
        gov_sid = shop_map[gov_sname]
        gov_dt = st.date_input("Target Date", value=date.today() + timedelta(days=1), key="gov_dt_key")

        caps = get_day_slot_capacities(gov_sid, str(gov_dt))
        if caps:
            st.dataframe(pd.DataFrame([dict(c) for c in caps]), use_container_width=True)

        with st.form("gov_cap_form"):
            target_slot = st.selectbox("Slot to Configure", OPERATIONAL_SLOTS)
            new_cap_val = st.number_input("Max Allowable Bookings", min_value=5, max_value=120, value=35)
            slot_open = st.checkbox("Slot Enabled for Booking", value=True)

            if st.form_submit_button("Save Slot Policy", type="primary"):
                with get_connection() as conn:
                    conn.execute(
                        """UPDATE slot_capacity SET max_capacity = ?, is_open = ?
                           WHERE shop_id = ? AND date = ? AND time_slot = ?""",
                        (new_cap_val, 1 if slot_open else 0, gov_sid, str(gov_dt), target_slot)
                    )
                    conn.commit()
                st.success("Slot policy saved successfully.")
                st.rerun()

    # 5. GRIEVANCE REDRESSAL
    with adm_tabs[4]:
        st.subheader("Citizen Grievance Redressal Queue")
        all_comps = get_all_complaints()
        if all_comps:
            for cp in all_comps:
                status_color = "#15803D" if cp["status"] == "RESOLVED" else "#DC2626"
                with st.expander(f"Grievance #{cp['id']} | {cp['subject']} [{cp['status']}]"):
                    st.write(f"**Cardholder:** {cp['head_of_family']} ({cp['ration_card_number']})")
                    st.write(f"**Depot:** {cp['shop_name']}")
                    st.write(f"**Description:** {cp['description']}")
                    st.write(f"**Logged At:** {cp['created_at']}")

                    if cp["status"] != "RESOLVED":
                        res_notes = st.text_input("Resolution Notes", key=f"res_{cp['id']}", placeholder="Action taken by Civil Supplies Officer...")
                        if st.button("Mark Grievance Resolved", key=f"btn_res_{cp['id']}", type="primary"):
                            resolve_complaint(cp["id"], res_notes)
                            st.success("Grievance resolved.")
                            st.rerun()
                    else:
                        st.info(f"Resolution: {cp['resolution_notes']}")
        else:
            st.info("No grievances logged.")

    # 6. BROADCAST & COMMUNICATION CENTER
    with adm_tabs[5]:
        st.subheader("Statewide PDS Notification & Citizen Broadcast Center")
        st.caption("Broadcast urgent policy updates, festive allocations, stock arrival bulletins, or weather advisory alerts to beneficiaries via Email and SMS.")

        b_c1, b_c2 = st.columns([1, 1])
        with b_c1:
            with st.form("admin_broadcast_form"):
                bc_title = st.text_input("Broadcast Subject / Title *", placeholder="e.g. Festival Grain Allotment or Shop Timing Update")
                all_s = get_all_shops()
                shop_options = ["Statewide (All Registered Beneficiaries)"] + [f"{s['shop_name']} ({s['shop_number']})" for s in all_s]
                bc_scope = st.selectbox("Target Recipient Scope", shop_options)
                bc_channels = st.multiselect("Active Delivery Channels", ["Email", "SMS"], default=["Email", "SMS"])
                bc_msg = st.text_area("Official Bulletin Message *", placeholder="Enter the bulletin text to dispatch to cardholders...")

                bc_submit = st.form_submit_button("📢 Dispatch Statewide Broadcast", type="primary", use_container_width=True)
                if bc_submit:
                    if bc_title.strip() and bc_msg.strip():
                        # Determine target beneficiaries
                        with get_connection() as conn:
                            c = conn.cursor()
                            if "Statewide" in bc_scope:
                                c.execute("SELECT b.id, b.user_id, b.head_of_family, b.ration_card_number, b.phone, u.email FROM beneficiaries b JOIN users u ON b.user_id = u.id")
                            else:
                                target_shop_num = bc_scope.split("(")[-1].replace(")", "").strip()
                                c.execute("""SELECT b.id, b.user_id, b.head_of_family, b.ration_card_number, b.phone, u.email 
                                             FROM beneficiaries b 
                                             JOIN users u ON b.user_id = u.id 
                                             JOIN ration_shops rs ON b.assigned_shop_id = rs.id 
                                             WHERE rs.shop_number = ?""", (target_shop_num,))
                            recipients = c.fetchall()

                        cnt_dispatched = 0
                        for r in recipients:
                            r_dict = dict(r)
                            u_email = r_dict.get("email") or f"citizen_{r_dict.get('ration_card_number')}@smartration.gov.in"
                            u_phone = r_dict.get("phone") or "9876543210"

                            if "Email" in bc_channels:
                                send_email(
                                    to_email=u_email,
                                    subject=f"🌾 PDS Official Bulletin: {bc_title.strip()}",
                                    html_content=f"""
                                    <div style='font-family: Arial, sans-serif; padding: 20px;'>
                                        <h2 style='color: #1E3A8A;'>Department of Food & Civil Supplies</h2>
                                        <h3>{bc_title.strip()}</h3>
                                        <p>Dear {r_dict['head_of_family']},</p>
                                        <p>{bc_msg.strip()}</p>
                                        <hr>
                                        <small style='color: #64748B;'>Official State PDS Alert</small>
                                    </div>
                                    """,
                                    smtp_user=st.session_state.get("smtp_user"),
                                    smtp_pass=st.session_state.get("smtp_pass")
                                )

                            if "SMS" in bc_channels:
                                send_instant_sms(
                                    to_phone=u_phone,
                                    message=f"PDS Bulletin: {bc_title.strip()} - {bc_msg.strip()[:100]}",
                                    user_id=r_dict["user_id"]
                                )
                            cnt_dispatched += 1

                        st.success(f"✓ Broadcast successfully delivered to {cnt_dispatched} beneficiaries across {bc_channels}!")
                        st.toast(f"Broadcast sent to {cnt_dispatched} cardholders!")
                    else:
                        st.warning("Please fill in both subject and bulletin message.")

        with b_c2:
            st.markdown("##### 📡 Recent System Broadcast Logs")
            with get_connection() as conn:
                c = conn.cursor()
                c.execute("""SELECT n.id, n.title, n.message, n.channel, n.created_at, u.username, u.full_name 
                             FROM notifications n 
                             JOIN users u ON n.user_id = u.id 
                             ORDER BY n.created_at DESC LIMIT 15""")
                recent_notifs = c.fetchall()

            if recent_notifs:
                st.dataframe(pd.DataFrame([dict(n) for n in recent_notifs]), use_container_width=True)
            else:
                st.info("No system notifications logged yet.")

    # 7. ML TELEMETRY
    with adm_tabs[6]:
        st.subheader("Live Inference Telemetry & Prediction Audit")
        logs = get_recent_prediction_logs(limit=200)
        if logs:
            st.dataframe(pd.DataFrame([dict(l) for l in logs]), use_container_width=True)
        else:
            st.info("No telemetry logs yet.")

    # 8. ML STUDIO
    with adm_tabs[7]:
        render_data_science_studio()

# ==============================================================================
# VIEW: DATA SCIENCE & ML ANALYTICS STUDIO
# ==============================================================================
def render_data_science_studio():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%); border-radius: 18px; padding: 24px 28px; color: #FFFFFF; box-shadow: 0 4px 16px rgba(67,56,202,0.25); margin-bottom: 22px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #C7D2FE; text-transform: uppercase; letter-spacing: 0.08em;">MACHINE LEARNING & PREDICTIVE ANALYTICS ENGINE</div>
                <h2 style="margin: 4px 0; color: #FFFFFF; font-weight: 800; font-size: 1.55rem;">📊 PDS Data Science & AI Diagnostic Studio</h2>
                <div style="color: #E0E7FF; font-size: 0.88rem;">
                    5 Gradient Boosting Regressors • Chronological 80/20 Holdout Validation • Zero Data Leakage • Real-Time Interactive Simulator
                </div>
            </div>
            <div>
                <span class="pill-badge pill-emerald">● 5 MODELS VERIFIED</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.guest_analytics and not st.session_state.authenticated:
        if st.button("← Back to Role Selection Gateways", type="secondary"):
            st.session_state.guest_analytics = False
            st.rerun()

    ml_tabs = st.tabs([
        "🏆 Model Performance Comparison",
        "🎯 Diagnostic Validation Plots",
        "🔬 Interactive What-If Simulator",
        "📈 Exploratory Data Analysis (EDA)"
    ])

    # 1. MODEL PERFORMANCE COMPARISON
    with ml_tabs[0]:
        st.subheader("5-Target Model Evaluation Summary")
        if METRICS_REPORT_PATH.exists():
            with open(METRICS_REPORT_PATH, "r", encoding="utf-8") as f:
                m_data = json.load(f)

            summary_rows = []
            for k, v in m_data.items():
                bm = v["best_metrics"]
                summary_rows.append({
                    "Prediction Target": v["display_name"],
                    "Target Variable": v["target"],
                    "Best Algorithm": v["best_algorithm"],
                    "Test R² Score": bm["test_r2"],
                    "Test RMSE": bm["test_rmse"],
                    "Test MAE": bm["test_mae"],
                    "CV R² Score": bm["cv_r2"],
                    "Overfit Gap (R²)": bm["overfit_gap_r2"]
                })

            st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

            # Bar comparison
            fig_bar = px.bar(
                pd.DataFrame(summary_rows),
                x="Target Variable",
                y="Test R² Score",
                color="Best Algorithm",
                text="Test R² Score",
                title="Model Generalization Accuracy Across All 5 Targets (Test Holdout R²)"
            )
            fig_bar.update_traces(texttemplate='%{text:.4f}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Model evaluation metrics not found.")

    # 2. DIAGNOSTIC PLOTS
    with ml_tabs[1]:
        st.subheader("Actual vs Predicted & Residual Diagnostics")
        if METRICS_REPORT_PATH.exists():
            with open(METRICS_REPORT_PATH, "r", encoding="utf-8") as f:
                m_data = json.load(f)

            task_opts = list(m_data.keys())
            sel_task = st.selectbox("Select Model to Inspect", task_opts, format_func=lambda x: m_data[x]["display_name"])

            p1 = m_data[sel_task]["plots"]["actual_vs_pred"]
            p2 = m_data[sel_task]["plots"]["residuals"]

            p_col1, p_col2 = st.columns(2)
            if os.path.exists(p1):
                with p_col1:
                    st.image(p1, caption="Actual vs Predicted (Holdout Test Split)", use_container_width=True)
            if os.path.exists(p2):
                with p_col2:
                    st.image(p2, caption="Residual Distribution Diagnostic", use_container_width=True)

    # 3. WHAT-IF SIMULATOR
    with ml_tabs[2]:
        st.subheader("Real-Time Multi-Model What-If Simulator")
        st.caption("Adjust operational parameters to test multi-model inference simultaneously.")

        s1, s2 = st.columns(2)
        with s1:
            w_day = st.selectbox("Day of Week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], index=2, key="w_day")
            w_slot = st.selectbox("Operational Time Slot", OPERATIONAL_SLOTS, index=1, key="w_slot")
            w_hour = SLOT_HOUR_MAP.get(w_slot, 10)
            w_wknd = 1 if w_day in ["Saturday", "Sunday"] else 0
            w_hol = st.selectbox("Is Holiday Schedule", [0, 1], index=0, key="w_hol")
            w_bk = st.slider("Slot Bookings", 0, 40, 12, key="w_bk")
            w_pc = st.slider("Prior Crowd Footfall", 0, 80, 28, key="w_pc")
            w_pt = st.slider("Prior Transactions", 0, 60, 24, key="w_pt")

        with s2:
            w_staff = st.slider("Staff On Duty", 2, 5, 3, key="w_staff")
            w_cnt = st.slider("Counters Available", 1, 4, 2, key="w_cnt")
            w_bens = st.number_input("Registered Depot Beneficiaries", 500, 1500, 850, step=25, key="w_bens")
            w_rice = st.number_input("Rice Stock (kg)", value=520.0, step=20.0, key="w_rice")
            w_wheat = st.number_input("Wheat Stock (kg)", value=180.0, step=10.0, key="w_wheat")
            w_sugar = st.number_input("Sugar Stock (kg)", value=95.0, step=5.0, key="w_sugar")

        if st.button("⚡ Run Live Multi-Model Inference", type="primary", use_container_width=True):
            preds = predict_slot_comprehensive(
                shop_id=1,
                date_str=str(date.today()),
                day_name=w_day,
                hour=w_hour,
                time_slot=w_slot,
                is_weekend=w_wknd,
                is_holiday=w_hol,
                bookings=float(w_bk),
                previous_crowd=float(w_pc),
                previous_transactions=float(w_pt),
                staff_on_duty=w_staff,
                counters_available=w_cnt,
                registered_beneficiaries=w_bens,
                rice_stock_kg=w_rice,
                wheat_stock_kg=w_wheat,
                sugar_stock_kg=w_sugar,
                persist_log=True
            )

            st.markdown("#### Model Inference Results")
            r1, r2, r3, r4, r5 = st.columns(5)
            r1.metric("Predicted Customers", f"{preds['predicted_customers']:.0f} ppl")
            r2.metric("Predicted Wait Time", f"{preds['predicted_waiting_time_min']:.1f} mins")
            r3.metric("Rice Demand", f"{preds['predicted_rice_demand_kg']:.1f} kg")
            r4.metric("Wheat Demand", f"{preds['predicted_wheat_demand_kg']:.1f} kg")
            r5.metric("Sugar Demand", f"{preds['predicted_sugar_demand_kg']:.1f} kg")
            st.success("Computed via trained Gradient Boosting pipelines and saved to prediction logs.")

    # 4. EDA VISUALIZATIONS
    with ml_tabs[3]:
        st.subheader("Exploratory Data Analysis Gallery")
        eda_dir = REPORTS_DIR / "figures"
        if eda_dir.exists():
            fig_files = sorted(list(eda_dir.glob("*.png")))
            for i in range(0, len(fig_files), 2):
                f1, f2 = st.columns(2)
                with f1:
                    st.image(str(fig_files[i]), caption=fig_files[i].stem.replace("_", " ").title(), use_container_width=True)
                if i + 1 < len(fig_files):
                    with f2:
                        st.image(str(fig_files[i+1]), caption=fig_files[i+1].stem.replace("_", " ").title(), use_container_width=True)

# ==============================================================================
# MAIN APPLICATION CONTROLLER
# ==============================================================================
# Persistent Application Sidebar with Gateway Controls
with st.sidebar:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <div style="font-size: 34px; line-height: 1; background: #1C2541; padding: 8px; border-radius: 10px;">🌾</div>
        <div>
            <div style="font-weight: 800; font-size: 1.15rem; color: #FFFFFF; letter-spacing: -0.01em;">SMART RATION</div>
            <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Government of Karnataka</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.authenticated:
        curr_user = dict(st.session_state.user) if st.session_state.user else {}
        u_role = curr_user.get("role", "user")
        role_label = "CARDHOLDER" if u_role == "beneficiary" else ("FPS DEALER" if u_role == "dealer" else "DIRECTORATE")
        role_badge = "pill-emerald" if u_role == "dealer" else ("pill-amber" if u_role == "beneficiary" else "pill-blue")
        
        st.markdown(f"""
        <div style="background: #1C2541; border: 1px solid #3A506B; border-radius: 12px; padding: 14px 16px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span class="pill-badge {role_badge}">● {role_label}</span>
                <span style="font-size: 0.72rem; color: #94A3B8;">ONLINE</span>
            </div>
            <div style="font-weight: 800; color: #FFFFFF; font-size: 1.05rem;">{curr_user.get('full_name', 'User')}</div>
            <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 2px;">
                {f"Card: {curr_user.get('ration_card_number')}" if u_role == 'beneficiary' else (f"Depot: {curr_user.get('shop_name')}" if u_role == 'dealer' else "State Food Directorate")}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Sign Out of Portal", use_container_width=True):
            logout()
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Interactive SMTP & Notification Settings Drawer
    with st.expander("⚙️ Email & SMS Gateway Setup", expanded=False):
        st.markdown("<small style='color: #64748B;'>Configure SMTP for live internet email delivery to real Gmail / Outlook accounts, or keep local sandbox capture.</small>", unsafe_allow_html=True)

        has_creds = bool(st.session_state.get("smtp_user") and st.session_state.get("smtp_pass"))
        mode_idx = 1 if has_creds else 0
        gate_mode = st.radio(
            "Gateway Mode",
            ["📦 Local Sandbox (Zero config required)", "⚡ Live SMTP Delivery (Real Inboxes)"],
            index=mode_idx,
            key="gw_mode_radio"
        )

        if "Live" in gate_mode:
            st.caption("Email (Gmail/Outlook with App Password):")
            s_host = st.text_input("SMTP Server", value=st.session_state.get("smtp_server", SMTP_SERVER), key="side_smtp_server")
            s_port = st.number_input("SMTP Port", value=int(st.session_state.get("smtp_port", SMTP_PORT)), step=1, key="side_smtp_port")
            s_user = st.text_input("Your Email", value=st.session_state.get("smtp_user", SMTP_USERNAME), placeholder="user@gmail.com", key="side_smtp_user")
            s_pass = st.text_input("App Password", value=st.session_state.get("smtp_pass", SMTP_PASSWORD), type="password", placeholder="16-character app password", key="side_smtp_pass")

            st.caption("Cellular SMS (Fast2SMS for India):")
            s_f2s = st.text_input("Fast2SMS API Key", value=st.session_state.get("fast2sms_key", ""), type="password", placeholder="Paste Fast2SMS Key", key="side_f2s_key")

            c_s_save, c_s_test = st.columns(2)
            with c_s_save:
                if st.button("💾 Save", key="btn_save_smtp", use_container_width=True):
                    st.session_state["smtp_server"] = s_host
                    st.session_state["smtp_port"] = s_port
                    st.session_state["smtp_user"] = s_user.strip()
                    st.session_state["smtp_pass"] = s_pass.strip().replace(" ", "")
                    st.session_state["fast2sms_key"] = s_f2s.strip()
                    st.success("Credentials saved!")
            with c_s_test:
                if st.button("⚡ Test", key="btn_test_smtp", use_container_width=True):
                    if s_user and s_pass:
                        ok_t, msg_t = send_email(
                            to_email=s_user,
                            subject="🌾 Smart Ration: Live SMTP Connection Verified",
                            html_content="<h3>Connection Verified!</h3><p>Your Smart Ration System SMTP configuration is active and communicating with real mail servers.</p>",
                            smtp_user=s_user,
                            smtp_pass=s_pass
                        )
                        if ok_t:
                            st.success("Test email delivered to your inbox!")
                        else:
                            st.error(msg_t)
                    else:
                        st.warning("Enter email & password.")
        else:
            st.info("Operating in **Local Sandbox Mode**. All booking reminders and purchase receipts will be captured into SQLite notification tables without network dependencies.")

# View Routing
if st.session_state.authenticated:
    u_role = st.session_state.user["role"]
    if u_role == "beneficiary":
        render_authenticated_beneficiary()
    elif u_role == "dealer":
        render_authenticated_dealer()
    else:
        render_authenticated_admin()
elif st.session_state.guest_analytics:
    render_data_science_studio()
else:
    render_landing_portal()
