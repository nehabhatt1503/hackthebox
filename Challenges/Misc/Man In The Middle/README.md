# Man In The Middle
## Challenge Description:
Help! One of our red teamers has captured something between a user and their computer, but we've got no idea what we're looking at! Can you take a look?

### STEPS:
### ![ab](https://github.com/user-attachments/assets/2ab2f2c6-2848-4763-879e-b8502a393ce8) - unzip the file usimg the password 'hackthebox'
### ![ab](https://github.com/user-attachments/assets/9bc335a7-ca3f-4715-b597-0531b00803c0) - look inside the file
### ![ab](https://github.com/user-attachments/assets/542877e5-67af-4055-acce-d065c60f46c0) - We have a binary file named 'mitm.log'. Open this file in Wireshark.
### ![ab](https://github.com/user-attachments/assets/eb588a3a-d3a7-4f7a-801c-a19f09292cb6) - We can see the HCI_MON (Bluetooth Linux HCI Monitor Transport) protocol,L2CAP protocol,their length,information,etc.
### ![ab](https://github.com/user-attachments/assets/1fd5f885-3f50-4cb6-ad69-e5d542b08f53) - Save the file in the system and write python code for extracting the flag. 

### ![ab](https://github.com/user-attachments/assets/1c4e5a26-7913-45f5-b6b2-a20ab3e87c1d) - all the files should be in the same folder.
### ![ab](https://github.com/user-attachments/assets/0c223bf6-ac83-48c1-9bc9-d74349395198) - run the python code and you will receive the flag.
