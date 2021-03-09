import sshtunnel
import os
import stat
import calendar
from datetime import datetime, timedelta
import pysftp
from zipfile import ZipFile
import time
from pathlib import Path
import configparser
from paramiko import SSHClient
import paramiko

# TODO
# Check required period
# Fix change of month to write day/previous_month - day/next_month
# Add to mail

config = configparser.ConfigParser()
config.read('config.ini')

############### Configuration ################

priv_key = config['keys']['private_key']
jh = config['servers']['netact_jh']
netact_ip = config['servers']['netact_ip']
jh_username = config['usernames']['jh_username']
netact_username = config['usernames']['netact_username']
netact_pwd = config['passwords']['netact_pwd']
localhost = config['servers']['localhost']
path_a = config['paths']['path_a']
path_b = config['paths']['path_b']
local_path = Path(config['paths']['local_path'])

current_date = datetime.now().date()
current_month = datetime.now().month
mont_abbr = calendar.month_abbr[current_month]

start_date = (current_date - timedelta(days=7)).strftime('%d-%m')
end_date = current_date.strftime('%d-%m')

#date_key = (datetime.today() - timedelta(days=1)).strftime('%Y_%m_%d')
date_key = datetime.today().strftime('%Y_%m_%d')
daily_files = []

with sshtunnel.open_tunnel(
        (jh, 22),
        ssh_username=jh_username,
        ssh_pkey=priv_key,
        remote_bind_address=(netact_ip, 22),
        local_bind_address=('0.0.0.0', 10022)
) as tunnel:
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    with SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(localhost,
                    port=tunnel.local_bind_port,
                    username=netact_username,
                    password=netact_pwd
                    )
        stdin, stdout, stderr = ssh.exec_command('cd ' + path_b + '/;ls -a | sort')
        for line in stdout:
            if date_key in line:
                daily_files.append(line)
    with pysftp.Connection(host=localhost, username=netact_username, password=netact_pwd, port=10022, cnopts=cnopts) as sftp:
        print("Connection succesfully established...\n")
        sftp.chdir(path_b)
        for f in daily_files:
            f = f.strip()
            sftp.get(remotepath=path_b + f, localpath=Path(local_path).absolute().joinpath(f))

print("Today's files are: \n")
for kpi in daily_files:
    print(kpi, end="")

os.chdir(local_path)

kpizip = start_date + '_' + end_date + '.zip'

with ZipFile(kpizip, 'w') as zipObj2:
    zipObj2.write(daily_files[0].strip())
    zipObj2.write(daily_files[1].strip())

print("")
print(kpizip + " created")
