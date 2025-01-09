import mysql.connector
from mysql.connector import Error
import pandas as pd
import datetime
import time
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
# def send_mail(htmlbody):
#     msg = MIMEMultipart('alternative')
#     msg['Subject'] = "Interactive Capacity Report - All Aggregates\n"
#     msg['From'] = "nmsintppeaum01@nmsintsmtprelay.netapp.com"
#     msg['To'] = "kprathyu@netapp.com;dhananjay.kumar@netapp.com"
#     msg_content = MIMEText(htmlbody, "html")
#     msg.attach(msg_content)
#     s = smtplib.SMTP('172.27.96.27','25') #, '587')
#     #s.login('dhananjaypossible@gmail.com', '9mpG6OhVYk0UbWd5')
#     s.sendmail("dhananjay.kumar@netapp.com",
#                "dhananjay.kumar@netapp.com", msg.as_string())
#     s.quit()

def main():

    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__),'C:\\Capacity_Report\\utils\\.config.ini'))
    cls_query = ("SELECT objid as id, name FROM netapp_model_view.cluster;")
    ocum_list = config['AIQUM']['aiqum'].split(',')
    html = ""
    date = datetime.date.today()
    tme = time.localtime()
    current_clock = time.strftime("%I:%M %p",tme)
    for ocum in ocum_list:
        with MySqlCon(ocum,config) as con:
            if not con is None:
                #print("Connect to OCUM")
                clusters = pd.DataFrame(con.get_clusters(cls_query))
                cluster_ids = list(clusters['id'])
                Cluster_names = list(clusters['name'])
                for i in range(0,len(cluster_ids)):
                    aggr_query = f"""
                    SELECT aggrName as Aggregate,ROUND(totalDataCapacity/1099511627776,1) as 'Total Data Capacity (TB)',ROUND(usedDataCapacity/1099511627776,1) as 'Used Data Capacity (TB)', ROUND(availableDataCapacity/1099511627776,1) as 'Available Data Capacity (TB)', usedDataCapacityPercentage as 'Used Data %',
                    CASE
                    WHEN availableDataCapacityPercentage IS NULL and usedDataCapacityPercentage = 0 THEN 100
                    ELSE availableDataCapacityPercentage
                    END AS 'Available Data %',
                    CASE
                    when dailyGrowthRate >= 0 THEN ROUND(dailyGrowthRate,1)
                    when dailyGrowthRate < 0 THEN 0
                    END AS 'Daily Growth Rate %',
                    CASE
                    when daysToFull IS NULL THEN 'Learning'
                    when daysToFull <= 1000 THEN daysToFull
                    when daysToFull > 1000 THEN '>1000'
                    ELSE ROUND(daysToFull,0)
                    END AS 'Days To Full'
                    FROM ocum.aggregatecapacityutilizationview where clusterId = {cluster_ids[i]} and aggrName NOT LIke "%root%";
                    """
                    aggr_df = pd.DataFrame(con.get_clusters(aggr_query))
                    aggr_df = aggr_df.loc[:, ['Aggregate', "Total Data Capacity (TB)", "Used Data Capacity (TB)", 'Available Data Capacity (TB)', "Used Data %", 'Available Data %', "Daily Growth Rate %",
                                       'Days To Full']]
                    aggr_df = aggr_df[~aggr_df['Aggregate'].str.contains("aggr00")]
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
                    styles = [dict(selector="tr:hover",props=[("background", "#bebeda"), ("width", "fit-content")]),dict(selector="th", props=[("padding", "5px 12px"),("color", "#e6e6e6"),("border", "1px solid #eee"),("border-collapse", "collapse"),("background", "#605ef5"),("text-transform", "uppercase"),("font-size", "10px")]),
                    dict(selector="td", props=[("text-align", "center"),("color", "black"),("width", "fit-content"),("border", "1px solid #eee"),("border-collapse", "collapse"),("font-size", "12px"),("font-weight", "990"), ("padding", "5px 12px")]),
                    dict(selector="table", props=[("table-layout", "auto"),("width", "fit-content"),("hight", "fit-content"),("font-family", 'Arial'),("border-collapse", "collapse"),("border", "1px solid #eee"),("border-bottom", "2px solid #00cccc"),]),
                    dict(selector="caption", props=[("caption-side", "bottom")]),
                    dict(selector=".row_heading", props=[('display', 'none')]),
                    dict(selector=".blank.level0", props=[('display', 'none')])]
                    styled = (aggr_df.style.set_table_styles(styles)
                        .applymap(lambda v: 'background-color: %s' % '#cc0d00' if (float(v) >= 75) else('background-color: %s' % '#cc6800' if (float(v) < 75 and float(v) >= 65) else 'background-color: #1e9e26'), subset=["Used Data %"])
                        .applymap(lambda v: 'background-color: %s' % '#e0e0e0' if (v == 'Learning') else('background-color: %s' % '#1e9e26' if(v == '>1000') else('background-color: %s' % '#cc0d00' if (float(v) <= 365) else('background-color: %s' % '#cc6800' if (float(v) > 365 and float(v) <= 1095) else 'background-color: #1e9e26'))), subset=["Days To Full"])
                        .applymap(lambda v: 'background-color: %s' % '#cc0d00' if (float(v) >= 5) else('background-color: %s' % '#cc6800' if (float(v) < 5 and float(v) >= 2) else 'background-color: #1e9e26'), subset=["Daily Growth Rate %"]))
                    html_out = styled.hide_index().render()
                    html_firmatter = f"""
                    <br>
                    <div>
                    <table>
                    <tr>
                    <th style="text-align: left;width:fit-content;text-transform: uppercase;color: black;background-color: #605ef5;border;1px solid #eee;font-size;10px;">{Cluster_names[i]}</th>
                    </tr>
                    <tr>
                    <td>{html_out}</td>
                    </tr>
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
                <p style="margin: 20px;">Hi All,<br><br>Below is utilization & allocation data of Storage Aggregates collected today at {current_clock} AEST</p>
                <p style="margin: 20px;">Data collected on:  {date}</p>
                <div style="margin: 20px;">
                  <H4 style='color : #464A46;font-size : 16px;'>Legend </H4>
                  <table style='width:auto;word-break: keep-all;border;1px solid #eee;'>
                      <tr>
                          <td bgcolor=#cc0d00>Red</td>
                          <td style='background-color: white;'>Critical</td>
                          <td bgcolor=#cc6800>Amber</td>
                          <td style='background-color: white;'>Warnings</td>
                          <td bgcolor=#1e9e26>Green</td>
                          <td style='background-color: white;'>OK</td>
                      </tr>
                  </table>
                </div>
                <div style="margin: 20px;">
                {html}
                </div>
                </body>
                """
                with open('./styled_test.html', 'w')as f:
                    f.write(htmlbody)
                #send_mail(htmlbody)
                return htmlbody
            else:
                print("Not Connect to OCUM")

print(main())
# if __name__ == "__main__":
#   main()
