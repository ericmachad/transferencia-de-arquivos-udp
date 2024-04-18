import random
import socket
import hashlib

def calculate_sha256(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.digest()

def simulacao_perda_pacote(taxa_perda_de_pacote):
    return random.random() > taxa_perda_de_pacote

IP_Servidor = 'localhost'
Porta_Servidor = 45874
taxa_perda_de_pacote = 0.1
TAMANHO_PACOTE = 4096
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.settimeout(10)
TIMEOUT = 5
try:
    while True:
        try:
            print("Para solicitar um arquivo do sistema digite o nome do arquivo")
            nome_arquivo = input()
            request = f"GET /{nome_arquivo}"
            udp.sendto(request.encode(), (IP_Servidor, Porta_Servidor))     
            pacote = 1

            pacotes_recebidos = {}  #  armazenamento de pacotes recebidos

            while True:
                try:
                    dados_com_sha256, server_address = udp.recvfrom(TAMANHO_PACOTE + 32)  # 32 bytes para o hash SHA256
                except socket.timeout:
                    print("Tempo limite de recepção atingido. Encerrando a conexão.")
                    break

                if dados_com_sha256 == b'FINAL':
                    print("Todos os pacotes foram recebidos.")
                    break
                if dados_com_sha256 == b'Arquivo nao encontrado':
                    print("Arquivo nao encontrado")
                    break
                
                ler_buffer = dados_com_sha256[:-32]  
                sha256_received = dados_com_sha256[-32:]
                sha256_calculated = calculate_sha256(ler_buffer)
                if sha256_received == sha256_calculated:
                    if simulacao_perda_pacote(taxa_perda_de_pacote):
                        print(f"Pacote {pacote}: recebido {len(ler_buffer)} bytes do servidor {IP_Servidor}:{Porta_Servidor}")
                        pacotes_recebidos[pacote] = ler_buffer  # Armazenar pacote
                        udp.sendto(f"ACK {pacote}".encode(), (IP_Servidor, Porta_Servidor))  # Enviar ACK
                        pacote += 1
                    else:
                        print(f"Pacote {pacote} perdido. Solicitando retransmissão.") 
                        udp.sendto(f"NACK {pacote}".encode(), (IP_Servidor, Porta_Servidor))  # Enviar NACK
                else:
                    print(f"Erro de SHA256! Dados corrompidos no pacote {pacote}. Solicitando retransmissão.") 
                    udp.sendto(f"NACK {pacote}".encode(), (IP_Servidor, Porta_Servidor))  # Enviar NACK

            with open(nome_arquivo, "wb") as arquivo:
                for i in sorted(pacotes_recebidos.keys()):
                    arquivo.write(pacotes_recebidos[i])

        except Exception as e:
            print(f"Ocorreu um erro: {e}")

except KeyboardInterrupt:
    print("Cliente encerrado pelo usuário")
