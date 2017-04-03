import socket                   
import os
import hashlib
from thread import *
import time

global history
history = ""

port0 = 60010
global socket0
socket0 = socket.socket()
socket0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname()
socket0.connect((host, port0))	

port1 = 60011
socket1 = socket.socket()
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname()
socket1.connect((host, port1))


def print_result(command, data):
	command = command.split(' ')
	if command[0] == "index": 
		print data
	elif command[0] == "hash" :
		if(command[1] == "verify") :
			print "MD5 checksum                      Last modified"
			print data
		elif(command[1] == "checkall") :
			data = data.split('\n')
			print "Filename         MD5 checksum                  Last modified"
			for entry in data:
				print entry
	return

def index(inp): 
	data = ""
	# return data corresponding to every file in the directory
	if inp[1] == "longlist":
		data = os.popen("ls -l").read()
	# data corresponding to a file in a specific time period
	elif inp[1] == "shortlist":
		initial_timestamp = inp[2]
		initial_timestamp = float(initial_timestamp)
		final_timestamp = inp[3]
		final_timestamp = float(final_timestamp)
		new_data = os.popen("ls").read()
		new_data = new_data.split('\n')
		displayFiles = []
		for file in new_data:
			if not file:
				break
			time = float(os.path.getmtime(file))
			if (time >= initial_timestamp) and (time <= final_timestamp) :
				displayFiles.append(file)

		for file in displayFiles:
			command = "ls -l " + file 
			info = os.popen(command).read()
			data += info
			# data += '\n'
	elif inp[1] == "regex": 
		data = os.popen('ls -l|grep --regexp=\"' + inp[2] + '\"').read()
		
	if not data: 
		data = '/0'
	socket0.send(data)
	return

def return_hash(command):
	hash = os.popen(command).read()
	hash = hash.split(" ")[0]	
	return hash

def download(command, sock): 
	protocol = command.split(' ')[1]
	filename = command.split(' ')[2]
	if protocol == "TCP":
		with open(''+filename, 'wb') as f:

			while True:
				flag=0
				data = sock.recv(1024)
				l=len(data)
				if data=='':
				    continue
				if data[l-1] == '\x00':
				    data=data[0:l-1]
				    flag=1

				# write data to a file

				f.write(data)

				if flag==1:
					break
		f.close()
	
	data = sock.recv(2048)
	currHash = os.popen(str("md5sum " + filename)).read()
	currHash = currHash.split(' ')[0]
	if currHash == data: 
		print "hashVerfication Successful"
	else :
		print "hashVerification Unsuccessful"
	# data = sock.recv(2048)
	# print data

	return
def hash(inp):
	data = ""
	#verfication for a particular file
	if inp[1] == "verify":
		command = "md5sum " + inp[2]
		hashed_value = return_hash(command) 
		time = float(os.path.getmtime(inp[2]))
		data = hashed_value + " " + str(time)

	#verfication for all the files
	elif inp[1] == "checkall":
		files_available = os.popen("ls").read()
		files_available = files_available.split()
		for file in files_available :
			print file
			if not file:
				break
			command = "md5sum " + file
			hashed_value = return_hash(command)
			time = float(os.path.getmtime(file))
			data += file + " " + hashed_value + " " + str(time) + '\n'

	socket0.send(data)
	return

def receive(): 
	while True:
		pass
		inp = socket1.recv(2048)
		inp = inp.split(' ')
		if inp[0] == "index":
			index(inp)

		elif inp[0] == "hash":
			hash(inp)

		elif inp[0] == "download":
			download_recv(inp, socket0)

		elif inp[0] == "sync": 
			sync_directories_recv()
			# do something 
start_new_thread(receive, ())

def download_recv(inp, sock):
	if inp[1] == "TCP" :
		filename = inp[2]
		f = open(inp[2],'rb')
		l = f.read(2048)
		while l:
			print "hello"
			sock.send(l)
			l = f.read(2048)
		sock.send('\0')
		f.close()
		data = os.popen(str("md5sum " + inp[2])).read()
		data = str(data)
		data = data.split(' ')
		print "rishabh"
		sock.send(data[0])
		print "arora"
		# i = "ls -l " + filename
		# out = os.popen(i).read()
		# out = str(out)
		# sock.send(out)

	elif inp[1] == "UDP":
			pass

def sync_directories_recv() :
	#read ls command

	command = socket0.recv(2048)
	print "command ", command
	
	command = os.popen(command).read()
	command = str(command)
	socket0.send(command)
	
	#read the list of common files
	flag = 0
	CommonFiles = socket0.recv(2048)
	if CommonFiles == "\0": 
		flag = 1
	CommonFiles = CommonFiles.split('\n')

	#send common files with later modification time
	eligible = ""
	count_eligible = 0

	print "Commonfiles", CommonFiles

	if flag == 0:
		for file in CommonFiles:
			if file == "" or file == '\n':
				break
			file = file.split(' ')
			print "file[0]", file
			timeOwn = float(os.path.getmtime(file[0]))
			timeRemote = float(file[1])
			if timeOwn > timeRemote :
				eligible += file[0] + '\n'
				print "ye babay"
				count_eligible += 1
		
	print "eligible", eligible
	if eligible == "" or eligible == "\n": 
		eligible == '\0'
	print "eligible", eligible
	socket0.send(eligible)
	eligible = eligible.split('\n')

	for i in xrange(0, count_eligible):  
		inp = socket0.recv(2048)
		inp = inp.split(' ')
		if inp[2] == "" or inp[2] == "\n": 
			break
		download_recv(inp, socket0) 
	
	print "end of function"
	# command = socket0.recv(2048)
	# if command == "\0": 
	# 	socket0.send("Nothing to delete!")
	# else :
	# 	os.popen(command).read()
	# 	socket0.send("Deleted the required files")
	return

# def _sync_directories_recv():
# 	port_sync_recv = 50003
# 	global socket0
# 	socket0 = socket.socket()
# 	socket0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 	socket0.connect((host, port_sync_recv))
	
# 	while True: 
# 		sync_directories_recv()
# 		time.sleep(1)
# start_new_thread(_sync_directories_recv, ())


while True: 
	command = raw_input("prompt=> ")
	history += (command + "\n")
	if command == "history":
		print history
		continue

	socket1.send(command)
	decide = command.split(' ')[0]

	if decide == "download": 
		download(command, socket0)
	else :
		data = socket0.recv(2048)	
		if data != '/0':
			print_result(command, data)
	pass

