import socket
import threading
import time
import sys
import os
import codecs
import json
# TODO : fix cmd interpretation, move all cmd interpretation code to the client script
# TODO : write function for each command
# TODO : feature that allows user to send message to a specific user
#TODO : RUSSIFICATION
#! server doesn't parse commands, they come clearly defined  with the message


class Sender:  # class is responsible for sending messages to other users
    def __init__(self):
        self.encoding = "Windows 1251"
        self.max_header_size = 64

    def prepare_to_send_msg(self, msg):  # msg - message_object
        # we need to remove delay and to and not_notif_message properties from our message
        sender = msg["from"]
        recipient_account = msg["to"]
        delay = msg["delay"]
        msg = parser.delete_message_properties(
            msg, "delay", "to", "not_notif_message", "command")
        msg_formatted = parser.encode_wrap_message(msg)
        # we don't use len(msg) cause it will output number of object properties
        message_len = len(msg_formatted)
        message_len_formatted = parser.format_message_length(message_len, True)
        
        if delay:
            delay = float(delay)
            send_timer = threading.Timer(delay,self.send,args = (message_len_formatted,msg_formatted,recipient_account))
            send_timer.start()
        else:
            self.send(message_len_formatted,msg_formatted,recipient_account)
        
    def send(self,msg_len_formatted, msg_formatted, recipient_account):
        conn = self.get_conn(recipient_account)
        if conn:  # for beginning we will just ignore that message hasn't been sent to user if its
            # account doesn't exist
            conn.send(msg_len_formatted)
            conn.send(msg_formatted)

    def get_conn(self, account_name):
        for elem in server.connections:
            if elem[0] == account_name:
                if len(elem) != 1:  # if connection was specified

                    return elem[1]
                print(f"No account named '{account_name}' has been found!")
                return 0

        print(f"No account named '{account_name}' has been found!")
        return 0

    def send_info(self, account_name):  # we will find connection in Server.connections
        pass

    # this function notifies sender that his message is on the server
    def notify_server_delivery(self):
        pass

    def notify_client_delivery(self):
        pass
# need to create one interface of message wrapping and unwrapping 

class Parser:  # performs various operations on our messages
    def __init__(self):
        self.encoding = "Windows 1251"
        self.max_header_len = 64

    def delete_message_properties(self, msg, *args):  # type(*args) ==string
        for argument in args:
            del msg[argument]

        return msg

    def encode(self, message):
        return message.encode(self.encoding)

    def decode(self, message):
        return message.decode(self.encoding)

    def format_message_length(self, msg_len, to_user=True):  # msg - int
        if to_user:  # encoding our message_len
            msg_len = str(msg_len)
            msg_len = msg_len+" "*(self.max_header_len-len(msg_len))
            msg_len = self.encode(msg_len)
            return msg_len
        else:  # decoding our message_len
            msg_len = self.decode(msg_len)
            msg_len = int(msg_len.strip())
            return msg_len

    def json_to_obj(self, jsn):
        obj = json.loads(jsn)
        return obj

    def obj_to_json(self, obj):
        json_string = json.dumps(obj)
        return json_string

    def decode_unwrap_message(self, msg):  # used for messages
        msg = self.decode(msg)
        msg = self.json_to_obj(msg)
        return msg

    def encode_wrap_message(self, msg):  # used for messages , not headers
        msg = self.obj_to_json(msg)
        msg = self.encode(msg)
        return msg


