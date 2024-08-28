# Mapmaker LiDAR

### An automated worflow for Surface Reconstruction

## Install using Command Prompt

#### Step 1: Start CMD with administrative privileges.

#### Step 2: Run "wsl -l -o" to list other Linux releases.

#### Step 3: You can install your favorite Linux distribution, use "wsl --install -d NameofLinuxDistro." (In this case we are using Ubuntu-22.04

```sh
wsl -l -o

Windows Subsystem for Linux Distributions:
Ubuntu-22.04
docker-desktop
docker-desktop-data

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

#### Step 7: Now we need to install docker on the ubuntu side. Type 



#### Step 4: Set Ubuntu-22.04 as the default installation in WSL 

```sh

wsl --set-default Ubuntu-22.04

```
