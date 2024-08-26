#Proyecto MONZAD

from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header    import Header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from getpass         import getpass
from email import encoders
#from smtplib         import SMTP_SSL
import smtplib
import ssl
from datetime import datetime

class mailer:
	def __init__(self, user="", pswd=""):
		self.user_login=user
		self.user_psswd=pswd

	def getMessage(self, report):
	    	return """
				<html>
				<body>
					<h1 align="center"><b>MONZAD</b></h1>
					<h2 align="center">Proyecto MONZAD</h2>
					<br>
					<p align="justify">Reporte del día</p>
					<br>

				<h3 align="center">MONZAD</h3>
				<h5 align="center">Version 1.0</h5>
				<style>
					h1, h2{
						background-color: lightblue;
						border: 2px solid green;
						border-radius: 25px;
					}
					h3, h5 {
						background-color: blue;
						color: white;
					}
					</style>
				</body>
				</html>"""
	
	def getBasicMail(self, emailUser="", report=None):
		port = 587
		context = ssl.create_default_context()
		msg = MIMEMultipart()#'related')
		msg['Subject'] = Header('Informe del día', 'utf-8')
		msg['From'] = self.user_login
		msg['To'] = emailUser

		#msg.attach(MIMEText("Hola mundo", 'plain'))

		msgAlt = MIMEMultipart('alternative')
		msg.attach(msgAlt)
		message=self.getMessage(report)
		msgT = MIMEText(message, 'html', 'utf-8')
		msgAlt.attach(msgT)

		filename = open(report, 'rb')
		attach_MIME = MIMEBase('application', 'octet-stream')
		attach_MIME.set_payload((filename).read())

		encoders.encode_base64(attach_MIME)
		attach_MIME.add_header('Content-Disposition', "attachment; filename = %s" % report)
		msg.attach(attach_MIME)
		# send it via gmail
		with smtplib.SMTP("smtp-mail.outlook.com", port) as s:
			s.starttls(context=context)
			s.login(self.user_login, self.user_psswd)
			s.sendmail(
				self.user_login,
				emailUser,
				msg.as_string()#message
			)
			s.quit()