class Server:
    def __init__(self):
        self.online_count = 0
        self.HEADERSIZE = 64
        self.PORT = 5050
        self.IP = "192.168.1.191"  # changed for local for the time being
        self.ADDR = (self.IP, self.PORT)
        self.encoding = "utf-8"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # matrix, each element of array contains 3 vals
        self.connections = [["a"], ["b"], ["c"], ["d"], [
            "e"], ["f"]]  # ! server identifies users using
        #! different accounts but users don't identify themselves (they is "a" account)
        self.client_function_list = {  # functions that can be called after client request : -s: , -disconnect: and so on
            "-s:": sender.prepare_to_send_msg,
            "-disconnect:": self.disconnect_user,
            "-info": sender.send_info
        }
        # accountname, connection info #! if len of element == 1 -> account is free for use

    def sendInfo(self, conn): # doesn't work! 
        filepath = "info.txt"
        with codecs.open(filepath, "r", "Windows 1251") as file:
            info = file.read()
            info = info.encode("Windows 1251")
        conn.send(info)
        print(f"info was sent to {conn}")

    def disconnect_user(self, msg):
        user_to_disconnect = msg["from"]

        for i in range(len(self.connections)):
            if self.connections[i][0] == user_to_disconnect:
                print(f"'{user_to_disconnect}' has been disconnected")
                self.connections[i] = [user_to_disconnect]
                print(self.connections, " - connections\n")
                break

    def execute_client_command(self, message):  # message in object repr
        message_command = message["command"]
        if message_command == "-s:":  # we only need message_command, functions work with message_obj
            self.client_function_list[message_command](message)

        elif message_command == "-info:":
            self.client_function_list[message_command](message)

        elif message_command == "-disconnect:":
            self.client_function_list[message_command](
                message)  # -disconnect: command

    def check_if_connected(self, indx):
        if len(self.connections[indx]) == 1:
            return False
        return True

    def login_client(self,conn):
        login_message_length = conn.recv(self.HEADERSIZE)
        
        login_message = conn.recv(parser.format_message_length(login_message_length,to_user = False))
        formatted_login_message = parser.decode_unwrap_message(login_message)
        account_name =formatted_login_message["text"]
        if account_name=="-disconnect:":
            pass
        is_valid,error = self.validity_check(account_name)
        
        return [account_name,is_valid,error]
        
    
    def add_to_connections(self,indx, connection):  # returns index of our user in array
        self.connections[indx].append(connection)
        return 0
    
    
    def get_client_index(self,account_name):
        indx = list(map(lambda elem:elem[0],self.connections)).index(account_name)
        return indx

    def validity_check(self,account_name):
        account_names = list(map(lambda elem:elem[0],self.connections))
        if account_name in account_names:
            indx = self.get_client_index(account_name)
            if len(self.connections[indx])!=0:
                return [False, "this account has already been connected"]
            else:
                return [True,""]
        return False,"this account doesn't exist"

    def handle_client(self, conn, addr):
        self.online_count += 1
        print(f"[New connection] {addr} connected")
        while True:
            account_name,is_valid,error = self.login_client(conn) # error is "" if login was successful
            if is_valid:
                client_index = self.get_client_index(account_name) # it is easier to operate with client index
                self.add_to_connections(client_index,conn)# that with our account name 
                print(f"{addr} has been connected as {account_name}")
                break
            else:
                print(f"LoginProcessError: invalid account name: {account_name}")
                continue
        
        print(f"New connection {addr} has logged in as '{account_name}'")
        while self.check_if_connected(client_index):
            try:
                msg_length = conn.recv(self.HEADERSIZE)
            except:
                print(f"{self.connections[client_index]} disconnected from the server")
                break
            msg_length = parser.format_message_length(msg_length, False)
            message = conn.recv(msg_length)
            #! there must be a method decoding message
            unwrpt_message = parser.decode_unwrap_message(message)
            self.execute_client_command(unwrpt_message)
            print(unwrpt_message)

    def start(self):  # handles all connection and passes each connection for handle_client
        self.sock.bind(self.ADDR)
        self.sock.listen()
        print(f"[Listening] Server is listening on {self.IP}")
        while True:
            conn, addr = self.sock.accept()
            thread = threading.Thread(
                target=self.handle_client, args=(conn, addr))
            thread.start()


sender = Sender()
parser = Parser()
server = Server()
print("Starting server")
server.start()


# code that is not needed as for now:

def exec_exit(self, *args):
    print("Shutting the server down")
    os._exit(0)