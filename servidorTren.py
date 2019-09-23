
import sys
import socket
import struct
import time
import statistics

MAX_ETHERNET_DATA=1500
MIN_ETHERNET_DATA=46
ETH_HDR_SIZE=14+4+8+12 # MAC header + CRC + Preamble + Interframe
IP_HDR_SIZE=20
UDP_HDR_SIZE=8
RTP_HDR_SIZE=12

MAX_WAIT_TIME=8
MAX_BUFFER=100000000

packet_list=[]
B_MASK=0xFFFFFFFF
DECENASMICROSECS=100000

npackets=0
len_paq=0
lista_bw=[]
lista_tiempos=[]
lista_delay=[]


if __name__ == "__main__":
	if len(sys.argv)!=3:
		print ('Error en los argumentos:\npython servidorTren.py ip_escucha puerto_escucha\n')
		exit(-1)

	ipListen=sys.argv[1]
	portListen=int(sys.argv[2])
	sock_listen = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # UDP
	sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,MAX_BUFFER)
	sock_listen.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock_listen.bind((ipListen,portListen))
	sock_listen.settimeout(MAX_WAIT_TIME)

	#Creamos las cabeceras y le añadimos la cabcera ethernet si estamos en ese caso
	Cabeceras=UDP_HDR_SIZE+IP_HDR_SIZE
	if ipListen!="127.0.0.1":
		Cabeceras+=ETH_HDR_SIZE

	#Recibimos los paquetes y salimos del bucle cuando no se reciban paquetes en MAX_WAIT_TIME segundos
	while True:
		try:
			data, addr = sock_listen.recvfrom(2048)
			#Para cada paquete recibido añadimos a la lista de paquetes
			#una tupla que contiene los datos del paquete y el tiempo en que 
			#se recibió dicho paquete
			packet_list.append((data,time.time()))

		except socket.timeout:
			break

	
	for packet in packet_list:
	#Para cada paquete recibido extraemos de la cabecera
	#cada uno de los campos necesarios para hacer los cálculos

		data=packet[0]
		header=struct.unpack('!HHII',data[0:12])
		seq_number=header[1]
		send_time_trunc=header[2]
		trainLength=header[3]
		#ATENCIÓN: El tiempo de recepción está en formato: segundos.microsegundos
		#Usar este tiempo para calcular los anchos de banda
		reception_time=packet[1]
		# Creamos una lista para los tiempos de recepcion
		lista_tiempos.append(reception_time)
		# Aumentamos el numero de paquetes. Esto nos servirá para comprobar futuras pérdidas
		npackets+=1
		#Truncamos el tiempo de recepción a centésimas de milisegundos 
		#(o decenas de microsegundos, segun se quiera ver) y 32 bits
		#para poder calcular el OWD en la misma base en que está eñ tiempo
		#de envío del paquete
		reception_time_trunc=int(reception_time*DECENASMICROSECS)&B_MASK

		print ('Retardo instantaneo en un sentido(s): ',(reception_time_trunc-send_time_trunc)/DECENASMICROSECS)

		#Si tenemos paquetes entonces calculamos los datos por cada paquete
		if npackets >1:
			Bw_inst = (((len(data)+Cabeceras)*8)/(lista_tiempos[-1] - lista_tiempos[-2])) /1000000 # t(n) - t(n-1)  Cabecera ya incluye RTP
			# Almacenamos los anchos de banda individuales en una lista
			lista_bw.append(Bw_inst)             
			print('Ancho de banda instantaneo(Mb/s): ',Bw_inst)                                                         
			Delay_inst = (reception_time_trunc - send_time_trunc)/100000
			lista_delay.append(Delay_inst)
			len_paq=len(data)
			print('Retardo instantaneo(s): ',Delay_inst)

	# Hallamos los datos pedidos mediante las formulas y las listas generados arriba
	Bw_average = ((npackets - 1)* ((len_paq+Cabeceras)*8) / (lista_tiempos[-1] - lista_tiempos[0])) /1000000 # tf-t0
	Bw_max = max(lista_bw)
	Bw_min = min(lista_bw)
	Delay_average = sum(lista_delay)/len(lista_delay)
	Delay_max = max(lista_delay)
	Delay_min = min(lista_delay)

	# Mostramos por pantalla 
	print('Ancho de banda medio(Mb/s): ',Bw_average)
	print('Ancho de banda maximo(Mb/s): ', Bw_max)
	print('Ancho de banda minimo(Mb/s): ', Bw_min)
	print('Retardo medio(s): ',Delay_average)
	print('Retardo maximo(s): ',Delay_max)
	print('Retardo minimo(s): ',Delay_min)

	#################################################################################
	packetLoss= (trainLength - npackets)/trainLength # para pasarlo a tanto por ciento
	print('Perdida de paquetes(%): ',packetLoss)
	jitter = statistics.pstdev(lista_delay)
	print('Variación del retardo(s): ',jitter)
    






