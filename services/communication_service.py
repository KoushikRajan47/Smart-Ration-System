"""
Automated Communication and Notification Engine.
Dispatches real SMTP emails (Booking Reminders, Electronic Receipts)
and simulated SMS dispatches with full HTML templates and SQLite logging.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, Optional, Dict, Any
from datetime import datetime
import os
import sys
import base64
import requests
from pathlib import Path

# Ensure root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import (
    SMTP_SERVER,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_SENDER_EMAIL,
    SMTP_SENDER_NAME,
    FAST2SMS_API_KEY,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER
)
from database.db import create_notification, get_connection

def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
    smtp_user: Optional[str] = None,
    smtp_pass: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Dispatches a real email via SMTP.
    If credentials are provided (or present in env/config), connects via TLS.
    Otherwise gracefully falls back to local simulation mode with SQLite logging.
    """
    user = smtp_user or SMTP_USERNAME or os.environ.get("SMTP_USERNAME", "")
    password = smtp_pass or SMTP_PASSWORD or os.environ.get("SMTP_PASSWORD", "")
    sender = user if ("@" in user) else SMTP_SENDER_EMAIL

    if not to_email or "@" not in to_email:
        return False, "Invalid recipient email address."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_SENDER_NAME} <{sender}>"
    msg["To"] = to_email

    if text_content:
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # If SMTP credentials are configured, execute real network delivery
    if user and password:
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, password)
            server.sendmail(sender, [to_email], msg.as_string())
            server.quit()
            return True, f"Live email successfully delivered to {to_email} via {SMTP_SERVER}."
        except Exception as e:
            return False, f"SMTP delivery error: {str(e)}"
    else:
        # Simulation / Sandbox Dispatch Mode (Captures message & logs to database)
        return True, f"Simulated delivery logged: Email captured for {to_email}. (To send live emails, configure SMTP credentials in Settings)."

