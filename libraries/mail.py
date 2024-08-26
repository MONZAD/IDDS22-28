#Proyecto MONZAD

from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header    import Header
from email.mime.text import MIMEText
from getpass         import getpass
from smtplib         import SMTP_SSL
from datetime import datetime

class mailer:
	def __init__(self, user="", pswd="", receiver=""):
		self.login=user
		self.psswd=pswd

	def getMessage(self, report):
	    	return """
			<html>
			  <body>
			  	<h1 align="center"><b>RESYS</b></h1>
				  <h2 align="center">Proyecto MONZAD</h2>
			    <br>
				<p align="justify">Reporte diario <br>
				<p align="justify">Reporte del día """+datetime.date.today()+"""</p>
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
		self.alertDT=datetime.now()
		msg = MIMEMultipart('related')
		msg['Subject'] = Header('Informe del día', 'utf-8')
		msg['From'] = self.login
		msg['To'] = emailUser

		msgAlt = MIMEMultipart('alternative')
		msg.attach(msgAlt)
		message=self.getMessage(report)
		msgT = MIMEText(message, 'html', 'utf-8')

        msgAlt.attach(msgT)
        #Adding report
        attach = MIMEApplication(report,_subtype="pdf")
        attach.add_header('Content-Disposition','attachment',filename="Informe del día "+(datetime.date.today()))
        msgAlt.attach(attach)
		
		# send it via gmail
		s = SMTP_SSL('smtp.gmail.com', 465, timeout=10)
		s.set_debuglevel(1)
		try:
			s.login(self.login, self.psswd)
			s.sendmail(msg['from'], msg['To'], msg.as_string())
		finally:
			s.quit()