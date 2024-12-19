"""

Fetch Solidfire Details

"""
import pandas as pd
import json
import requests
import urllib3
from itertools import * 
from datetime import datetime, timedelta
import os
from configparser import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
from socket import *
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

""" Variable Configuration From Utils Config File"""
result = {'sfcluster_info':[],'sfcluster_capacity':[],'sfcluster_threshold':[],'sfdeleted_volumes':[],'sfcluster_alerts':[],'clusterError_info': []}


# with open('./solidfire_input.json') as f:
#     clusters_input = json.load(f)
# sf_cluster_list = clusters_input["SOLIDFIRE"]
# print(sf_cluster_list)

""" Logger Configuration """

log_path = os.path.join(os.path.dirname(__file__),'../logs')
if not os.path.exists(log_path):
    os.makedirs(log_path)
log = (os.path.join(log_path,'solidfire_hc.log'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s : %(name)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
log_handler = RotatingFileHandler(log, maxBytes=500000, backupCount=3)
log_handler.setLevel(logging.ERROR)
log_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.addHandler(stream_handler)

def get_sfcluster_info(client):
    error= pd.DataFrame()
    columns = ['Cluster_Name','Cluster_Version','Node_Count']
    df_cluster_info = pd.DataFrame(columns=columns)

    resource_path = 'method=GetClusterInfo'
    rc, cluster_info = client.get(resource_path)

    if (rc == 200 and cluster_info):
        df_cluster_info.loc[0,'Cluster_Name'] = cluster_info['result']['clusterInfo']['name']

        resource_path = 'method=GetClusterVersionInfo'
        rc, cluster_info = client.get(resource_path)
        df_cluster_info.loc[0,'Cluster_Version'] = cluster_info['result']['clusterVersion']

        resource_path = 'method=ListAllNodes'
        rc, cluster_info = client.get(resource_path)
        nodes = cluster_info['result']['nodes']
        df_cluster_info.loc[0,'Node_Count'] = str(len(nodes))

    else:
        error = pd.DataFrame({'Cluster': client.address, 'Error': cluster_info}, index=[0])
        error= error.astype({'Error' : 'str'})

    return(df_cluster_info, error)

def get_sfcluster_capacity(client):
    
    error= pd.DataFrame()
    columns = ['Cluster_Name','ProvisionedSpace(Gb)','Percent_Provisioned','MaxUsableMetadataSpace(Gb)','UsedMetadataSpace(Gb)','Percent_Metadata_used','MaxUsableSpace(Gb)','UsedSpace(Gb)','Percent_Space_Used']
    df_cluster_capacity = pd.DataFrame(columns=columns)
    max_provisionable = 0

    resource_path = 'method=GetClusterInfo'
    rc, cluster_info = client.get(resource_path)
    if (rc == 200 and cluster_info):
        cluster_name = cluster_info['result']['clusterInfo']['name']
        resource_path = 'method=GetClusterCapacity'
        rc, cluster_capacity = client.get(resource_path)
        if (rc == 200 and cluster_capacity):
            df_cluster_capacity.loc[0,'Cluster_Name'] = cluster_name
            max_provisionable = round(int(cluster_capacity['result']['clusterCapacity']['maxOverProvisionableSpace'])/(1000000000),1)
            df_cluster_capacity.loc[0,'ProvisionedSpace(Gb)'] = round(int(cluster_capacity['result']['clusterCapacity']['provisionedSpace'])/(1000000000),1)
            df_cluster_capacity.loc[0,'Percent_Provisioned'] = round((df_cluster_capacity.loc[0,'ProvisionedSpace(Gb)']/max_provisionable)*100,0)
            df_cluster_capacity.loc[0,'MaxUsableMetadataSpace(Gb)'] = round(int(cluster_capacity['result']['clusterCapacity']['maxUsedMetadataSpace'])/(1000000000),1)
            df_cluster_capacity.loc[0,'UsedMetadataSpace(Gb)'] = round(int(cluster_capacity['result']['clusterCapacity']['usedMetadataSpace'])/(1000000000),1)
            df_cluster_capacity.loc[0,'Percent_Metadata_used'] = round((df_cluster_capacity.loc[0,'UsedMetadataSpace(Gb)']/df_cluster_capacity.loc[0,'MaxUsableMetadataSpace(Gb)'])*100,0)
            df_cluster_capacity.loc[0,'MaxUsableSpace(Gb)'] = round(int(cluster_capacity['result']['clusterCapacity']['maxUsedSpace'])/(1000000000),1)
            df_cluster_capacity.loc[0,'UsedSpace(Gb)'] = round(int(cluster_capacity['result']['clusterCapacity']['usedSpace'])/(1000000000),1)
            df_cluster_capacity.loc[0,'Percent_Space_Used'] = round((df_cluster_capacity.loc[0,'UsedSpace(Gb)']/df_cluster_capacity.loc[0,'MaxUsableSpace(Gb)'])*100,0)
            df_cluster_capacity['ProvisionedSpace(Gb)'] = df_cluster_capacity['ProvisionedSpace(Gb)'].map(str)
            df_cluster_capacity['Percent_Provisioned'] = df_cluster_capacity['Percent_Provisioned'].map(str)
            df_cluster_capacity['MaxUsableMetadataSpace(Gb)'] = df_cluster_capacity['MaxUsableMetadataSpace(Gb)'].map(str)
            df_cluster_capacity['UsedMetadataSpace(Gb)'] = df_cluster_capacity['UsedMetadataSpace(Gb)'].map(str)
            df_cluster_capacity['Percent_Metadata_used'] = df_cluster_capacity['Percent_Metadata_used'].map(str)
            df_cluster_capacity['MaxUsableSpace(Gb)'] = df_cluster_capacity['MaxUsableSpace(Gb)'].map(str)
            df_cluster_capacity['UsedSpace(Gb)'] = df_cluster_capacity['UsedSpace(Gb)'].map(str)
            df_cluster_capacity['Percent_Space_Used'] = df_cluster_capacity['Percent_Space_Used'].map(str)
        else:
            error = pd.DataFrame({'Cluster': client.address, 'Error': cluster_capacity}, index=[0])
            error= error.astype({'Error' : 'str'})
    else:
        error = pd.DataFrame({'Cluster': client.address, 'Error': cluster_info}, index=[0])
        error= error.astype({'Error' : 'str'})
    
    return(df_cluster_capacity, error)

def get_sfcluster_threshold(client):
    
    error= pd.DataFrame()
    columns = ['Cluster_Name','blockFullness','fullness','metadataFullness']
    df_cluster_threshold = pd.DataFrame(columns=columns)

    resource_path = 'method=GetClusterInfo'
    rc, cluster_info = client.get(resource_path)
    if (rc == 200 and cluster_info):
        cluster_name = cluster_info['result']['clusterInfo']['name']
        resource_path = 'method=GetClusterFullThreshold'
        rc, cluster_threshold = client.get(resource_path)
        if (rc == 200 and cluster_threshold):
            df_cluster_threshold.loc[0,'Cluster_Name'] = cluster_name
            df_cluster_threshold.loc[0,'blockFullness'] = cluster_threshold['result']['blockFullness']
            df_cluster_threshold.loc[0,'fullness'] = cluster_threshold['result']['fullness']
            df_cluster_threshold.loc[0,'metadataFullness'] = cluster_threshold['result']['metadataFullness']
        else:
            error = pd.DataFrame({'Cluster': client.address, 'Error': cluster_threshold}, index=[0])
            error= error.astype({'Error' : 'str'})
    else:
        error = pd.DataFrame({'Cluster': client.address, 'Error': cluster_info}, index=[0])
        error= error.astype({'Error' : 'str'})
    return(df_cluster_threshold, error)

def get_deleted_volumes(client):

    error= pd.DataFrame()
    columns = ['Cluster_Name','Volume_Name', "status"]
    vol_name = ''
    vol_state = ''
    df_deleted_volumes = pd.DataFrame(columns=columns)

    resource_path = 'method=GetClusterInfo'
    rc, cluster_info = client.get(resource_path)
    if (rc == 200 and cluster_info):
        cluster_name = cluster_info['result']['clusterInfo']['name']
        resource_path = 'method=ListVolumes&volumeStatus=deleted'
        rc, deleted_volumes = client.get(resource_path)
        if (rc == 200 and deleted_volumes):
            for i in range(0,len(deleted_volumes['result']['volumes'])):
                vol_name = deleted_volumes['result']['volumes'][i]['name']
                vol_state = deleted_volumes['result']['volumes'][i]['status']
                df_deleted_volumes = df_deleted_volumes.append({'Cluster_Name': cluster_name, 'Volume_Name': vol_name, 'status': vol_state},ignore_index=True)    
        else:
            error = pd.DataFrame({'Cluster': client.address, 'Error': deleted_volumes}, index=[0])
            error= error.astype({'Error' : 'str'})
    else:
        error = pd.DataFrame({'Cluster': client.address, 'Error': cluster_info}, index=[0])
        error= error.astype({'Error' : 'str'})  

    return(df_deleted_volumes, error)


def get_fscluster_alerts(client):
    error= pd.DataFrame()
    columns = ['Cluster_Name',"clusterFaultID", "code","severity","details"]
    faultid = ''
    fault_code  =''
    severity = ''
    fault_details = ''
    df_cluster_alerts = pd.DataFrame(columns=columns)
    resource_path = 'method=GetClusterInfo'
    rc, cluster_info = client.get(resource_path)
    if (rc == 200 and cluster_info):
        cluster_name = cluster_info['result']['clusterInfo']['name']
        resource_path = 'method=ListClusterFaults&faultTypes=current&bestPractices=true'
        rc, cluster_alerts = client.get(resource_path)
        if (rc == 200 and cluster_alerts):
            for i in range(0,len(cluster_alerts['result']['faults'])):
                faultid = str(cluster_alerts['result']['faults'][i]['clusterFaultID'])
                fault_code = str(cluster_alerts['result']['faults'][i]['code'])
                severity = cluster_alerts['result']['faults'][i]['severity']
                fault_details = cluster_alerts['result']['faults'][i]['details']
                df_cluster_alerts = df_cluster_alerts.append({'Cluster_Name': cluster_name, "clusterFaultID": faultid, "code": fault_code,"severity": severity,"details": fault_details},ignore_index=True)
        else:

            error = pd.DataFrame({'Cluster': client.address, 'Error': df_cluster_alerts}, index=[0])
            error= error.astype({'Error' : 'str'})
    else:
    
        error = pd.DataFrame({'Cluster': client.address, 'Error': cluster_info}, index=[0])
        error= error.astype({'Error' : 'str'})  

    return(df_cluster_alerts, error)    
            



class APIClient:
    """A minimum client for API services"""

    def __init__(self, address: str, username: str, password: str, protocol: str = 'https'):
        """Create an API Client.

        :param address: The hostname or IP address of the Web Services
        :param username: The username for authenticating to web services.
        :param password: The password for authenticating to web services.
        :param port: The TCP port to use for web services. Defaults to 8443.
        :param protocol: Specify the protocol, either 'http' or 'https'. Defaults to https.
        """
        self.address = address
        self.api_user = username
        self.api_password = password
        self.protocol = protocol
        self.base_url = f"{self.protocol}://{self.address}/json-rpc/12.0?"
        self.session = self.create_session(username=self.api_user, password=self.api_password)

    @staticmethod
    def create_session(username: str, password: str, verify_tls: bool = False) -> requests.Session:
        """Create a requests session.

        :param username:
        :param password:
        :param verify_tls:
        :return:

        """
        session = requests.Session()
        session.auth = (username, password)
        session.verify = verify_tls

        return session



    def do_request(self, api_path: str, **request_args):
        """Make an API request

        :param api_path: The path portion of the URL for the request.
        :param request_args: Any additional keyword args supported by the requests module.
        :return:
        """
        response = ""
        rc = ""
        data = ""
        request_args['url'] = self.base_url + api_path
        try:
            response = self.session.request(**request_args)
            response.raise_for_status()
        except Exception as error:
            if isinstance(response, requests.models.Response):
                rc = response.status_code
                try:
                    data = response.json()
                except json.decoder.JSONDecodeError:
                    data = error
            else:
                data = error
        if response:
            rc = response.status_code
            data = response.json()
        return rc,data

    def get(self, api_path: str, **request_args):
        """Make a GET request for the api_path.

        :param api_path:
        :param request_args:
        :return:
        """

        request_args['url'] = self.base_url + api_path
        request_args["method"] = 'get'
        return self.do_request(api_path=api_path, **request_args)

def sf_get_data(sf_cluster_list):
    sfcluster_info = pd.DataFrame()
    sfcluster_capacity = pd.DataFrame()
    sfcluster_threshold = pd.DataFrame()
    sfdeleted_volumes = pd.DataFrame()
    sfcluster_alerts = pd.DataFrame()
    cluster_error= pd.DataFrame()
    with open('./secrets/u_solidfire_creds.json') as f:
        config = json.load(f)
    for sf_cluster in sf_cluster_list:
        print(sf_cluster)
        session_client = APIClient(address=sf_cluster, username=config[sf_cluster]['username'], password=config[sf_cluster]['password'])
        df1,df2 = get_sfcluster_info(session_client)
        if df1 is not None:
            sfcluster_info = sfcluster_info.append(df1)
        if df2 is not None:
            cluster_error = cluster_error.append(df2)
        df1,df2 = get_sfcluster_capacity(session_client)
        if df1 is not None:
            sfcluster_capacity = sfcluster_capacity.append(df1)
        if df2 is not None:
            cluster_error = cluster_error.append(df2)
        df1,df2 = get_sfcluster_threshold(session_client)
        if df1 is not None:
            sfcluster_threshold = sfcluster_threshold.append(df1)
        if df2 is not None:
            cluster_error = cluster_error.append(df2)
        df1,df2 = get_deleted_volumes(session_client)
        if df1 is not None:
            sfdeleted_volumes = sfdeleted_volumes.append(df1)
        if df2 is not None:
            cluster_error = cluster_error.append(df2)
        df1,df2 = get_fscluster_alerts(session_client)
        if df1 is not None:
            sfcluster_alerts = sfcluster_alerts.append(df1)
        if df2 is not None:
            cluster_error = cluster_error.append(df2)
    #print(sfcluster_info,"\n", sfcluster_capacity,"\n",sfcluster_threshold,"\n",sfdeleted_volumes,"\n", sfcluster_alerts,'\n', cluster_error)
    return sfcluster_info, sfcluster_capacity, sfcluster_threshold, sfdeleted_volumes, sfcluster_alerts, cluster_error

def sf_format_data(sf_cluster_list):
    sfcluster_info, sfcluster_capacity, sfcluster_threshold, sfdeleted_volumes, sfcluster_alerts, cluster_error = sf_get_data(sf_cluster_list)
    sfcluster_info_list = [sfcluster_info.to_dict('records')]
    sfcluster_capacity_list = [sfcluster_capacity.to_dict('records')]
    sfcluster_threshold_list = [sfcluster_threshold.to_dict('records')]
    sfdeleted_volumes_list = [sfdeleted_volumes.to_dict('records')]
    sfcluster_alerts_list = [sfcluster_alerts.to_dict('records')]
    cluster_error_list = [cluster_error.to_dict('records')]
    if(sfcluster_info_list):
      for record in sfcluster_info_list:
        for rec in record:
          result['sfcluster_info'].append(rec)
    if(sfcluster_capacity_list):
      for record in sfcluster_capacity_list:
        for rec in record:
          result['sfcluster_capacity'].append(rec)
    if(sfcluster_threshold_list):
      for record in sfcluster_threshold_list:
        for rec in record:
          result['sfcluster_threshold'].append(rec)
    if(sfdeleted_volumes_list):
      for record in sfdeleted_volumes_list:
        for rec in record:
          result['sfdeleted_volumes'].append(rec)
    if(sfcluster_alerts_list):
      for record in sfcluster_alerts_list:
        for rec in record:
          result['sfcluster_alerts'].append(rec)
    if(cluster_error_list):
      for record in cluster_error_list:
        for rec in record:
          result['clusterError_info'].append(rec)
    cluster_info_dt = ""
    cluster_capacity_dt = ""
    cluster_threshold_dt = ""
    cluster_deleted_volumes_dt = ""
    cluster_alerts_dt = ""
    for sfcl in result['sfcluster_info']:
        cluster_info_dt += '<TR><TD>'+ sfcl['Cluster_Name'] + '</TD><TD>'+ sfcl['Cluster_Version'] + '</TD><TD>' + sfcl['Node_Count'] + '</TD></TR>'
    for sfclcap in result['sfcluster_capacity']:
        cluster_capacity_dt += '<TR><TD>'+ sfclcap['Cluster_Name'] + '</TD><TD>'+ sfclcap['ProvisionedSpace(Gb)'] + '</TD><TD>' + sfclcap['Percent_Provisioned'] + '</TD><TD>' + sfclcap['MaxUsableMetadataSpace(Gb)'] + '</TD><TD>' + sfclcap['UsedMetadataSpace(Gb)'] + '</TD><TD>' + sfclcap['Percent_Metadata_used'] + '</TD><TD>' + sfclcap['MaxUsableSpace(Gb)'] + '</TD><TD>' + sfclcap['UsedSpace(Gb)'] + '</TD><TD>' + sfclcap['Percent_Space_Used'] + '</TD></TR>'
    for sfclcap in result['sfcluster_threshold']:
        cluster_threshold_dt += '<TR><TD>'+ sfclcap['Cluster_Name'] + '</TD><TD>'+ sfclcap['blockFullness'] + '</TD><TD>' + sfclcap['fullness'] + '</TD><TD>' + sfclcap['metadataFullness'] + '</TD></TR>'
    for sfclcap in result['sfdeleted_volumes']:
        cluster_deleted_volumes_dt += '<TR><TD>'+ sfclcap['Cluster_Name'] + '</TD><TD>'+ sfclcap['Volume_Name'] + '</TD><TD>' + sfclcap['status'] + '</TD></TR>'
    for sfclcap in result['sfcluster_alerts']:
        cluster_alerts_dt += '<TR><TD>'+ sfclcap['Cluster_Name'] + '</TD><TD>'+ sfclcap['clusterFaultID'] + '</TD><TD>' + sfclcap['code'] + '</TD><TD>' + sfclcap['severity'] + '</TD><TD>' + sfclcap['details'] + '</TD></TR>'
    return (cluster_info_dt, cluster_capacity_dt, cluster_threshold_dt, cluster_deleted_volumes_dt, cluster_alerts_dt)    

def main(sf_cluster_list):
    cluster_info_dt, cluster_capacity_dt, cluster_threshold_dt, cluster_deleted_volumes_dt, cluster_alerts_dt = sf_format_data(sf_cluster_list)
    sf_html_out = f"""
   <div>
   <h3 style='color : #464A46; font-size : 21px' align="" left ""> Solidfire Cluster Info </h3>
   </caption>
       <Table>
           <TR>
               <TH><B> Cluster_Name </B></TH>
               <TH><B> Cluster_Version </B></TH>
               <TH><B> Node_Count </B></TH>
           </TR>
           {cluster_info_dt}
       </Table>
   <h3 style='color : #464A46; font-size : 21px' align="" left ""> Solidfire Cluster Capacity </h3>
   </caption>
       <Table>
           <TR>
               <TH><B> Cluster_Name </B></TH>
               <TH><B> ProvisionedSpace(Gb) </B></TH>
               <TH><B> Percent_Provisioned </B></TH>
               <TH><B> MaxUsableMetadataSpace(Gb) </B></TH>
               <TH><B> UsedMetadataSpace(Gb) </B></TH>
               <TH><B> Percent_Metadata_used </B></TH>
               <TH><B> MaxUsableSpace(Gb) </B></TH>
               <TH><B> UsedSpace(Gb) </B></TH>
               <TH><B> Percent_Space_Used </B></TH>
           </TR>
           {cluster_capacity_dt}
       </Table>
   <h3 style='color : #464A46; font-size : 21px' align="" left ""> Solidfire Cluster Threshold </h3>
   </caption>
       <Table>
           <TR>
               <TH><B> Cluster_Name </B></TH>
               <TH><B> blockFullness </B></TH>
               <TH><B> fullness </B></TH>
               <TH><B> metadataFullness </B></TH>
           </TR>
           {cluster_threshold_dt}
        </Table>
   <h3 style='color : #464A46; font-size : 21px' align="" left ""> Solidfire Deleted Volumes </h3>
   </caption>
       <Table>
           <TR>
               <TH><B> Cluster_Name </B></TH>
               <TH><B> Volume_Name </B></TH>
               <TH><B> status </B></TD>
           </TR>
           {cluster_deleted_volumes_dt}
       </Table>
   <h3 style='color : #464A46; font-size : 21px' align="" left ""> Solidfire Cluster  Alerts </h3>
   </caption>
       <Table>
           <TR>
               <TH><B> Cluster_Name </B></TH>
               <TH><B> clusterFaultID </B></TH>
               <TH><B> code </B></TD>
               <TH><B> severity </B></TH>
               <TH><B> details </B></TH>
           </TR>
           {cluster_alerts_dt}
       </Table>
   </div>  

    """
    return sf_html_out


if __name__ == "__main__":
    solidfire_clusters = ["172.27.96.15","172.27.29.15"]
    print(sf_get_data(solidfire_clusters))
    #html = main()
    # with open('./test.html','w') as f:
    #     f.write(html)