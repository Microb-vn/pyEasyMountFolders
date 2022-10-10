# EasyMountFolders
Linux/Python script to automatically attempts to mount SMB/CIFS shared folders when you are connected to a network.

*Disclaimer: the script stores login credentials that allow access to the shared folders on the computers' local file system, with the security set so that only the user can access the stored credentials. Mind you that anyone with root access (sudo) can change the file's security attributes and with that can get access to the stored credentials! If you find this to big a risc, do not use this script!*


# Prerequisites
to be able to use this script, you need to:

- have **superuser (sudo) access** to run mount and umount commands on your machine.\
You may need to ask your system system admin to configure that for you. He/She can go [here](#configure-minimal-sudo-access-to-be-able-to-run-the-script) to find out how to do that.
- make sure that **Python v3 is installed**.\
The script assumes that your python executable is here: /usr/bin/python3\
When you or your distribution uses another folder to install python, you may need to update that file location in the main script.
- verify with your network administrator(s) that you have a network account with sufficient access (readonly or Read-Write) to all network shares on the hosts that you will be accessing.

# How to install

- **copy the** contents of this **repository** to your local disk drive - preferably into your personal folder.\
*It is highly recommended to use your personal folder to prevent file and folder access issues while running this script.*\
Note that the repository contains some hidden folders. You may need to (temporarily) enable the "view hidden files" option in your file explorer.
- make sure the **main script** (file \<your copy location\>/.py/EasyMountFolders.py) **is marked as executable**. If you'r not sure if this file is currently marked as executable, execute the following command:

```bash
chmod +x <your copy location>/.py/EasyMountFolders.py
```
- **Update the configuration file** *folders.default.json* in  \<your copy location\> to configure *your* drive mappings.\
See the [Configuration section](#configure-your-mapped-drives) on how to do that.
- **Run the script once** and see if the script works for you.\
You will be prompted for UserID('s) and Password(s) that need to be used to create the mappings. Also, when the script is run as normal user (no *sudo* is used to launch the script), you will be prompted for your sudo password (unless you or your administrator used the NOPASSWD option in the /etc/sudoers file).
- When satisfied, **configure the script to run at user-login, or from your Linux Application Menu or a TaskBar shortcut**.\
*Because the many different distribution of Linux use different methods to configure startup/login programs, no instructions are added in this document. A sample bash command file is available to included in the repository root that can be used to easily trigger the script.*


# Configuration

## Configure your mapped drives

The repository contains a sample configuration file, which has the following format:

```json
{
    "Mappings": [
        {
            "LocalFolder": "~/nassie/video",
            "RemoteHost": "192.168.123.253",
            "RemoteFolder": "video"
        },
        {
            "LocalFolder": "~/nassie/rob",
            "RemoteHost": "192.168.123.253",
            "RemoteFolder": "homes/rob"
        },
        {
            "LocalFolder": "~/nassie/audio",
            "RemoteHost": "192.168.123.253",
            "RemoteFolder": "audio"
        }
    ]
}
```

As displayed above, the json file contains an array of drives-to-be-mapped. Each array element contains the following attributes:

- **LocalFolder**. The folder on your machine where the network drive should be mapped to. This can be either a full path (e.g. /mnt/MyHost/videos), a relative path (e.g. MyHost/videos) or a personal homefolder path (e.g. ~/Myhost/videos).\
The relative path will point to a folder that is in the current directory - the directory that has focus the moment the script is triggered -.\
The personal homefolder path will point to a folder in your local "home" folder (aka the "Personal Folder" in most Linux GUI's).\
*It is highly recommended to always use a 'personal homefolder path'*.\
\
Note that this folder does not have to exist before you trigger the script. The only requirement is that you (that is, your local linux account) should be able to create it at the indicated location.\
\
Also, the folder - when it exists - should be empty.

- **RemoteHost**. The IP address, hostname of (UNC) name of the host that publishes the shared folder. When a name is used, it must be resolvable to an address in your network, either by DNS or WINS.\
Before a mapping attempt is made, an attempts is done to discover the host on the network. When no host responds to the query made by the script, the mapping attempt is skipped.\
This allows you to ALWAYS execute your script at logon, and configure different hosts for different networks you connect to. The host detection will decide for you which mappings are be made and which are skipped.)
- **RemoteFolder**. The name of the shared CIFS/SMB (or Windows) shared folder on the host.

A few notes when using the mappings:

- When multiple mappings are defined for the same host, one network account is used to execute the mount commands. You need to ensure that you use an account that has sufficient access to all shares on that host.
- As you can see in the sample configuration file, you can create drive mappings to subfolders in a shared folder (e.g. create a mapping to a shared folder homes/rob, while the host only exposes the homes folder. As result the subfolder homes/rob will be mounted, thus implicitly hiding all the other homes subfolders for you)

## Configure minimal sudo access to be able to run the script

The script contains both mount and umount commands that need to be executed in normal userspace. These commands require root level privileges. In order to let non-privileged users execute these commands, you or your system administrator will need to update the /etc/sudoers file.

*WARNING: Never edit the /etc/sudoers file with a normal editor; always use the visudo command to update the file to prevent that the file gets corrupted*

*NOTE: In the below (simple) example, one user will be allowed to use the script. If you want, you can use linux group membership(s) to allow specific users - members of that group - to allow running the sudo commands, and configure the sudoers settings for that group*

To allow *a single user* to issue the appropriate mount commands, add the folling line to the sudoers file

```text
<user-name-here> ALL=(ALL) /usr/bin/mount -t cifs *,/usr/bin/umount -t cifs *
```

With the above line added, the user can execute the script. When the script executes, the user will be prompted for his/her password. If you want to allow the user to execute the script without a sudo password prompt, change the above line to:

```text
<user-name-here> ALL=(ALL) NOPASSWD:/usr/bin/mount -t cifs *,/usr/bin/umount -t cifs *
```


# Typical script output

When the script is executed, you will se output as shown below:

```text
INFO: Script EasyMountFolders.py is triggered, Starting its execution now...
INFO: Checking logged in user
INFO: Normal user rob found; expect a sudo password login during this script execution!
INFO: Checking required working directory /home/rob/Documenten/GitHub/EasyMountFolders/.cache
INFO: Working directory is available
INFO: Based on trigger command used, the script assumes that -MappingsFile folders.default.json is to be used.
INFO: Start the unmount of previously mounted drives
INFO: No drives found to unmount
INFO: Checking the contents of /home/rob/Documenten/GitHub/EasyMountFolders/folders.default.json
INFO: No anomalies found in /home/rob/Documenten/GitHub/EasyMountFolders/folders.default.json
INFO: Start creating the drive mappings
INFO: Checking host 192.168.123.253
INFO: Found; getting the credentials for host 192.168.123.253 to create mapping to remote folder video
INFO: Attemtping to map remote folder to ~/nassie/video
[sudo] wachtwoord voor rob:            
INFO: mapping action executed, network folder is now available in ~/nassie/video
INFO: Checking host 192.168.123.253
INFO: Found; getting the credentials for host 192.168.123.253 to create mapping to remote folder homes/rob
INFO: Attemtping to map remote folder to ~/nassie/rob
INFO: mapping action executed, network folder is now available in ~/nassie/rob
INFO: Checking host 192.168.123.253
INFO: Found; getting the credentials for host 192.168.123.253 to create mapping to remote folder Download
INFO: Attemtping to map remote folder to ~/nassie/download
INFO: mapping action executed, network folder is now available in ~/nassie/download
INFO: Done! This window will close in 5 seconds
```