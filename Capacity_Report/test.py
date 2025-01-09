from email import encoders
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.message import Message
from configparser import ConfigParser
htmlbody = "test"
msg = MIMEMultipart('alternative')
msg['Subject'] = "Allianz Capacity Report - All Aggregates\n"
msg_from  = "daily-aggr-capacity@allianz.com.au"
msg_to = "appam.madhu@netapp.com"
msg['From'] = msg_from
msg['To'] = msg_to
msg_content = MIMEText(htmlbody, "html")
msg.attach(msg_content)
s = smtplib.SMTP('10.90.36.17',) #, '587')
#s.login('dhananjaypossible@gmail.com', '9mpG6OhVYk0UbWd5')
s.sendmail(msg_from, msg_to, msg.as_string())
s.quit()