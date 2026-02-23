import smtplib

smtp_server = "smtp-relay.brevo.com"
port = 587
username = "98f3e3001@smtp-brevo.com"
password = "fFxAQ8yNnrOV5gSz"

try:
    server = smtplib.SMTP(smtp_server, port)
    server.starttls()
    server.login(username, password)
    print("✅ Login successful — credentials are correct.")
    server.quit()
except smtplib.SMTPAuthenticationError:
    print("❌ Authentication failed — username or password incorrect.")
except Exception as e:
    print(f"⚠️ Error: {e}")
