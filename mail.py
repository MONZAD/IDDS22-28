from libraries.mailer import *
from datetime import datetime
import json
import sqlite3
from fpdf import FPDF
import time

#Loading the database 
def getJSONValues():
    dataValues = []
    with open('data.json', 'r') as jsonDataF:
        load_file = json.load(jsonDataF)
        dataValues.append({"ltModel":load_file["ltModel"], "dbConn":load_file["dbConn"]})
    return dataValues

def generateDailyReport():
    #try:
    sumPV = 0
    sumPM = 0
    promPV = 0
    promPM = 0
    global crowdName
    crowdName="Galera1"
    dataValues = getJSONValues()
    conn = sqlite3.connect(dataValues[0]["dbConn"])
    con = conn.cursor()
    con.execute('select idCrowd, chickInitQuant from crowd where crowdName = ?;', (crowdName, ))
    idCrowd = con.fetchall()
    conn = sqlite3.connect(dataValues[0]["dbConn"])
    con = conn.cursor()
    con.execute('select estudio.numEstudio, dateEst, cantPVivos, cantPMuertos from estudio inner join cantPollos on estudio.numEstudio = cantPollos.numEstudio where estudio.idCrowd= ?;', (str(idCrowd[0][0]), ))
    estudio = con.fetchall()
    con.close()
    pdf = FPDF()
    pdf.add_page()

    page_width = pdf.w -2 * pdf.l_margin

    pdf.set_font('Times', 'B', 14.0)
    pdf.cell(page_width, 0.0, crowdName, align='C')
    pdf.ln(10)
    pdf.cell(page_width, 0.0, 'Datos de los estudios', align='C')

    pdf.ln(10)
    pdf.set_font('Courier', '', 12)
    col_width = page_width/4
    pdf.ln(1)

    th = pdf.font_size

    pdf.cell(page_width/2, th, 'Cantidad de pollos iniciales', border=1)
    pdf.cell(page_width/2, th, str(idCrowd[0][1]), border=1)
    pdf.ln(10)
    
    pdf.cell(col_width, th, "# Estudio", border=1)
    pdf.cell(col_width, th, "Fecha", border=1)
    pdf.cell(col_width, th, "Detectados", border=1)
    pdf.cell(col_width, th, "No detectados", border=1)
    pdf.ln(th)
    for row in estudio:
        pdf.cell(col_width, th, str(row[0]), border=1)
        pdf.cell(col_width, th, str(row[1]), border=1)
        pdf.cell(col_width, th, str(row[2]), border=1)
        pdf.cell(col_width, th, str(row[3]), border=1)
        pdf.ln(th)
    
    pdf.ln(10)
    for est in estudio:
        sumPV += est[2]
        sumPM += est[3]
    
    promPV = sumPV/len(estudio)
    promPM = sumPM/len(estudio)
    
    pdf.cell(col_width, th, 'Promedios', border=1)
    pdf.ln(th)
    pdf.cell(col_width, th, "Detectados", border=1)
    pdf.cell(col_width, th, "No detectados", border=1)
    pdf.ln(th)
    pdf.cell(col_width, th, str(round(promPV, 0)), border=1)
    pdf.cell(col_width, th, str(round(promPM, 0)), border=1)
    pdf.ln(th)
    pdf.ln(th)
    pdf.set_font('Times', '', 10.0)
    pdf.cell(page_width, 0.0, '- Fin del reporte', align='C')
    pdf.output("reports/"+crowdName+".pdf", 'F')#name = str(crowdName)+".pdf", dest='S')
    #except Exception as e:
    #    print(e)

def send_Mail(mailSystem=None, psswdSystem=None, emailUser=None):
    #try:
    """ now = datetime.now()
    current_hour = now.strftime("%H")
    current_minutes = now.strftime("%M")
    if(current_hour == "8"):#if(current_time == "23:59:59"):
        current_minutes = int(current_minutes)
        if(current_minutes >= 50 and current_minutes <= 50):"""
    print("AQUÍ")
    #print(mailSystem, psswdSystem, emailUser)
    mailer2 = mailer(mailSystem, psswdSystem)
    print(type(mailer2))
    generateDailyReport()
    time.sleep(1)
    mailer2.getBasicMail(emailUser, report="reporte.pdf")
    #except Exception as e:
    #    print(e)

send_Mail(mailSystem="monzad2023@outlook.com", psswdSystem="MonZ4d23", emailUser="fedgo5462@gmail.com")