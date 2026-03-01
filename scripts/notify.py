"""
notify.py - Sends Gmail notification when reels are ready.

Reuses the same Gmail SMTP pattern from LATEST-AI-RADAR and NATE-HERK-RADAR.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime


def generate_email_html(reels_info):
    """Generate styled HTML email for reel notifications."""
    today = datetime.now().strftime("%B %d, %Y")
    reel_rows = ""

    for i, reel in enumerate(reels_info, 1):
        reel_rows += f"""
        <tr>
            <td style="padding:12px; border-bottom:1px solid #333; color:#fff; font-weight:bold;">
                Reel #{i}
            </td>
            <td style="padding:12px; border-bottom:1px solid #333; color:#ddd;">
                {reel.get('title', 'AI Tool Update')[:60]}
            </td>
            <td style="padding:12px; border-bottom:1px solid #333; color:#aaa;">
                {reel.get('source', 'unknown').replace('_', ' ').title()}
            </td>
            <td style="padding:12px; border-bottom:1px solid #333; color:#0af;">
                {reel.get('duration', 'N/A')}
            </td>
        </tr>"""

    html = f"""
    <html>
    <body style="margin:0; padding:0; background:#0a0a14; font-family:Arial,sans-serif;">
        <div style="max-width:600px; margin:0 auto; background:#0a0a14;">
            <!-- Header -->
            <div style="background:linear-gradient(135deg,#8250ff,#3c78ff); padding:30px; text-align:center; border-radius:8px 8px 0 0;">
                <h1 style="color:#fff; margin:0; font-size:24px;">AI REELS GENERATOR</h1>
                <p style="color:rgba(255,255,255,0.8); margin:8px 0 0;">Your daily Instagram reels are ready!</p>
            </div>

            <!-- Date -->
            <div style="padding:20px 30px; background:#111;">
                <p style="color:#888; margin:0;">Generated on <strong style="color:#fff;">{today}</strong></p>
            </div>

            <!-- Reels Table -->
            <div style="padding:0 30px 20px; background:#111;">
                <table style="width:100%; border-collapse:collapse;">
                    <tr style="background:#1a1a2e;">
                        <th style="padding:10px 12px; text-align:left; color:#8250ff; font-size:13px;">#</th>
                        <th style="padding:10px 12px; text-align:left; color:#8250ff; font-size:13px;">TOPIC</th>
                        <th style="padding:10px 12px; text-align:left; color:#8250ff; font-size:13px;">SOURCE</th>
                        <th style="padding:10px 12px; text-align:left; color:#8250ff; font-size:13px;">DURATION</th>
                    </tr>
                    {reel_rows}
                </table>
            </div>

            <!-- Instructions -->
            <div style="padding:20px 30px; background:#111;">
                <p style="color:#ddd; font-size:14px; line-height:1.6;">
                    Your reels are ready for posting! Each reel comes with:
                </p>
                <ul style="color:#aaa; font-size:14px; line-height:1.8;">
                    <li>MP4 video file (1080x1920, ready for Instagram)</li>
                    <li>Caption text file with hashtags</li>
                </ul>
                <p style="color:#888; font-size:13px;">
                    Find your reels at:<br>
                    <code style="color:#0af;">AI-REELS-GENERATOR/output/{datetime.now().strftime('%Y-%m-%d')}/</code><br>
                    <span style="color:#666;">(inside your Desktop/Projects folder)</span>
                </p>
            </div>

            <!-- Footer -->
            <div style="padding:20px 30px; background:#0a0a14; text-align:center; border-radius:0 0 8px 8px;">
                <p style="color:#555; font-size:12px; margin:0;">
                    AI Reels Generator | Content from Matt Wolfe & Nate Herk
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def generate_email_text(reels_info):
    """Generate plain text fallback email."""
    today = datetime.now().strftime("%B %d, %Y")
    text = f"AI REELS GENERATOR - {today}\n{'='*40}\n\n"
    text += "Your daily Instagram reels are ready!\n\n"

    for i, reel in enumerate(reels_info, 1):
        text += f"Reel #{i}: {reel.get('title', 'AI Tool Update')[:60]}\n"
        text += f"  Source: {reel.get('source', 'unknown').replace('_', ' ').title()}\n"
        text += f"  Duration: {reel.get('duration', 'N/A')}\n\n"

    text += f"Find your reels in: output/{datetime.now().strftime('%Y-%m-%d')}/\n"
    return text


def send_notification(reels_info, gmail_address=None, gmail_password=None, notify_email=None):
    """Send Gmail notification when reels are ready."""
    gmail_address = gmail_address or os.getenv("GMAIL_ADDRESS")
    gmail_password = gmail_password or os.getenv("GMAIL_APP_PASSWORD")
    notify_email = notify_email or os.getenv("NOTIFY_EMAIL", gmail_address)

    if not gmail_address or not gmail_password:
        print("Warning: Gmail credentials not set. Skipping notification.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Reels Ready - {datetime.now().strftime('%b %d, %Y')} ({len(reels_info)} reels)"
    msg["From"] = gmail_address
    msg["To"] = notify_email

    text_part = MIMEText(generate_email_text(reels_info), "plain")
    html_part = MIMEText(generate_email_html(reels_info), "html")
    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_address, gmail_password)
            server.sendmail(gmail_address, notify_email, msg.as_string())
        print(f"Notification sent to {notify_email}")
        return True
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test notification
    test_reels = [
        {"title": "Claude Code Changed Everything", "source": "nate_herk", "duration": "45s"},
        {"title": "5 Free AI Tools You Need", "source": "matt_wolfe", "duration": "38s"},
        {"title": "n8n Automation Secrets", "source": "nate_herk", "duration": "52s"},
    ]

    send_notification(test_reels)
