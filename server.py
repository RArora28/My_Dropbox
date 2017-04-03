import socket
import os
import hashlib
from thread import *
import time

command = ""
deleted = {}
global history
history = ""

port0 = 60010
global conn0
socket0 = socket.socket()
socket0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname()
socket0.bind((host, port0))	

port1 = 60011
socket1 = socket.socket()
socket1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host = socket.gethostname()
socket1.bind((host, port1))

socket0.listen(5)
socket1.listen(5)

conn0, addr = socket0.accept()
conn1, addr = socket1.accept()


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
	conn0.send(data)
	return

def return_hash(command):
	hash = os.popen(command).read()
	hash = hash.split(" ")[0]	
	return hash

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

	conn0.send(data)
	return

def print_result(command, data):
	command = command.split(' ')
	if command[0] == "index": 
		print data
	elif command[0] == "hash" :
		if(command[1] == "verify") :
			print "MD5 checksum      Last modified"
			print data
		elif(command[1] == "checkall") :
			data = data.split('\n')
			print "Filename       MD5 checksum      Last modified"
			for entry in data:
				print entry
	return

def download(command, conn): 
	protocol = command.split(' ')[1]
	filename = command.split(' ')[2]
	if protocol == "TCP":
		# with open(filename, 'wb') as f:	
		# 	while True:
		# 		data = conn.recv(2048)
		# 		if data[len(data)-1] == '\0':
		# 			print "hello"
		# 			if len(data) != 1:	
		# 				data = data[0: len(data)-1]
		# 				f.write(data)
		# 			break
		# 		else :	
		# 			f.write(data)
		with open(''+filename, 'wb') as f:

			while True:
				flag=0
				data = conn.recv(1024)
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
	
	data = conn.recv(2048)
	currHash = os.popen(str("md5sum " + filename)).read()
	currHash = currHash.split(' ')[0]
	
	if currHash == data: 
		print "hashVerfication Successful"
	else :
		print "hashVerification Unsuccessful"

	# data = conn.recv(2048)
	# print data
	return

def sync_directories_send():

	conn1.send("sync")

	conn0.send("ls -1")
	RemoteFiles = conn0.recv(2048)
	RemoteFiles = RemoteFiles.split('\n')
	OwnFiles = os.popen("ls -1").read()
	OwnFiles = OwnFiles.split('\n')
	PossibleDownloads = []
	to_be_deleted = "rm -rf"
	print "mera naam hai "
	# # categorises as common file or not
	for file in RemoteFiles:
		if (file in OwnFiles) or (file not in deleted) or (deleted[file] == False) :
			PossibleDownloads.append(file)
		elif (file not in OwnFiles) and (deleted[file] == True):
			to_be_deleted += " " + file


	common_files = ""
	global Time
	Time = 0
	
	for file in PossibleDownloads:
		if not file or file == '\n':
			break
		if file in OwnFiles:
			Time = float(os.path.getmtime(file))
		else : 
			Time = float(-1) 
		common_files += (str(file) + " " + str(Time) + '\n')
	print common_files

	if common_files == "": 
		common_files == "\0"
	conn0.send(common_files)

	# download the modified files
	Eligible = conn0.recv(2048)
	Eligible = Eligible.split('\n')

	for file in Eligible:
		command = "download TCP " + file
		print command
		conn0.send(command)
		if command.split(' ')[2] == "": 
			break
		download(command, conn0)

# 	print "bahar to aaya"
# 	# delete the files 
# 	# if to_be_deleted == "rm -rf":
# 	# 	to_be_deleted == '\0'
# 	# conn0.send(to_be_deleted)
# 	# message = conn0.recv(2048)
# 	# print message
	return

def _sync_directories_send():
	while True: 
		print "entered"
		sync_directories_send()
		print "exit"
		# time.sleep(2)

start_new_thread(_sync_directories_send, ())

def download_recv(inp, sock):
	if inp[1] == "TCP":
		filename = inp[2]
		f = open(inp[2],'rb')
		l = f.read(2048)
		while l:
			sock.send(l)
			l = f.read(2048)
		sock.send('\0')
		f.close()
		data = os.popen(str("md5sum " + inp[2])).read()
		data = str(data)
		data = data.split(' ')
		sock.send(data[0])	
		i = "ls -l " + filename
		out = os.popen(i).read()
		out = str(out)
		# sock.send(out)
	elif inp[1] == "UDP":
			pass

def receive(): 
	while True:
		inp = conn1.recv(2048)
		inp = inp.split(' ')
		if inp[0] == "index":
			index(inp)

		elif inp[0] == "hash":
			hash(inp)

		elif inp[0] == "download":
			download_recv(inp, conn0)

		elif inp[0] == "sync": 
			pass
			# do something 
start_new_thread(receive, ())

while True: 
	command = raw_input("prompt=> ")
	history += (command + "\n")
	if command == "history":
		print history
		continue
	print command
	conn1.send(command)
	decide = command.split(' ')[0]

	if decide == "download": 
		download(command, conn0)
	else :
		print "hello"
		data = conn0.recv(2048)
		print "data"	
		if data != '/0':
			print_result(command, data)


