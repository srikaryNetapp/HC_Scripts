"""
###############################################################################################################################
#                                                         
#                                                           Infrastructure Health Check Report                  
#   This script is part of a 4 part script to perform Health check of the infrastructure components(Storage, Compute, Network, Applications)
#   This Script is a subscript for storage script and deals with the Storagegrid. The script should be imported to the infra_main.py script and  then
#   storgrid.storagegrid_data(grid) function should be called from the Storage script.
# 
#                                              This is and NetApp Internal script                                                   
###############################################################################################################################
"""
# Import Dependencies
import json
import datetime
from urllib3 import disable_warnings
import requests

# disable unsecure HTTP request warning as we dont have the self signed certificate implemented
disable_warnings()

#   Function to fetch credentials


def api_auth(cluster):
    """
    Function to fetch credentials
    usage:  api_auth(<cluster IP/ FQDN>)
    """
    credential_path = "./secrets/u_storagegrid_cred.json"
    credentials = {}
    cred = {}
    try:
        with open(credential_path) as f:
            credentials = json.load(f)
        try:
            cred = (credentials[cluster])
        except:
            print(
                "Incorrect formatting in credentials file or incorrect cluster IP specified in site file")
    except:
        print("Credentials file does not exist, please check documentation to store the credentials in secrets folder")
    header = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'accept': "application/json",
        'Cookie': 'GridAuthorization=2e81a9b4-a536-487e-8aff-d2a728dcd32d; Locale=en-US'
    }
    url = f"https://{cluster}/api/v3/authorize"
    payload = json.dumps(cred)
    response = requests.request(
        "POST", url, headers=header, data=payload, verify=False)
    access_token = (response.json())['data']
    return access_token

#   Function to make get call


