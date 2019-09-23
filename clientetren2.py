
import sys
import socket
import struct
import time
import statistics

# Definimos macros
MAX_ETHERNET_DATA=1500
MIN_ETHERNET_DATA=46
ETH_HDR_SIZE=14+4+8+12 # MAC header + CRC + Preamble + Interframe
IP_HDR_SIZE=20
UDP_HDR_SIZE=8
RTP_HDR_SIZE=12

B_MASK=0xFFFFFFFF
DECENASMICROSECS=100000

# Esta linea hace que el programa empiece a ejecutarse aqui ya que si no la ponemos empieza a ejecutarse desde la primera linea de arriba del todo hasta abajo
if __name__ == "__main__":
	# Si ponemos menos de cinco argumentos (0 al 4) nos da error
	if len(sys.argv)!=5 and len(sys.argv)!=6:
		print ('Error en los argumentos:\npython clienteTren.py ip_destino puerto_destino longitud_tren longitud_datos tasa_binaria (Kb/s)\n')
		exit(-1)
	
	# Leemos los valores por argumento y los asignamos a una variable
	dstIP=sys.argv[1]
	dstPort=int(sys.argv[2])
	addr=(dstIP,dstPort)
	trainLength=int(sys.argv[3])
	dataLength=int(sys.argv[4])
	
	
	if dataLength+IP_HDR_SIZE+UDP_HDR_SIZE+RTP_HDR_SIZE>MAX_ETHERNET_DATA or dataLength+IP_HDR_SIZE+UDP_HDR_SIZE+RTP_HDR_SIZE<MIN_ETHERNET_DATA :
		# Se controla si la trama sería inferior al tamaño minimo, o bien tan grande que habría que fragmentarla, estropeando la medida
		print('Tamaño de datos incorrecto')
		exit(0)
	L=0
	# Comprobamos si estamos en localhost o no y en función de eso añadimos la cabecera Ethernet
	if dstIP=="127.0.0.1":
		L=(dataLength+IP_HDR_SIZE+UDP_HDR_SIZE+RTP_HDR_SIZE)*8
	else:
		L=(dataLength+IP_HDR_SIZE+UDP_HDR_SIZE+RTP_HDR_SIZE+ETH_HDR_SIZE)*8

	
	sock_send= socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
	#generar un array de datos de longitud dataLength con el caracter 0 
	data=('0'*(dataLength)).encode()
	seq_number=0

	tespera=0
	# Si hay un sexto argumento (tasa_binaria) entonces lo pasamos a bit/s y calculamos la espera a introducir para que la red vaya a la velocidad que queremos
	if len(sys.argv)==6:
		tasaBinaria=float(sys.argv[5])*1000 #lo pasamos a bits/s
		tespera=L/tasaBinaria
	for i in range(0,trainLength):
		#usamos la longitud del tren como identificador de fuente. De esta manera en destino podemos saber la
		#longitud original del tren. En el campo timestamp (32bits) sólo podemos enviar segundos y 
		#centésimas de milisegundos (o decenas de microsegundos, segun se quiera ver) truncados a 32bits
		message=struct.pack('!HHII',0x8014,seq_number, int(time.time()*DECENASMICROSECS)&B_MASK,trainLength)+data
		# Enviamos a través del socket, aumentamos el numero de secuencia e introducimos el retardo precalculado para la tasa binaria
		sock_send.sendto(message,addr)
		seq_number+=1
		time.sleep(tespera)


