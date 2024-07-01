import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import asyncio
import websockets
import json


def iniciar_http():
    server_address = ('0.0.0.0', 8080) 
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("Servidor HTTP rodando na porta 8080...")
    httpd.serve_forever()


thread_http = threading.Thread(target=iniciar_http)
thread_http.start()


def iniciar_rpc():
    from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)

    server = SimpleXMLRPCServer(('0.0.0.0', 8000), requestHandler=RequestHandler)  
    server.register_introspection_functions()

    usuarios = {}
    votacoes = {}

    def registrar_usuario(nome, senha):
        if nome in usuarios:
            return False
        usuarios[nome] = senha
        return True

    def autenticar_usuario(nome, senha):
        return usuarios.get(nome) == senha

    def criar_votacao(votacao_id):
        if votacao_id in votacoes:
            return False
        votacoes[votacao_id] = {}
        return True

    def recuperar_historico(votacao_id):
        return votacoes.get(votacao_id, {})

    server.register_function(registrar_usuario, 'registrar_usuario')
    server.register_function(autenticar_usuario, 'autenticar_usuario')
    server.register_function(criar_votacao, 'criar_votacao')
    server.register_function(recuperar_historico, 'recuperar_historico')

    print("Servidor RPC rodando na porta 8000...")
    server.serve_forever()


thread_rpc = threading.Thread(target=iniciar_rpc)
thread_rpc.start()


clientes = set()


votos = []  

async def handler(websocket, path):
    print(f"Nova conexão: {path}")
    clientes.add(websocket)
    try:
        
        resultado = {
            'resultados': {
                'pessoa1': {
                    'votos': sum(1 for voto in votos if voto[1] == 'pessoa1'),
                    'nomes': [voto[0] for voto in votos if voto[1] == 'pessoa1']
                },
                'pessoa2': {
                    'votos': sum(1 for voto in votos if voto[1] == 'pessoa2'),
                    'nomes': [voto[0] for voto in votos if voto[1] == 'pessoa2']
                }
            }
        }
        await websocket.send(json.dumps(resultado))
        
        async for message in websocket:
            print(f"Mensagem recebida: {message}")
            data = json.loads(message)
            acao = data.get('acao')
            if acao == 'votar':
                nome = data['nome']
                opcao = data['opcao']
                if opcao in ['pessoa1', 'pessoa2']:
                    votos.append((nome, opcao))
                    print(f"Novo voto: {nome} votou em {opcao}")

                    
                    resultado = {
                        'resultados': {
                            'pessoa1': {
                                'votos': sum(1 for voto in votos if voto[1] == 'pessoa1'),
                                'nomes': [voto[0] for voto in votos if voto[1] == 'pessoa1']
                            },
                            'pessoa2': {
                                'votos': sum(1 for voto in votos if voto[1] == 'pessoa2'),
                                'nomes': [voto[0] for voto in votos if voto[1] == 'pessoa2']
                            }
                        }
                    }
                    
                    for cliente in clientes:
                        await cliente.send(json.dumps(resultado))
                else:
                    print(f"Opção {opcao} não válida")
            else:
                print(f"Ação {acao} não reconhecida")
    finally:
        print(f"Conexão fechada: {path}")
        clientes.remove(websocket)

async def start_server():
    async with websockets.serve(handler, "0.0.0.0", 8765):  
        print("Servidor de Votação rodando na porta 8765...")
        await asyncio.Future()  


thread_ws = threading.Thread(target=asyncio.run, args=(start_server(),))
thread_ws.start()