def get_api_call(cluster, res_path, fields):
    """

    Function to make get call

    Usage: get_api_call(<cluster IP/ FQDN>, <Resource Path>, Fields)

    """
    token = api_auth(cluster)
    auth = f'Bearer {token}'
    header = {
        'Authorization': auth,
        'content-type': "application/json",
        'cache-control': "no-cache",
        'accept': "application/json"
    }
    url = f"https://{cluster}/api/v3/"
    try:
        response = requests.request(
            "GET", (url + res_path + fields), headers=header, verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as errh:
        raise SystemExit(errh)

    except requests.exceptions.ConnectionError as errc:
        raise SystemExit(errc)

    except requests.exceptions.RequestException as erre:
        raise SystemExit(erre)

#   Function to get Grid version


def get_grid_version(cluster):
    """

    Function to get the STORAGEGRID Version

    Usage: get_grid_version(<cluster IP/ FQDN>)
    """
    res_path = "grid/config/product-version"
    fields = ""
    response = get_api_call(cluster, res_path, fields)
    version = response['data']['productVersion']
    version = version.split('-')[0]
    return version

#   Function to get grid and node status


def get_grid_node_status(cluster):
    """


    Function to get grid and node status

    Usage: get_grid_node_status(<cluster IP/ FQDN>)

    """
    res_path = "grid/health/topology"
    fields = "?depth=node"
    response = get_api_call(cluster, res_path, fields)
    grid_name = response['data']['name']
    grid_state = response['data']['state']
    grid_severity = response['data']['severity']
    site_count = len(response['data']['children'])
    node_status = {}
    node_names = []
    for i in range(0, site_count):
        node_count = len(response['data']['children'][i]['children'])
        for j in range(0, node_count):
            node_name = response['data']['children'][i]['children'][j]['name']
            node_names += [node_name]
            node_state = response['data']['children'][i]['children'][j]['state']
            node_serverity = response['data']['children'][i]['children'][j]['severity']
            node_status[node_name] = {
                'node_state': node_state, 'node_serverity': node_serverity}
    return (grid_name, grid_state, grid_severity, node_names, node_status)

#   Function to get Grid Utilisation


def get_grid_usage(cluster):
    """
    Function to get Grid Utilisation

    Usage: get_grid_usage(<cluster IP/ FQDN>)

    """
    res_path = "grid/metric-query"
    fields = "?query=storagegrid_storage_utilization_total_space_bytes"
    response = get_api_call(cluster, res_path, fields)
    storage_node_count = len(response['data']['result'])
    total_capacity = 0
    usable_capacity = 0
    for i in range(0, storage_node_count):
        total_capacity += int(response['data']['result'][i]['value'][1])
    total_capacity_TiB = ((((total_capacity)/1000)/1000)/1000)/1000
    total_capacity_TiB = round(total_capacity_TiB, 1)
    fields = "?query=storagegrid_storage_utilization_usable_space_bytes"
    response = get_api_call(cluster, res_path, fields)
    for i in range(0, storage_node_count):
        usable_capacity += int(response['data']['result'][i]['value'][1])
    usable_capacity_TiB = ((((usable_capacity)/1000)/1000)/1000)/1000
    usable_capacity_TiB = round(usable_capacity_TiB, 1)
    used_capacity = total_capacity-usable_capacity
    used_capacity_TiB = ((((used_capacity)/1000)/1000)/1000)/1000
    used_capacity_TiB = round(used_capacity_TiB, 1)
    percent_used = round(
        ((total_capacity-usable_capacity)/total_capacity)*100, 0)
    if (round(used_capacity_TiB, 1) > 0.0):
        grid_unit = "TiB"
        return (used_capacity_TiB, percent_used, grid_unit)
    else:
        used_capacity_GiB = (((used_capacity)/1000)/1000)/1000
        used_capacity_GiB = round(used_capacity_GiB, 1)
        grid_unit = "GiB"
        return (used_capacity_GiB, percent_used, grid_unit)

#   Function to get Tenant Utilisation


def get_tenant_usage(cluster):
    """

    Function to get Tenant Utilisation

    Usage: get_tenant_usage(<cluster IP/ FQDN>)
    """
    res_path = "grid/accounts"
    fields = ""
    response = get_api_call(cluster, res_path, fields)
    tenant_count = len(response['data'])
    tenant_ids = []
    tenant_name = []
    tenant_quotas = []
    tenant_usages = []
    tenant_usage_percent = []
    for i in range(0, tenant_count):
        tenant_ids += [response['data'][i]['id']]
        tenant_name += [response['data'][i]['name']]
    for id in tenant_ids:
        res_path = f"grid/accounts/{id}/usage"
        response = get_api_call(cluster, res_path, fields)
        tenant_usage = response['data']['dataBytes']
        tenant_usages += [int(int(tenant_usage)/1000000000000)]
        res_path = f"grid/accounts/{id}"
        response = get_api_call(cluster, res_path, fields)
        tenant_quota = response['data']['policy']['quotaObjectBytes']
        if tenant_quota != None:
            tenant_quotas += [int(int(tenant_quota)/1000000000000)]
            tenant_usage_percent += [int((tenant_usage/tenant_quota)*100)]
        else:
            tenant_quotas += ["None"]
            tenant_usage_percent += ["NA"]
    return (tenant_name, tenant_quotas, tenant_usages, tenant_usage_percent)

#   Function to get Alerts


def get_alerts(cluster):
    """

    Function to get Alerts

    Usage: get_alerts(<cluster IP/ FQDN>)
    """
    res_path = "grid/alarms"
    fields = "?includeAcknowledged=false"
    response = get_api_call(cluster, res_path, fields)
    attributeCode = []
    severity = []
    status = []
    alert_count = len(response['data'])
    for i in range(0, alert_count):
        attributeCode += [response['data'][i]['attributeCode']]
        severity += [response['data'][i]['severity']]
        #status += [response['data'][i]['status']]
    return (attributeCode, severity)

#   Function to format storagegrid Report data


def storagegrid_data(cluster):
    """

    Function to format storagegrid Report data

    Usage:

    """
    grid_name, grid_state, grid_severity, node_names, node_status = get_grid_node_status(
        cluster)
    version = get_grid_version(cluster)
    used_capacity_TiB, percent_used, grid_unit = get_grid_usage(
        cluster)
    tenant_name, tenant_quotas, tenant_usages, tenant_usage_percent = get_tenant_usage(
        cluster)
    alertname, severity = get_alerts(cluster)
    #   Format Grid status
    if grid_severity == "normal":
        grid_status = f"""<TD bgcolor=#33FFBB>Grid State: {grid_state}<br>Grid Severity: {grid_severity}</TD>"""
    elif grid_severity == "critical":
        grid_status = f"""<TD bgcolor=#FA8074>Grid State: {grid_state}<br>Grid Severity: {grid_severity}</TD>"""
    else:
        grid_status = f"""<TD bgcolor=#EFF613>Grid State: {grid_state}<br>Grid Severity: {grid_severity}</TD>"""

    #   Format Node status
    node_stat_dt = ""
    for node in node_names:
        if node_status[node]['node_serverity'] == "normal":
            node_stat_dt += f"<TR><TD bgcolor=#33FFBB>{node}: State: {node_status[node]['node_state']} Severity: {node_status[node]['node_serverity']}</TD></TR>"
        elif node_status[node]['node_serverity'] == "critical":
            node_stat_dt += f"<TR><TD bgcolor=#FA8074>{node}: State: {node_status[node]['node_state']} Severity: {node_status[node]['node_serverity']}</TD></TR>"
        else:
            node_stat_dt += f"<TR><TD bgcolor=#EFF613>{node}: State: {node_status[node]['node_state']} Severity: {node_status[node]['node_serverity']}</TD></TR>"
    node_stat = f"""
    <TD>
        <table>
            {node_stat_dt}
        </table>
    </TD>
    """

    #   Format Grid Utilisation Data
    grid_utilisation_dt = "<TR><TH>Utilisation%</TH><TH>Utilisation</TH></TR>"
    if percent_used >= 90:
        grid_utilisation_dt += f"""<TR><TD bgcolor=#FA8074> {percent_used}% </TD><TD bgcolor=#FA8074>{used_capacity_TiB}{grid_unit}</TD></TR>"""
    elif percent_used >= 80:
        grid_utilisation_dt += f"""<TR><TD bgcolor=#EFF613>{percent_used}% </TD><TD bgcolor=#EFF613> {used_capacity_TiB}{grid_unit}</TD></TR>"""
    else:
        grid_utilisation_dt += f"""<TR><TD bgcolor=#33FFBB>{percent_used}% </TD><TD bgcolor=#33FFBB> {used_capacity_TiB}{grid_unit}</TD></TR>"""
    #   Format Tenant Utilisation Data
    grid_utilisation = f"""
    <TD>
        <table>
            {grid_utilisation_dt}
        </table>
    </TD>
    """
    tenant_utilisation_dt = "<TR><TH>Tenant Name</TH><TH> Tenant Quota</TH><TH> Tenant Usage</TH><TH> Tenant Usage%</TH><TR>"
    for i in range(0, len(tenant_name)):
        if (isinstance(tenant_usage_percent[i],int)):
            if (tenant_usage_percent[i] < 90):
                tenant_utilisation_dt += f"<TR><TD>{tenant_name[i]}</TD><TD> {tenant_quotas[i]} TiB </TD><TD> {tenant_usages[i]}TiB </TD><TD> {tenant_usage_percent[i]} %</TD></TR>"
            else:
                tenant_utilisation_dt += f"<TR><TD  bgcolor=#FA8074>{tenant_name[i]}</TD><TD bgcolor=#FA8074> {tenant_quotas[i]}TiB </TD><TD bgcolor=#FA8074> {tenant_usages[i]}TiB </TD><TD bgcolor=#FA8074> {tenant_usage_percent[i]} %</TD></TR>"
        else:
            tenant_utilisation_dt += f"<TR><TD  bgcolor=#FA8074>{tenant_name[i]}</TD><TD bgcolor=#FA8074> {tenant_quotas[i]}TiB </TD><TD bgcolor=#FA8074> {tenant_usages[i]}TiB </TD><TD bgcolor=#FA8074> {tenant_usage_percent[i]} %</TD></TR>"
    tenant_utilisation = f"""
    <TD>
        <table>
            {tenant_utilisation_dt}
        </table>
    </TD>
    """
    if len(alertname):
        active_alerts_dt = ""
        for i in range(0, len(alertname)):
            if (severity == "critical" or severity == "major"):
                active_alerts_dt += f"<TR><TD bgcolor=#FA8074>{alertname[i]} || Severity: {severity[i]} </TD></TR>"
            else:
                active_alerts_dt += f"<TR><TD bgcolor=#EFF613>{alertname[i]} || Severity: {severity[i]} </TD></TR>"
        active_alerts = f"""
        <TD>
            <table>
                {active_alerts_dt}
            </table>
        </TD>
    """
    else:
        active_alerts = "<TD bgcolor=#33FFBB> No Active Alerts on Grid </TD>"

    storagegrid_dt = f"""
    <TR>
        <TD> {grid_name} </TD>
        <TD> {version} </TD>
        {grid_status}
        {node_stat}
        {grid_utilisation}
        {tenant_utilisation}
        {active_alerts}
    </TR>
    """
    return(storagegrid_dt)


if __name__ == '__main__':

    grid = "172.27.14.50"
    print(storagegrid_data(grid))