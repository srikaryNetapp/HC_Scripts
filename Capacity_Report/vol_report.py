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
import openpyxl
import time

_file_path = 'volume_data.xlsx'

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

    def get_sql_data(self, query):
        self.cursor.execute(query)
        records = self.cursor.fetchall()
        return records



def main():
    config = ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__),'Utils/.config.ini'))
    cls_query = ("SELECT objid as id, name FROM netapp_model_view.cluster;")
    ocum_list = config['AIQUM']['aiqum'].split(',')
    html = ""
    date = datetime.date.today()
    tme = time.localtime()
    current_clock = time.strftime("%I:%M %p",tme)
    date = datetime.date.today()
    writer = pd.ExcelWriter(_file_path,engine='openpyxl')
    for ocum in ocum_list:
        with MySqlCon(ocum,config) as con:
            if not con is None:
                clusters = pd.DataFrame(con.get_sql_data(cls_query))
                cluster_ids = list(clusters['id'])
                cluster_names = list(clusters['name'])
                
                for i in range(0,len(cluster_ids)):
                    vol_query = f"""
                    SELECT volumeName as Volume,
                    ROUND(totalDataCapacity/1099511627776,1) as 'Total Capacity (TB)',
                    ROUND(usedDataCapacity/1099511627776,1) as 'Used Capacity (TB)',
                    ROUND(availableDataCapacity/1099511627776,1) as 'Available Capacity (TB)',
                    CASE
                    WHEN logicalSpaceUsedCapacity IS NULL THEN 0
                    ELSE ROUND(logicalSpaceUsedCapacity/1099511627776,1)
                    END as 'Logical Used Capacity (TB)',
                    usedData as 'Used Data %',
                    CASE
                    WHEN availableData IS NULL and usedData = 0 THEN 100
                    ELSE availableData
                    END AS 'Available Data %',
                    CASE
                    WHEN autoGrow = 0 THEN 'Disabled'
                    WHEN autoGrow = 1 THEN 'Enabled'
                    END as 'Autogrow',
                    ROUND(autoSizeMaximumSize/1099511627776,1) as 'Max Autogrow Size (TB)',
                    CASE
                    WHEN ROUND((logicalSpaceUsedCapacity/totalDataCapacity)*100,1) IS NULL THEN 0
                    ELSE ROUND((logicalSpaceUsedCapacity/totalDataCapacity)*100,1)
                    END as 'Logical Capacity Used %',
                    CASE
                    when dailyGrowthRate >= 0 THEN ROUND(dailyGrowthRate,1)
                    when dailyGrowthRate < 0 THEN 0
                    END AS 'Daily Growth Rate %*',
                    CASE
                    when daysToFull IS NULL THEN 'Learning'
                    when daysToFull <= 1000 THEN daysToFull
                    when daysToFull > 1000 THEN '>1000'
                    ELSE ROUND(daysToFull,0)
                    END AS 'Days To Full'
                    FROM ocum.volumecapacityutilizationview
                    inner join netapp_model_view.volume on ocum.volumecapacityutilizationview.volumeId = netapp_model_view.volume.objid
                    where ocum.volumecapacityutilizationview.clusterId = {cluster_ids[i]};
                    """
                    vol_df = pd.DataFrame(con.get_sql_data(vol_query))
                    #print(vol_df)
                    # if (i == 0):
                    #     writer = pd.ExcelWriter(_file_path,engine='openpyxl', mode='w')
                    #     vol_df.to_excel(writer, sheet_name=f"{cluster_ids[i]}",index=False)
                    # else:
                    #     writer = pd.ExcelWriter(_file_path,engine='openpyxl', mode='a')
                    #     writer.book = openpyxl.load_workbook(_file_path)
                    vol_df = vol_df[~vol_df['Volume'].str.contains("vol0")]
                    vol_df = vol_df[~vol_df['Volume'].str.contains("root")]
                    vol_df = vol_df[~vol_df['Volume'].str.contains("MDV_CRS")]
                    vol_df.to_excel(writer, sheet_name=f"{cluster_names[i]}",index=False)
                        
                    vol_df = vol_df.loc[:, ['Volume',"Total Capacity (TB)", "Used Capacity (TB)",'Available Capacity (TB)',"Logical Used Capacity (TB)", "Used Data %", "Logical Capacity Used %", 'Available Data %', "Autogrow", "Max Autogrow Size (TB)", "Daily Growth Rate %*",'Days To Full']]
                    list_not_needed_volumes = ["tfavsv303_tfa_vcd_nfs_backup_t0200_sl_03", "tfavsv303_tfa_vcd_nfs_backup_t0200_sl_06", "tfavsv303_tfa_vcd_nfs_backup_t0200_sl_07"]
                    for elem in list_not_needed_volumes:
                        vol_df = vol_df[~vol_df['Volume'].str.contains(elem)]
                        
                    vol_df = vol_df[vol_df['Used Data %'] >= 60]
                    vol_df.sort_values(by=['Days To Full'], inplace=True)
                    vol_df['Daily Growth Rate %*'] = vol_df['Daily Growth Rate %*'].astype(str)
                    vol_df['Available Data %'] = vol_df['Available Data %'].astype(
                        str)
                    vol_df['Available Capacity (TB)'] = vol_df['Available Capacity (TB)'].astype(
                        str)
                    vol_df['Used Data %'] = vol_df['Used Data %'].astype(
                        str)
                    vol_df['Used Capacity (TB)'] = vol_df['Used Capacity (TB)'].astype(
                        str)
                    vol_df['Total Capacity (TB)'] = vol_df['Total Capacity (TB)'].astype(str)
                    vol_df["Logical Capacity Used %"] = vol_df["Logical Capacity Used %"].astype(str)
                    vol_df["Logical Used Capacity (TB)"] = vol_df["Logical Used Capacity (TB)"].astype(str)
                    vol_df["Max Autogrow Size (TB)"] = vol_df["Max Autogrow Size (TB)"].astype(str)
                    styles = [dict(selector="tr:hover",props=[("background", "#bebeda"), ("width", "fit-content")]),dict(selector="th", props=[("color", "#e6e6e6"),("border", "1px solid #eee"),("padding", "6px 17px"),("border-collapse", "collapse"),("background", "#605ef5"),("text-transform", "uppercase"),("font-size", "12px")]),
                    dict(selector="td", props=[("color", "black"),("width", "fit-content"),("border", "1px solid #eee"),("padding", "6px 17px"),("border-collapse", "collapse"),("font-size", "12px"),("font-weight", "990")]),
                    dict(selector="table", props=[("table-layout", "auto"),("width", "fit-content"),("hight", "fit-content"),("font-family", 'Arial'),("border-collapse", "collapse"),("border", "1px solid #eee"),("border-bottom", "2px solid #00cccc")]),
                    dict(selector="caption", props=[("caption-side", "bottom")]),
                    dict(selector=".row_heading", props=[('display', 'none')]),
                    dict(selector=".blank.level0", props=[('display', 'none')])]
                    styles = [dict(selector="tr:hover",props=[("background", "#bebeda"), ("width", "fit-content")]),dict(selector="th", props=[("padding", "5px 12px"),("color", "#e6e6e6"),("border", "1px solid #eee"),("border-collapse", "collapse"),("background", "#605ef5"),("text-transform", "uppercase"),("font-size", "10px")]),
                    dict(selector="td", props=[("text-align", "center"),("color", "black"),("width", "fit-content"),("border", "1px solid #eee"),("border-collapse", "collapse"),("font-size", "12px"),("font-weight", "990"), ("padding", "5px 12px")]),
                    dict(selector="table", props=[("table-layout", "auto"),("width", "fit-content"),("hight", "fit-content"),("font-family", 'Arial'),("border-collapse", "collapse"),("border", "1px solid #eee"),("border-bottom", "2px solid #00cccc"),]),
                    dict(selector="caption", props=[("caption-side", "bottom")]),
                    dict(selector=".row_heading", props=[('display', 'none')]),
                    dict(selector=".blank.level0", props=[('display', 'none')])]
                    styled = (vol_df.style.set_table_styles(styles)
                        .applymap(lambda v: 'background-color: %s' % '#cc0d00' if (float(v) >= 75) else('background-color: %s' % '#cc6800' if (float(v) < 75 and float(v) >= 65) else 'background-color: #1e9e26'), subset=["Used Data %"])
                        .applymap(lambda v: 'background-color: %s' % '#e0e0e0' if (v == 'Learning') else('background-color: %s' % '#1e9e26' if(v == '>1000') else('background-color: %s' % '#cc0d00' if (float(v) <= 365) else('background-color: %s' % '#cc6800' if (float(v) > 365 and float(v) <= 1095) else 'background-color: #1e9e26'))), subset=["Days To Full"])
                        .applymap(lambda v: 'background-color: %s' % '#cc0d00' if (float(v) >= 5) else('background-color: %s' % '#cc6800' if (float(v) < 5 and float(v) >= 2) else 'background-color: #1e9e26'), subset=["Daily Growth Rate %*"]))
                    html_out = styled.hide_index().render()
                    html_firmatter = f"""
                    <br>
                    <div>
                    <table>
                    <tr>
                    <th style="text-align: left;width:fit-content;text-transform: uppercase;color: black;background-color: #605ef5;border;1px solid #eee;font-size;10px;">{cluster_names[i]}</th>
                    </tr>
                    <tr>
                    <td>{html_out}</td>
                    </tr>
                    </table>
                    </div>
                    <br>
                    """
                    html += html_firmatter
                writer.save()
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
                <p style="margin: 20px;">Hi All,<br><br>Below is utilization & allocation data of Storage Volumes collected today at {current_clock} AEST</p>
                <p style="margin: 20px;">Below table shows data for volumes above 60% utilisation. For raw data please find attached excel sheet</p>
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
# if __name__ == '__main__':
#     main()