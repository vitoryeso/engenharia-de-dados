# ██████╗  ██████╗ █████╗   DEPTO DE ENGENHARIA DE
# ██╔══██╗██╔════╝██╔══██╗  COMPUTACAO E AUTOMACAO
# ██║  ██║██║     ███████║  UFRN, NATAL-RN, BRASIL
# ██║  ██║██║     ██╔══██║   
# ██████╔╝╚██████╗██║  ██║  PROF CARLOS M D VIEGAS
# ╚═════╝  ╚═════╝╚═╝  ╚═╝  viegas '@' dca.ufrn.br
#
# SCRIPT CLIENTE TCP (python3)
#
# COMO EXECUTAR?
#  python clienteTCP.py <endereco-ip-do-servidor>
#

# importacao das bibliotecas
from socket import *
import sys
import time

# definicao das variaveis
serverName = str(sys.argv[3])
print("server name: ", serverName)
serverPort = 30000 # porta a se conectar
clientSocket = socket(AF_INET,SOCK_STREAM) # criacao do socket TCP
clientSocket.connect((serverName, serverPort)) # conecta o socket ao servidor

sentence = 'hostname: ' + gethostname() + ' ip: ' + gethostbyname(gethostname())
print ('> enviando para o servidor -> %s' % sentence)
clientSocket.send(sentence.encode('utf-8')) # envia o texto para o servidor
print("sleeping in 2 seconds...")
time.sleep(2)
clientSocket.close() # encerramento o socket do cliente