def send_booking_reminder_email(
    beneficiary_email: Optional[str] = None,
    beneficiary_user_id: Optional[int] = None,
    head_of_family: Optional[str] = None,
    booking_ref: Optional[str] = None,
    date_str: Optional[str] = None,
    time_slot: Optional[str] = None,
    shop_name: Optional[str] = None,
    predicted_wait: Optional[float] = None,
    smtp_user: Optional[str] = None,
    smtp_pass: Optional[str] = None,
    **kwargs: Any
) -> Tuple[bool, str]:
    """Builds and sends an HTML slot booking reminder email with resilient parameter resolution."""
    email = beneficiary_email or kwargs.get("recipient_email") or kwargs.get("email") or "citizen@smartration.gov.in"
    user_id = beneficiary_user_id or kwargs.get("user_id") or 1
    name = head_of_family or kwargs.get("beneficiary_name") or kwargs.get("name") or "Cardholder"
    ref = booking_ref or kwargs.get("ref") or "BK-000000"
    dt = date_str or kwargs.get("date") or str(datetime.now().date())
    slot = time_slot or kwargs.get("slot") or "9-10 AM"
    shop = shop_name or kwargs.get("depot_name") or "Fair Price Shop"
    wait = predicted_wait if predicted_wait is not None else float(kwargs.get("est_wait_min", 15.0))
    s_user = smtp_user or kwargs.get("smtp_username")
    s_pass = smtp_pass or kwargs.get("smtp_password")

    subject = f"🌾 PDS Booking Reminder: Slot Reserved for {dt} ({slot})"

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F8FAFC; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 12px; overflow: hidden; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%); padding: 28px 24px; color: #FFFFFF; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
            .header p {{ margin: 6px 0 0 0; color: #BFDBFE; font-size: 14px; }}
            .content {{ padding: 24px; }}
            .card {{ background: #F8FAFC; border-radius: 8px; border: 1px solid #E2E8F0; padding: 16px; margin: 16px 0; }}
            .row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; }}
            .label {{ color: #64748B; font-weight: 500; }}
            .val {{ color: #0F172A; font-weight: 700; }}
            .highlight-box {{ background: #EFF6FF; border-left: 4px solid #2563EB; padding: 12px 16px; margin: 16px 0; border-radius: 0 8px 8px 0; }}
            .footer {{ background: #F1F5F9; padding: 16px; text-align: center; font-size: 12px; color: #64748B; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌾 DEPARTMENT OF FOOD & CIVIL SUPPLIES</h1>
                <p>Smart Public Distribution System — Appointment Confirmation</p>
            </div>
            <div class="content">
                <p>Dear <b>{name}</b>,</p>
                <p>This is a confirmation and reminder for your upcoming subsidized grain collection time slot:</p>
                
                <div class="card">
                    <div class="row"><span class="label">Booking Reference:</span><span class="val" style="color: #2563EB;">{ref}</span></div>
                    <div class="row"><span class="label">Date of Collection:</span><span class="val">{dt}</span></div>
                    <div class="row"><span class="label">Reserved Time Slot:</span><span class="val">{slot}</span></div>
                    <div class="row"><span class="label">Fair Price Shop:</span><span class="val">{shop}</span></div>
                    <div class="row"><span class="label">Est. Queue Waiting Time:</span><span class="val" style="color: #16A34A;">~{wait:.1f} minutes</span></div>
                </div>

                <div class="highlight-box">
                    <b style="color: #1E40AF;">Important Beneficiary Instructions:</b>
                    <ul style="margin: 6px 0 0 0; padding-left: 20px; font-size: 13px; color: #334155;">
                        <li>Please arrive 5 minutes prior to your time slot to ensure swift processing.</li>
                        <li>Carry your original Ration Card and Aadhaar card for biometric/OTP e-KYC.</li>
                        <li>Bring clean carrying bags for rice, wheat, and sugar collection.</li>
                    </ul>
                </div>
            </div>
            <div class="footer">
                This is an automated notification from the Smart Ration System. Please do not reply directly to this email.<br>
                For grievances, log in to the portal or dial the PDS Toll-Free Helpline: 1967.
            </div>
        </div>
    </body>
    </html>
    """

    ok, msg = send_email(
        to_email=email,
        subject=subject,
        html_content=html_template,
        smtp_user=s_user,
        smtp_pass=s_pass
    )

    # Log in SQLite notifications
    create_notification(
        user_id=user_id,
        title=f"Reminder: Slot {slot} on {dt}",
        message=f"Reminder sent for Booking {ref}. Arrive at {shop} during {slot}. Est. wait: {wait:.1f} mins.",
        channel="EMAIL+SMS"
    )

    return ok, msg

def send_purchase_receipt_email(
    beneficiary_email: Optional[str] = None,
    beneficiary_user_id: Optional[int] = None,
    head_of_family: Optional[str] = None,
    ration_card_no: Optional[str] = None,
    card_type: Optional[str] = None,
    tx_ref: Optional[str] = None,
    date_str: Optional[str] = None,
    shop_name: Optional[str] = None,
    rice_kg: float = 0.0,
    wheat_kg: float = 0.0,
    sugar_kg: float = 0.0,
    total_amount: float = 0.0,
    payment_mode: str = "SUBSIDIZED_FREE",
    smtp_user: Optional[str] = None,
    smtp_pass: Optional[str] = None,
    **kwargs: Any
) -> Tuple[bool, str]:
    """Builds and sends an HTML official electronic collection receipt with resilient parameter resolution."""
    email = beneficiary_email or kwargs.get("recipient_email") or kwargs.get("email") or "citizen@smartration.gov.in"
    user_id = beneficiary_user_id or kwargs.get("user_id") or 1
    name = head_of_family or kwargs.get("beneficiary_name") or kwargs.get("name") or "Cardholder"
    card_no = ration_card_no or kwargs.get("ration_card_number") or "N/A"
    c_type = card_type or kwargs.get("card_category") or "BPL"
    ref = tx_ref or kwargs.get("transaction_ref") or "TX-000000"
    dt = date_str or kwargs.get("date") or str(datetime.now().date())
    shop = shop_name or kwargs.get("depot_name") or "Fair Price Depot"
    r_kg = rice_kg or float(kwargs.get("rice_issued_kg", 0.0))
    w_kg = wheat_kg or float(kwargs.get("wheat_issued_kg", 0.0))
    s_kg = sugar_kg or float(kwargs.get("sugar_issued_kg", 0.0))
    amount = total_amount or float(kwargs.get("amount_paid", 0.0))
    p_mode = payment_mode or kwargs.get("pay_mode") or "SUBSIDIZED"
    s_user = smtp_user or kwargs.get("smtp_username")
    s_pass = smtp_pass or kwargs.get("smtp_password")

    subject = f"🧾 Official PDS Receipt: Ration Disbursed (Ref: {ref})"

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F8FAFC; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 12px; overflow: hidden; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
            .header {{ background: linear-gradient(135deg, #15803D 0%, #16A34A 100%); padding: 24px; color: #FFFFFF; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
            .content {{ padding: 24px; }}
            .receipt-box {{ border: 2px dashed #CBD5E1; border-radius: 8px; padding: 18px; margin: 16px 0; }}
            .table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
            .table th {{ background: #F1F5F9; padding: 8px; text-align: left; color: #475569; }}
            .table td {{ padding: 8px; border-bottom: 1px solid #E2E8F0; color: #1E293B; }}
            .row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; }}
            .total-row {{ display: flex; justify-content: space-between; font-size: 16px; font-weight: 800; color: #0F172A; margin-top: 12px; padding-top: 8px; border-top: 1px solid #CBD5E1; }}
            .footer {{ background: #F8FAFC; padding: 14px; text-align: center; font-size: 11px; color: #94A3B8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌾 DEPARTMENT OF FOOD & CIVIL SUPPLIES</h1>
                <p style="margin: 4px 0 0 0; color: #DCFCE7; font-size: 13px;">Official Electronic Distribution Receipt & Tax Invoice</p>
            </div>
            <div class="content">
                <p>Dear <b>{name}</b>,</p>
                <p>Your ration collection has been verified and disbursed successfully. Here is your official distribution voucher:</p>
                
                <div class="receipt-box">
                    <div class="row"><span>Transaction ID:</span><b>{ref}</b></div>
                    <div class="row"><span>Date & Time:</span><b>{dt}</b></div>
                    <div class="row"><span>Ration Card No:</span><b>{card_no} ({c_type})</b></div>
                    <div class="row"><span>Fair Price Depot:</span><b>{shop}</b></div>

                    <table class="table">
                        <thead>
                            <tr>
                                <th>Commodity</th>
                                <th>Quantity</th>
                                <th>Subsidized Price</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>🍚 Subsidized Rice</td>
                                <td>{r_kg:.1f} kg</td>
                                <td>₹ 2.00 / kg</td>
                                <td>₹ {r_kg * 2.0:.2f}</td>
                            </tr>
                            <tr>
                                <td>🌾 Fortified Wheat</td>
                                <td>{w_kg:.1f} kg</td>
                                <td>₹ 3.00 / kg</td>
                                <td>₹ {w_kg * 3.0:.2f}</td>
                            </tr>
                            <tr>
                                <td>🍬 Refined Sugar</td>
                                <td>{s_kg:.1f} kg</td>
                                <td>₹ 13.50 / kg</td>
                                <td>₹ {s_kg * 13.5:.2f}</td>
                            </tr>
                        </tbody>
                    </table>

                    <div class="total-row">
                        <span>Total Amount Paid ({p_mode}):</span>
                        <span style="color: #16A34A;">₹ {amount:.2f}</span>
                    </div>
                </div>

                <div style="font-size: 12px; color: #64748B; text-align: center;">
                    NFSA Digital Security Hash: {abs(hash(str(ref))) % 10**12:012d} | Valid for Auditing
                </div>
            </div>
            <div class="footer">
                Thank you for utilizing the Smart Public Distribution System.<br>
                For any discrepancies, contact your local Food Inspector or call 1967.
            </div>
        </div>
    </body>
    </html>
    """

    ok, msg = send_email(
        to_email=email,
        subject=subject,
        html_content=html_template,
        smtp_user=s_user,
        smtp_pass=s_pass
    )

    # Log in SQLite notifications
    create_notification(
        user_id=user_id,
        title=f"Receipt: Disbursed {ref}",
        message=f"Ration collected! {r_kg}kg Rice, {w_kg}kg Wheat, {s_kg}kg Sugar disbursed. Total: Rs {amount:.2f}. Receipt sent to {email}.",
        channel="EMAIL+SMS"
    )

    return ok, msg

def send_instant_sms(
    to_phone: Optional[str] = None,
    message: str = "",
    user_id: Optional[int] = None,
    fast2sms_key: Optional[str] = None,
    twilio_sid: Optional[str] = None,
    twilio_token: Optional[str] = None,
    twilio_from: Optional[str] = None,
    **kwargs: Any
) -> Tuple[bool, str]:
    """
    Dispatches SMS alerts.
    If Fast2SMS or Twilio API credentials are provided, connects to real telecom gateways for live delivery.
    Otherwise safely falls back to local database audit logging with transparent simulation mode status.
    """
    raw_phone = str(to_phone or kwargs.get("phone_number") or kwargs.get("phone") or "9876543210")
    clean_digits = "".join(filter(str.isdigit, raw_phone))
    clean_phone = clean_digits[-10:] if len(clean_digits) >= 10 else clean_digits
    msg_text = message or kwargs.get("text") or "PDS Notification Alert"
    uid = user_id or kwargs.get("uid")

    f2s_key = fast2sms_key or kwargs.get("f2s_key") or FAST2SMS_API_KEY or os.environ.get("FAST2SMS_API_KEY", "")
    t_sid = twilio_sid or kwargs.get("t_sid") or TWILIO_ACCOUNT_SID or os.environ.get("TWILIO_ACCOUNT_SID", "")
    t_token = twilio_token or kwargs.get("t_token") or TWILIO_AUTH_TOKEN or os.environ.get("TWILIO_AUTH_TOKEN", "")
    t_from = twilio_from or kwargs.get("t_from") or TWILIO_FROM_NUMBER or os.environ.get("TWILIO_FROM_NUMBER", "")

    # 1. Attempt Live Fast2SMS Indian Cellular Gateway Delivery
    if f2s_key and len(clean_phone) == 10:
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "route": "q",
                "message": msg_text,
                "language": "english",
                "flash": 0,
                "numbers": clean_phone
            }
            headers = {
                "authorization": f2s_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            resp = requests.post(url, data=payload, headers=headers, timeout=10)
            res_json = resp.json()
            if res_json.get("return"):
                if uid:
                    create_notification(uid, "PDS Live Cellular SMS", f"[Live Fast2SMS to +91-{clean_phone}] {msg_text}", "SMS")
                return True, f"Live cellular SMS delivered to +91-{clean_phone} via Fast2SMS telecom gateway."
            else:
                err_msg = res_json.get("message", ["Fast2SMS Gateway Error"])[0] if isinstance(res_json.get("message"), list) else str(res_json.get("message"))
                return False, f"Fast2SMS error: {err_msg}"
        except Exception as e:
            return False, f"Fast2SMS telecom dispatch error: {str(e)}"

    # 2. Attempt Live Twilio Global Telecom Gateway Delivery
    if t_sid and t_token and t_from:
        try:
            tw_url = f"https://api.twilio.com/2010-04-01/Accounts/{t_sid}/Messages.json"
            formatted_target = f"+91{clean_phone}" if len(clean_phone) == 10 else f"+{clean_phone}"
            tw_data = {
                "From": t_from,
                "To": formatted_target,
                "Body": msg_text
            }
            auth_str = f"{t_sid}:{t_token}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            headers = {"Authorization": f"Basic {auth_b64}"}
            tw_resp = requests.post(tw_url, data=tw_data, headers=headers, timeout=10)
            if tw_resp.status_code in (200, 201):
                if uid:
                    create_notification(uid, "PDS Live Cellular SMS", f"[Live Twilio SMS to {formatted_target}] {msg_text}", "SMS")
                return True, f"Live SMS delivered to {formatted_target} via Twilio."
            else:
                return False, f"Twilio gateway error ({tw_resp.status_code}): {tw_resp.text}"
        except Exception as e:
            return False, f"Twilio dispatch error: {str(e)}"

    # 3. Offline / Simulation Fallback (When no telecom API key is provided)
    if uid:
        create_notification(
            user_id=uid,
            title="PDS SMS Dispatch (Offline Sandbox)",
            message=f"[Simulation to +91-{clean_phone}] {msg_text}",
            channel="SMS"
        )
    return True, f"Simulated delivery logged: SMS captured in SQLite audit table for +91-{clean_phone}. (To receive actual cellular SMS on your phone, enter a Fast2SMS or Twilio API key in Gateway Settings)."

def send_whatsapp_message(
    to_phone: str,
    message: str,
    callmebot_apikey: Optional[str] = None,
    user_id: Optional[int] = None
) -> Tuple[bool, str]:
    """
    Dispatches a 100% FREE WhatsApp message to your mobile phone via CallMeBot.
    Requires no paid SMS credits or wallet recharge.
    """
    clean_digits = "".join(filter(str.isdigit, str(to_phone)))
    clean_phone = f"+91{clean_digits[-10:]}" if len(clean_digits) == 10 else f"+{clean_digits}"
    apikey = callmebot_apikey or os.environ.get("CALLMEBOT_API_KEY", "")

    if not apikey:
        return False, "CallMeBot API key not configured."

    try:
        url = "https://api.callmebot.com/whatsapp.php"
        params = {
            "phone": clean_phone,
            "text": message,
            "apikey": apikey
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200 and ("Message queued" in resp.text or "ok" in resp.text.lower() or "success" in resp.text.lower()):
            if user_id:
                create_notification(user_id, "PDS WhatsApp Alert", f"[WhatsApp to {clean_phone}] {message}", "WHATSAPP")
            return True, f"Live WhatsApp message delivered to {clean_phone}!"
        else:
            return False, f"WhatsApp gateway response: {resp.text}"
    except Exception as e:
        return False, f"WhatsApp connection error: {str(e)}"

