import smtplib
import ssl

# ✅ Set port to 587
port = 587
smtp_server = "smtp-mail.outlook.com"#'smtp.gmail.com'
sender_email = "monzad2023@outlook.com"
receiver_email = "fedgo5462@gmail.com"
password = "MonZ4d23"

message = '''Hola'''
#Create the SSLContext object
context = ssl.create_default_context()

#Use smtplib.SMTP() class
with smtplib.SMTP(smtp_server, port) as server:
    #Put the connection into TLS mode
    server.starttls(context=context)
    server.login(sender_email, password)
    server.sendmail(
        sender_email,
        receiver_email,
        message
    )
    server.quit()
