import subprocess
import os
def vmware_cli():
  """ Retrives data from the imported Vmware Powercli Script .
      Convert to datframe to list to make it compatible for htmt() of the program.
      Append the values to result dictionary.
      :param:
      :return:
  """
  POWERSHELL_PATH= "powershell.exe"
  os.chdir("C:\\Program Files\\StorageManager\\client")
  firmware_command = f".\\SMcli.exe 172.27.18.16 -c 'show Controller [a];' | findstr 'Firmware'"
  fw_command = [POWERSHELL_PATH,firmware_command]
  out = subprocess.run(fw_command, stdout=subprocess.PIPE, shell=True)
  # script_path = "C:\\HC_Scripts\\vmware_hc.ps1"

  # commandline_options = [POWERSHELL_PATH, '-ExecutionPolicy', 'Unrestricted', script_path]
  # out = subprocess.run(commandline_options, stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines = True)
  
  return out.stdout


print(vmware_cli())