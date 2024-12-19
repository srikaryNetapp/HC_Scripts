"""
###############################################################################################################################
#                                                         
#                                                             Infrastructure Health Check Report                  
#   This script is part of a 6 part script to perform Health check of the infrastructure components(Storage, Compute, Network, Applications)
#   This Script is a subscript for storage script and deals with the eseries Storage. The script should be imported to the infra_main.py script and  then
#   application_check.app_data(url, haproxy_servers, grafana_server, harvest_server, snapcenter_server) function should be called from the Storage script.
# 
#                                              This is and NetApp Internal script                                                   
###############################################################################################################################
"""

# Check Application status
import urllib.request
import paramiko
import json
import http.client
import ssl
import datetime


def alive_check(url):
    """
    Check if the passed URL is alive and reachable
    """
    status_code = urllib.request.urlopen(url).getcode()
    if status_code == 200:
        site_status = "UP"
        return site_status
    else:
        site_status = "DOWN"
        return site_status


def ssh_command_push(server, command):
    """
    Function to send commands over ssh session
    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    server_credentials_path = "./secrets/u_server_secret.json"
    with open(server_credentials_path) as f:
        server_credentials = json.load(f)
    if server in server_credentials:
        server_username = server_credentials[server]["username"]
        server_password = server_credentials[server]["password"]
        ssh.connect(server, username=server_username,
                    password=server_password)
    else:
        error_msg = f"Error: Credentials for {server} not found"
        print(error_msg)
        exit
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
    if ("-j" in command or "json" in command):
        out = ssh_stdout.read()
        err = ssh_stderr.read().decode('utf-8')
        output = json.loads(out)
    else:
        out = ssh_stdout.read()
        err = ssh_stderr.read().decode('utf-8')
        output = out.decode('utf-8').split('\n')
    if (err == ''):
        return output[0]
    else:
        return err


#   Function to authenticate Snap Center


def snapcenter_token_get(snapcenter_server):
    conn = http.client.HTTPSConnection(
        f"{snapcenter_server}", 8144, context=ssl._create_unverified_context())
    payload_path = "./secrets/u_snapcenter.json"
    with open(payload_path) as f:
        payload = f.read()
    headers = {'Content-Type': 'application/json'}
    conn.request(
        "POST", "/api/4.1/auth/login", payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    return (response["response"]["token"])


def snapcenter_job_get(snapcenter_server):
    token = snapcenter_token_get(snapcenter_server)
    conn = http.client.HTTPSConnection(
        f"{snapcenter_server}", 8144, context=ssl._create_unverified_context())

    payload = ''
    headers = {}
    headers['token'] = token

    conn.request("GET", "/api/4.1/jobs?type=backup",
                 payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    return response["response"]


def app_data_table(url, haproxy_servers,  grafana_server, harvest_server, snapcenter_server):

    # For formatting the URL Alive check data
    alive_status = alive_check(url)
    url_down = 0
    if alive_status == "UP":
        url_alive_status = f"""<TD bgcolor=#33FFBB> {alive_status} </TD>"""
    else:
        url_alive_status = f"""<TD bgcolor=#FA8074> {alive_status} </TD>"""

    # For Formatting the Server Service check data
    HA_proxy_status = ""
    for server in haproxy_servers:
        try:
            command = "systemctl status haproxy | grep 'Active:'"
            out = ssh_command_push(server, command).split()
            service_status = out[1] + out[2]
            if service_status == 'active(running)':
                HA_proxy_status += f"""<TR><TD bgcolor=#33FFBB> {server}: {service_status} </TD></TR>"""
            else:
                HA_proxy_status += f"""<TR><TD bgcolor=#FA8074> {server}: {service_status} </TD></TR>"""
        except:
            HA_proxy_status += f"<TD bgcolor=#FA8074> Unable to connect to {server} </TD>"
    HA_service_status = f"""
    <TD>
    <table>
        {HA_proxy_status}
    </table>
    </TD>
    """
    # Grafana service status
    try:
        command = "systemctl status grafana-server | grep 'Active:'"
        out = ssh_command_push(grafana_server, command).split()
        service_status = out[1] + out[2]
        if service_status == 'active(running)':
            grafana_status = f"""<TD bgcolor=#33FFBB> {grafana_server}: {service_status} </TD>"""
        else:
            grafana_status = f"""<TD bgcolor=#FA8074> {grafana_server}: {service_status} </TD>"""
    except:
        grafana_status = f"<TD bgcolor=#FA8074> Unable to connect to {grafana_server} </TD>"
    # Harvest service status
    try:
        command = "systemctl status netapp-harvest | grep 'Active:'"
        out = ssh_command_push(harvest_server, command).split()
        service_status = out[1] + out[2]
        if service_status == 'active(running)':
            harvest_status = f"""<TD bgcolor=#33FFBB> {harvest_server}: {service_status} </TD>"""
        else:
            harvest_status = f"""<TD bgcolor=#FA8074> {harvest_server}: {service_status} </TD>"""
    except:
        harvest_status = f"<TD bgcolor=#FA8074> Unable to connect to {harvest_server} </TD>"
    # Harvest Manager status
    try:
        command = "/opt/netapp-harvest/netapp-manager -status | grep 'RUNNING' | wc -l"
        out = ssh_command_push(harvest_server, command).split()

        service_running_count = int(out[0])
        service_notrunning = 4 - service_running_count
        if service_running_count != 4:
            harvest_manager_status = f"""<TD bgcolor=#FA8074>{service_notrunning} managers not running </TD>"""
        else:
            harvest_manager_status = f"""<TD bgcolor=#33FFBB> {service_running_count} managers running </TD>"""
    except:
        harvest_manager_status = f"<TD bgcolor=#FA8074> Unable to connect to {harvest_server} </TD>"

    # Snapcenter job status
    sc_jobs = snapcenter_job_get(snapcenter_server)
    tme = datetime.datetime.now() - datetime.timedelta(1)
    total_jobs = 0
    success_jobs = 0
    for i in range(0, len(sc_jobs)):
        endtime = (sc_jobs[i]["endTime"])
        endtime = datetime.datetime.strptime(endtime, "%m/%d/%Y %I:%M:%S %p")
        if tme < endtime:
            total_jobs += 1
            if (sc_jobs[i]["status"] == "COMPLETED"):
                success_jobs += 1
    success_percent = int((success_jobs/total_jobs)*100)
    if success_percent == 100:
        job_status = f"<TD bgcolor=#33FFBB> {success_percent}% </TD>"
    else:
        job_status = f"<TD bgcolor=#FA8074> {success_percent}% </TD>"
    app_dt1 = f"""
    <TR>
        {url_alive_status}
        {HA_service_status}
        {grafana_status}
        {harvest_status}
        {harvest_manager_status}
        {job_status}
    </TR>
    """

    return app_dt1

