# Mapmaker LiDAR

### An automated worflow for Surface Reconstruction

## Installation steps for Windows Subsystem for Linux 2 (WSL 2) and docker

#### Step 1: Start a command prompt with administrative privileges.

#### Step 2: Run "wsl -l -o" to list other Linux releases.

#### Step 3: Type:

```sh wsl -l -o 

Windows Subsystem for Linux Distributions:
Ubuntu-22.04
docker-desktop
docker-desktop-data

```

then:

```sh
wsl --install -d Ubuntu-22.04
```

#### Step 4: Once the installation process is complete, you will be prompted to create a usename and password and confirm the password, use `mapmaker` for both

#### Step 5: The system will log user mapmaker and present the linux bash prompt, type `sudo visudo`, enter the password for mapmaker.

#### Step 6: We will add user mapmaker to the sudoers list (to allow for priviledge escalation and override the password requests. Type the following directive

```sh
mapmaker ALL=(ALL:ALL) NOPASSWD:ALL
```

directly below `%sudo   ALL=(ALL:ALL) ALL`, on the section that reads `# Allow members of group sudo to execute any command`, press CTRL+O and CTRL+X to save your changes to the 
sudoers list and exit editing mode. The changes are registered immediately and you shoudl not need to type a password any time you invoque a command with sudo form now on

#### Step 7: Now we need to install docker on the ubuntu side. Type:

```sh
sudo apt update && sudo apt upgrade -y
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

#### Step 8: Now we need to install docker on the ubuntu side. Type:

#### Step 9: Now close the WSL 2 window and open a Windows command prompt. Type:

```sh
wsl --set-default Ubuntu-22.04
```

followed by:

```sh
wsl --shutdown
```

#### Step 10: Reopen a wsl 2 sesion by typing: ```sh wsl `` and once in the Ubuntgu prompt, type: ```sh docker --version ```. Docker should reply with a version number. At this time, you may close all windows. Ubuntu 22-04 is now the default version running in WSL 2 and docker is up and running as well.

#### Step 11: Install Docker for Windows and Settings/General, enable `Use the WSL 2 base engine``

Also, under Settings/Resources, ensure `Enable inmtegration with my default WSL distro` is enable, as well that ```Ubuntu-2204``` is enabled under  ```Enable integration with additional distros``


