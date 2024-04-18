import socket
import hashlib

def calcula_sha256(data):
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.digest()

HOST = 'localhost'
PORT = 45874
TAMANHO_JANELA = 5
TAMANHO_PACOTE = 4096

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind((HOST, PORT))
print(f"Servidor rodando na porta{PORT} e no host {HOST}")
udp.settimeout(30)

try:
    while True:     
        request, endereco_cliente = udp.recvfrom(TAMANHO_PACOTE)
        request = request.decode()

        if request.startswith("GET"):
            nome_arquivo = request.split()[1][1:]
            try: 
                with open(nome_arquivo, "rb") as arquivo:
                    pacote = 1
                    janela_deslizante = {}
                    while True:
                        ler_buffer = arquivo.read(TAMANHO_PACOTE)
                        if not ler_buffer:
                            break
                        checksum = calcula_sha256(ler_buffer)
                        janela_deslizante[pacote] = (ler_buffer, checksum)
                        pacote += 1

                    # Enviar pacotes e reenviar os não confirmados
                    base = 1
                    prox_numero_sequencia = 1
                    while base <= len(janela_deslizante):
                        while prox_numero_sequencia < base + TAMANHO_JANELA and prox_numero_sequencia <= len(janela_deslizante):
                            data, sha256_hash = janela_deslizante[prox_numero_sequencia]
                            udp.sendto(data + sha256_hash, endereco_cliente)
                            print(f"Pacote {prox_numero_sequencia}: enviado {len(data)} bytes para o cliente {endereco_cliente}")
                            prox_numero_sequencia += 1
                        try:
                            ack, _ = udp.recvfrom(TAMANHO_PACOTE)
                            ack = ack.decode()
                            if ack.startswith("ACK"):
                                ack_num = int(ack.split()[1])
                                base = ack_num + 1
                            elif ack.startswith("NACK"):
                                nack_num = int(ack.split()[1])
                                print(f"NACK recebido para o pacote {nack_num}. Reenviando...")
                                data, sha256_hash = janela_deslizante[nack_num]
                                udp.sendto(data + sha256_hash, endereco_cliente)
                                print(f'pacote {nack_num} reenviado {len(data)} para {endereco_cliente}')
                        except socket.timeout:
                            print(f"Timeout ao aguardar ACK para o pacote {base}. Reenviando...")
                            prox_numero_sequencia = base                   

                    # Enviar pacote de finalização
                    pacote_final = "FINAL".encode()
                    udp.sendto(pacote_final, endereco_cliente)
                    
                    print(f"Arquivo de {pacote - 1} pacotes enviado para o cliente {endereco_cliente}")   
            except FileNotFoundError:
                print("Erro ao localizar arquivo")
                erro = "Arquivo nao encontrado"
                udp.sendto(erro.encode(), endereco_cliente)
except KeyboardInterrupt:
    print("Servidor encerrado pelo usuário")
finally:
    udp.close()
