#!/usr/bin/env python2.7
from mailer import Mailer
from mailer import Message
import datetime
####################################################
date = datetime.date.today()
message = Message(From="GSSC-MS@netapp.com",
                  To=["naveen7@netapp.com"],
                  Subject="GovDC Infrastructure Health-Check Report",
                  charset="utf-8")
filelocation = "./Output/InfraHC.html".format(date)
message.Body = """Please find attached Health-Check Report"""
message.attach(filelocation)
sender = Mailer('10.151.107.5')
sender.send(message)
