# artifactor

Help capture artifacts from remote hosts. The intent is a lightweight, parallelized tool that allows pulling artifact type information. The tool has basic flexibility to store new and additional commands in JSON format, please refer to `commands.json.template`.

## Supported features

- Add and store commands
- Add and store hosts
- Use a port forward host for SSH to linux and WinRM to Windows
- Use password/key for each connection (password has limited testing)
- Parallelized connections to each host

## Setup

Download the repository to your local device and make sure you have python install. Once it is downloaded, make sure to retrieve the required packages.

```sh
# clone the repo from online
git clone https://github.com/3d6564/artifactor.git

# install required libraries from requirements.txt
pip install -r ./artifactor/requirements.txt
```

As long as Python is setup in your `PATH` you should be able to start it with the below.

```sh
# change to the artifactor directory
cd ./artifactor

# run artifactor, it will initialize if first time
python artifactor
```

## Troubleshooting

The nature of this tool can involve significant troubleshooting for networking and permission issues. A few of the common/major issues are covered below. This list is not all inclusive but the most common problems.

### Windows and WinRM
Adding the host to the TrustHosts list may be required and can be done with the below.
```sh
Set-Item WSMan:\localhost\Client\TrustedHosts -Value 'X.X.X.X'
```

Setup and check if WinRM is running in PowerShell.
```sh
# initial setup of WinRM
winrm quickconfig

# verify service is running
Get-Service WinRM
```

The remote Windows target may need a firewall rule configured. Here is an example of what that may look like. The `-Profile` may need set to whatever type of network the host is connected to. The `-LocalPort` may also need configured appropriately.
```sh
New-NetFirewallRule -Name "Allow WinRM HTTP" -DisplayName "Allow WinRM HTTP" -Enabled True -Direction Inbound -Protocol TCP -LocalPort 5985 -RemoteAddress X.X.X.X -Profile Private -Action Allow
```

### Linux
Linux is less prone to issues because it is using SSH for the jumpbox/forwarding and for the command execution. Things to consider are if there are any firewall rules and if the SSH service is running.

Verify status of SSH service.
```sh
sudo service ssh status
```

Attempt to check connect from source or jumpbox and inspect banner.
```sh
nc X.X.X.X 22
```