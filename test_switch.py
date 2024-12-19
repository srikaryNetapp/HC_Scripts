import json
import paramiko
def ssh_command_push(switch, command):
    """

    Function to send commands over ssh session

    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    mel_credentials_path = "./secrets/u_mel_secret.json"
    with open(mel_credentials_path) as f:
        mel_credentials = json.load(f)

    if switch in mel_credentials:
        cumulus_username = mel_credentials[switch]["username"]
        cumulus_password = mel_credentials[switch]["password"]
        ssh.connect(switch, username=cumulus_username,
                    password=cumulus_password)
    else:
        error_msg = f"Error: Credentials for {switch} not found"
        print(error_msg)
        exit

    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(command)
    out = ssh_stdout.read()
    err = ssh_stderr.read().decode('utf-8')
    output = out.decode('utf-8').split('\n')
    if (err == ''):
        return output
    else:
        return err

if __name__ == '__main__':
    command = "show hosts | include Hostname"
    mel_switch = "172.27.96.124"
    hostname = ssh_command_push(mel_switch, command)
    print(hostname)