# ITSM Details


def opsramp_auth():

    client_auth_path = "./secrets/u_opsramp.json"
    with open(client_auth_path) as f:
        client_auth = json.load(f)
    client_id = client_auth['client_id']
    client_secret = client_auth['client_secret']
    tenant_id = client_auth['tenant_id']
    payload = f"client_id={client_id}&grant_type=client_credentials&client_secret={client_secret}"
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    conn = http.client.HTTPSConnection("netapp.api.opsramp.com")
    conn.request("POST", "/auth/oauth/token", payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    token = (response['access_token'])
    return (token, tenant_id)


def GW_Status_get():

    token, tenant_id = opsramp_auth()
    token = f'Bearer {token}'
    headers = {
        'Authorization': token
    }
    payload = ''
    conn = http.client.HTTPSConnection("netapp.api.opsramp.com")
    conn.request(
        "GET", f"/api/v2/tenants/{tenant_id}/managementProfiles/search", payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    GW_count = response['totalResults']
    mgmt_profile_name = []
    GW_tunnel_status = []
    GW_registration_status = []
    for i in range(0, GW_count):
        mgmt_profile_name += [response['results'][i]['name']]
        GW_tunnel_status += [response['results'][i]['status']]
        GW_registration_status += [str(response['results'][i]['registered'])]
    return (GW_count, mgmt_profile_name, GW_tunnel_status, GW_registration_status)


def alert_correlation_get():

    token, tenant_id = opsramp_auth()
    token = f'Bearer {token}'
    headers = {
        'Authorization': token
    }
    payload = ''
    conn = http.client.HTTPSConnection("netapp.api.opsramp.com")
    conn.request(
        "GET", f"/api/v2/tenants/{tenant_id}/policies/alertCorrelation", payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    correlation_policy_name = []
    correlation_policy_status = []
    alert_co_policies_cnt = response['totalResults']
    for i in range(0, alert_co_policies_cnt):
        correlation_policy_name += [response["results"][i]["name"]]
        correlation_policy_status += [response["results"][i]["enabledMode"]]
    return(alert_co_policies_cnt, correlation_policy_name, correlation_policy_status)


def first_response_policy_get():

    token, tenant_id = opsramp_auth()
    token = f'Bearer {token}'
    headers = {
        'Authorization': token
    }
    payload = ''
    conn = http.client.HTTPSConnection("netapp.api.opsramp.com")
    conn.request(
        "GET", f"/api/v2/tenants/{tenant_id}/policies/firstResponse/", payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    first_res_policies_cnt = response['totalResults']
    first_res_policy_name = []
    first_res_policy_status = []
    for i in range(0, first_res_policies_cnt):
        first_res_policy_name += [response['results'][i]['name']]
        first_res_policy_status += [response['results'][i]['enabledMode']]
    return (first_res_policies_cnt, first_res_policy_name, first_res_policy_status)


def alert_escalation_get():

    token, tenant_id = opsramp_auth()
    token = f'Bearer {token}'
    headers = {
        'Authorization': token
    }
    payload = ''
    conn = http.client.HTTPSConnection("netapp.api.opsramp.com")
    conn.request(
        "GET", f"/api/v2/tenants/{tenant_id}/escalations/search", payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    escalation_policy_count = response['totalResults']
    escalation_policy_name = []
    escalation_policy_status = []
    for i in range(0, escalation_policy_count):
        escalation_policy_name += [response['results'][i]['name']]
        escalation_policy_status += [response['results'][i]['enabledMode']]
    return (escalation_policy_count, escalation_policy_name, escalation_policy_status)


def switch_backup_get():

    token, tenant_id = opsramp_auth()
    token = f'Bearer {token}'
    headers = {
        'Authorization': token
    }
    payload = ''
    conn = http.client.HTTPSConnection("netapp.api.opsramp.com")
    conn.request(
        "GET", f"/api/v2/tenants/{tenant_id}/jobs/search", payload, headers)
    res = conn.getresponse()
    response = json.load(res)
    job_count = response['totalResults']
    schedule = "NA"
    backup_job = "NA"
    for i in range(0, job_count):
        job_name = response['results'][i]['name']
        if job_name == 'Switch Config backup':
            schedule = response['results'][i]['schedule']['startDate']
            backup_job = job_name
    return (schedule)


def itsm_data_table():
    alert_co_policies_cnt, correlation_policy_name, correlation_policy_status = alert_correlation_get()
    first_res_policies_cnt, first_res_policy_name, first_res_policy_status = first_response_policy_get()
    escalation_policy_count, escalation_policy_name, escalation_policy_status = alert_escalation_get()
    GW_count, mgmt_profile_name, GW_tunnel_status, GW_registration_status = GW_Status_get()
    schedule = switch_backup_get()

    GW_status = "<TR><TH>Management Profile : Tunnel Status : Registered</TH></TR>"
    for i in range(0, GW_count):
        if GW_tunnel_status[i] == 'UP' and GW_registration_status[i] == 'True':
            GW_status += f"""<TR><TD bgcolor=#33FFBB> {mgmt_profile_name[i]} : {GW_tunnel_status[i]} : {GW_registration_status[i]}</TD></TR>"""
        else:
            GW_status += f"""<TR><TD bgcolor=#EFF613> {mgmt_profile_name[i]} : {GW_tunnel_status[i]} : {GW_registration_status[i]}</TD></TR>"""
    GW_connection_status = f"""
    <TD>
    <table>
        {GW_status}
    </table>
    </TD>
    """

    alert_corelation_policy_status = "<TR><TH>Policy Name : Policy Status</TH></TR>"
    for i in range(0, alert_co_policies_cnt):
        if correlation_policy_status[i] == 'ON':
            alert_corelation_policy_status += f"""<TR><TD bgcolor=#33FFBB> {correlation_policy_name[i]}: {correlation_policy_status[i]} </TD></TR>"""
        else:
            alert_corelation_policy_status += f"""<TR><TD bgcolor=#EFF613> {correlation_policy_name[i]}: {correlation_policy_status[i]} </TD></TR>"""
    alert_corelation_status = f"""
    <TD>
    <table>
        {alert_corelation_policy_status}
    </table>
    </TD>
    """

    first_response_policy_status = "<TR><TH>Policy Name : Policy Status</TH></TR>"
    for i in range(0, first_res_policies_cnt):
        if first_res_policy_status[i] == 'ON':
            first_response_policy_status += f"""<TR><TD bgcolor=#33FFBB> {first_res_policy_name[i]}: {first_res_policy_status[i]} </TD></TR>"""
        else:
            first_response_policy_status += f"""<TR><TD bgcolor=#EFF613> {first_res_policy_name[i]}: {first_res_policy_status[i]} </TD></TR>"""
    first_response_status = f"""
    <TD>
    <table>
        {first_response_policy_status}
    </table>
    </TD>
    """

    escalation_policy_statuses = "<TR><TH>Policy Name : Policy Status</TH></TR>"
    for i in range(0, escalation_policy_count):
        if escalation_policy_status[i] == 'ON':
            escalation_policy_statuses += f"""<TR><TD bgcolor=#33FFBB> {escalation_policy_name[i]}: {escalation_policy_status[i]} </TD></TR>"""
        else:
            escalation_policy_statuses += f"""<TR><TD bgcolor=#EFF613> {escalation_policy_name[i]}: {escalation_policy_status[i]} </TD></TR>"""
    escalation_status = f"""
    <TD>
    <table>
        {escalation_policy_statuses}
    </table>
    </TD>
    """
    itsm_dt = f"""
    <TR>
        <TD> {GW_connection_status} </TD>
        {alert_corelation_status}
        {first_response_status}
        {escalation_status}
        <TD> last backup on: {schedule} </TD>
    </TR>
    """
    return itsm_dt


def app_data(url, haproxy_servers, grafana_server, harvest_server, snapcenter_server):
    app_dt1 = "Test"  # app_data_table(url, haproxy_servers,
    #              grafana_server, harvest_server, snapcenter_server)
    itsm_dt = itsm_data_table()
    app_table1 = f"""
    <div>
    <h3 style='color : #464A46; font-size : 21px' align="" left "">  </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> GovDC Portal Status </B></TH>
                <TH><B> HA Proxy service status </B></TH>
                <TH><B> grafana service status </B></TH>
                <TH><B> harvest service status </B></TH>
                <TH><B> harvest manager service status </B></TH>
                <TH><B> Snapcenter job success rate </B></TH>
            </TR>
            {app_dt1}
        </Table>
    </div>
    <div>
    <h3 style='color : #464A46; font-size : 21px' align="" left ""> ITSM </h3>
    </caption>
        <Table>
            <TR>
                <TH><B> Gateway Status </B></TH>
                <TH><B> Corelation Policy status </B></TH>
                <TH><B> First Response Policy status </B></TH>
                <TH><B> Escalation Policy status </B></TH>
                <TH><B> Switch Config backup </B></TH>
            </TR>
            {itsm_dt}
        </Table>
    </div>

    """
    return app_table1
