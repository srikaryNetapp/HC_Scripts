import mysql.connector
from mysql.connector import Error
import pandas as pd
import datetime
from email import encoders
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.message import Message
from configparser import ConfigParser
import os
class MySqlCon(object):

    def __init__(self, host,config):
        self.host = host
        self.conn = None
        self.cursor = None
        self.config = config
    def __enter__(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host, user=self.config['AIQUM']['user'], password=self.config['AIQUM']['password'])
            self.info = self.conn.get_server_info()
            self.cursor = self.conn.cursor(dictionary=True)
            return self
        except Error as e:
            print((str(e)))

    def __exit__(self, exception_type, exception_val, trace):
        if not self.conn is None:
            self.cursor.close()
            self.conn.close()

    def aggr_model_view(self, query):
        self.cursor.execute(query)
        records = self.cursor.fetchall()
        return records

    def aggr_ocum_view(self, query):
        self.cursor.execute(query)
        records = self.cursor.fetchall()
        return records

    def get_clusters(self, query):
        self.cursor.execute(query)
        records = self.cursor.fetchall()
        return records
def sendmail(htmlbody):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Capacity Repport Test\n"
    msg['From'] = "dhananjay.kumar@netapp.com"
    msg['To'] = "dhananjay.kumar@netapp.com;dhananjay.kumar@netapp.com"
    msg_content = MIMEText(htmlbody, "html")
    msg.attach(msg_content)
    s = smtplib.SMTP('smtp-relay.sendinblue.com', '587')
    s.login('dhananjaypossible@gmail.com', '9mpG6OhVYk0UbWd5')
    s.sendmail("dhananjay.kumar@netapp.com",
               "dhananjay.kumar@netapp.com", msg.as_string())
    s.quit()

def main():

    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__),'utils/.config.ini'))
    cls_query = ("SELECT objid as id, name FROM netapp_model_view.cluster;")
    ocum_list = config['AIQUM']['aiqum'].split(',')
    html = ""
    date = datetime.date.today()
    for ocum in ocum_list:
        with MySqlCon(ocum,config) as con:
            if not con is None:
                print("Connect to OCUM")
                clusters = pd.DataFrame(con.get_clusters(cls_query))
                cluster_ids = list(clusters['id'])
                Cluster_names = list(clusters['name'])
                for i in range(0,len(cluster_ids)):
                    aggr_query = f"""
                    SELECT name as Aggregate,ROUND(sizeTotal/1099511627776,1) as 'Total Data Capacity (TB)',ROUND(sizeUsed/1099511627776,1) as 'Used Data Capacity (TB)', ROUND(sizeAvail/1099511627776,1) as 'Available Data Capacity (TB)', sizeUsedPercent as 'Used Data %',
                    CASE
                    WHEN sizeAvailPercent IS NULL and sizeUsedPercent = 0 THEN 100
                    ELSE sizeAvailPercent
                    END AS 'Available Data %',
                    CASE
                    when bytesUsedPerDay >= 0 THEN ROUND((bytesUsedPerDay/sizeTotal)*100,1)
                    when bytesUsedPerDay < 0 THEN 0
                    END AS 'Daily Growth Rate %',
                    CASE
                    when daysUntilFull IS NULL THEN 'Learning'
                    ELSE ROUND(daysUntilFull,0)
                    END AS 'Days To Full'
                    FROM netapp_model_view.aggregate inner join ocum_view.aggregate ON netapp_model_view.aggregate.objid = ocum_view.aggregate.id where clusterId = {cluster_ids[i]};
                    """
                    aggr_df = pd.DataFrame(con.get_clusters(aggr_query))
                    aggr_df = aggr_df.loc[:, ['Aggregate', "Total Data Capacity (TB)", "Used Data Capacity (TB)", 'Available Data Capacity (TB)', "Used Data %", 'Available Data %', "Daily Growth Rate %",
                                       'Days To Full']]
                    aggr_df['Daily Growth Rate %'] = aggr_df['Daily Growth Rate %'].astype(
                        str)
                    aggr_df['Available Data %'] = aggr_df['Available Data %'].astype(
                        str)
                    aggr_df['Available Data Capacity (TB)'] = aggr_df['Available Data Capacity (TB)'].astype(
                        str)
                    aggr_df['Used Data %'] = aggr_df['Used Data %'].astype(
                        str)
                    aggr_df['Used Data Capacity (TB)'] = aggr_df['Used Data Capacity (TB)'].astype(
                        str)
                    aggr_df['Total Data Capacity (TB)'] = aggr_df['Total Data Capacity (TB)'].astype(
                   str)
                    styles = [dict(selector="tr:hover",props=[("background", "#bebeda"), ("width", "fit-content")]),dict(selector="th", props=[("color", "#e6e6e6"),("border", "1px solid #eee"),("padding", "12px 35px"),("border-collapse", "collapse"),("background", "#605ef5"),("text-transform", "uppercase"),("font-size", "10px")]),
                    dict(selector="td", props=[("color", "black"),("width", "fit-content"),("border", "1px solid #eee"),("padding", "12px 35px"),("border-collapse", "collapse"),("font-size", "12px"),("font-weight", "990")]),
                    dict(selector="table", props=[("table-layout", "auto"),("width", "fit-content"),("hight", "fit-content"),("font-family", 'Arial'),("margin", "25px auto"),("border-collapse", "collapse"),("border", "1px solid #eee"),("border-bottom", "2px solid #00cccc"),]),
                    dict(selector="caption", props=[("caption-side", "bottom")]),
                    dict(selector=".row_heading", props=[('display', 'none')]),
                    dict(selector=".blank.level0", props=[('display', 'none')])]
                    styled = (aggr_df.style.set_table_styles(styles)
                        .applymap(lambda v: 'background-color: %s' % '#cc0d00' if (float(v) >= 90) else('background-color: %s' % '#cc6800' if (float(v) < 90 and float(v) >= 60) else 'background-color: #1e9e26'), subset=["Used Data %"])
                        .applymap(lambda v: 'background-color: %s' % '#e0e0e0' if (v == 'Learning') else('background-color: %s' % '#cc0d00' if (float(v) <= 365) else('background-color: %s' % '#cc6800' if (float(v) > 365 and float(v) <= 1095) else 'background-color: #1e9e26')), subset=["Days To Full"])
                        .applymap(lambda v: 'background-color: %s' % '#cc0d00' if (float(v) >= 5) else('background-color: %s' % '#cc6800' if (float(v) < 5 and float(v) >= 2) else 'background-color: #1e9e26'), subset=["Daily Growth Rate %"]))
                    html_out = styled.render()
                    html_firmatter = f"""
                    <br>
                    <div>
                    <table style="background-color: #605ef5;border-collapse: collapse; border: 1px solid #eee;">
                    <tr><th style="background-color: #605ef5;border;1px solid #eee;">{Cluster_names[i]}</th></tr>
                    {html_out}
                    </table>
                    </div>
                    <br>
                    """
                    html += html_firmatter
                htmlbody = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                    <title>Capacity Report </title>             
                </head>
                <body>
                <br>
                <br>
                <p style="margin: 20px;">Hi All,<br><br>Below is utilization & allocation data of Storage Aggregates collected today at 11:50 AM</p>
                <br>
                <p style="margin: 20px;">Data collected on:  {date}</p>
                  <H4 style='color : #464A46;font-size : 16px;padding-left: 20px;'>Legend </H4>
                  <table style='width:auto;padding-left: 20px;word-break: keep-all;border;1px solid #eee;'>
                      <tr>
                          <td bgcolor=#cc0d00>Red</td>
                          <td style='background-color: white;'>Critical</td>
                          <td bgcolor=#cc6800>Amber</td>
                          <td style='background-color: white;'>Warnings</td>
                          <td bgcolor=#1e9e26>Green</td>
                          <td style='background-color: white;'>OK</td>
                      </tr>
                  </table>
                <br>
                <div style="margin: 20px;">
                {html}
                </div>
                </body>
                """
                with open('./styled_test.html', 'w')as f:
                    f.write(htmlbody)
                #sendmail(htmlbody)
            else:
                print("Not Connect to OCUM")


if __name__ == "__main__":
  main()
