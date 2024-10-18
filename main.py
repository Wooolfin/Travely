from flask import Flask, render_template, redirect, request, session
import mysql.connector
import boto3

from werkzeug.utils import secure_filename

import os
import datetime as dt
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

aws_access_key = 'SUA CHAVE TOKEN'
aws_secret_access_key = '/SUA CHAVE TOKEN '
bucket_name = 'travely-turismo'

app = Flask(__name__)
app.secret_key = "travely"

conexaoDB = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="Trevely"
)

s3_client = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key
)

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salvando as credenciais no arquivo token.json
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def verifica_sessao():
    return "login" in session and session['login']

def buscar_passeios_por_nome(event_name):
    cursorDB = conexaoDB.cursor()
    comandoSQL = f'''
        SELECT 
            p.idPasseio,
            p.nome AS nomePasseio,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome AS categoria,
            p.descricaoPasseio
        FROM 
            agendamentos p
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        WHERE 
            p.nome = %s;
    '''
    cursorDB.execute(comandoSQL, (event_name,))
    passeios = cursorDB.fetchall()
    cursorDB.close()
    return passeios

@app.route('/')
def home():
    cursorDB = conexaoDB.cursor()
    consultaAgendamentos = '''
    SELECT 
        ag.idAgendamento,
        ag.event_id,
        p.idPasseio,
        p.nome AS nomePasseio,
        p.estadoPasseio,
        p.cidadePasseio,
        p.bairroEndPasseio,
        p.valor,
        c.nome AS nomeCategoria,
        p.descricaoPasseio,
        ag.qtdMaxTur,
        ag.dataAgendamento,
        ag.horaAgendamento,
        ag.duracaoAgendamento,
        img.caminhoS3
    FROM 
        agendamento ag
    JOIN 
        passeio p ON ag.idPasseio = p.idPasseio
    JOIN 
        categoria c ON p.categoria = c.idCategoria
    LEFT JOIN 
        imagens img ON p.idPasseio = img.idPasseio;
    '''
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(consultaAgendamentos)
    agendamentos = cursorDB.fetchall()

    tipo_usuario = session.get('tipo')

    return render_template("home.html", agendamentos=agendamentos, tipo=tipo_usuario)

@app.route("/cadastrarGuia", methods=['POST'])
def cadGuia():
    creds = main()

    nome = request.form['nome']
    cpf_cnpj = request.form['cpf_cnpj']
    telefone = request.form['telefone']
    data_nascimento = request.form['data_nascimento']
    cep = request.form['cep']
    ruaEndUser = request.form['ruaEndUser']
    bairroEndUser = request.form['bairroEndUser']
    numEndUser = request.form['numEndUser']
    email = request.form['email']
    senha = request.form['senha']
    cadastur = request.form['cadastur']
    chavePix = request.form['chavePix']

    tipo = True
    # Inserir na tabela `usuario`
    comandoSQL_usuario = """
        INSERT INTO usuario (nome, cpfCnpj, numTelefone, dataNasc, cepEndUser, ruaEndUser, bairroEndUser, numEndUser, email, senha, tipo) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    valores_usuario = (nome, cpf_cnpj, telefone, data_nascimento, cep, ruaEndUser, bairroEndUser, numEndUser, email, senha, tipo)

    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL_usuario, valores_usuario)
    conexaoDB.commit()

    id_usuario = cursorDB.lastrowid

    try:
        service = build("calendar", "v3", credentials=creds)
        calendar = {
            'summary': f'{ id_usuario } - { nome }',
            'timeZone': 'America/Los_Angeles'
        }

        created_calendar = service.calendars().insert(body=calendar).execute()
        
        calendar_id = created_calendar['id']  # Pegue o id do calendário criado 
    except HttpError as error:
        print(f"An error occurred: {error}")

    # Inserir na tabela `adGuia` utilizando o id_usuario
    comandoSQL_adGuia = """
        INSERT INTO adGuia (cadastur, chavePix, idUsuario, calendar_id) 
        VALUES (%s, %s, %s, %s)
    """
    valores_adGuia = (cadastur, chavePix, id_usuario, calendar_id)
    cursorDB.execute(comandoSQL_adGuia, valores_adGuia)
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/adm')

@app.route('/adm')
def adm():
    cursorDB = conexaoDB.cursor()

    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    
    cursorDB = conexaoDB.cursor()

    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão
    tipo_usuario = session.get('tipo')

    comandoSQL1 = f'SELECT nome FROM usuario WHERE idUsuario = {idUsuario}'
    cursorDB.execute(comandoSQL1)
    nomeGuia = cursorDB.fetchone()


    comandoSQL = f'SELECT * FROM passeio WHERE idGuia = {idUsuario} ORDER BY idPasseio DESC '
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeios = cursorDB.fetchall()
    cursorDB.close()
    return render_template("adm.html",passeios=passeios, tipo=tipo_usuario , nomeGuia=nomeGuia)

@app.route("/cadPasseio", methods=['POST'])
def cadpasseio():
    nome = request.form['nome']
    estadoPasseio = request.form['estadoPasseio']
    cidadePasseio = request.form['cidadePasseio']
    bairroEndPasseio = request.form['bairroEndPasseio']
    valor = request.form['valor']
    categoria = request.form['categoria']
    descricaoPasseio = request.form['descricao']
    
    idGuia = session.get('idUsuario')  

    if idGuia is None:
        return render_template('error.html', msg="ID do Guia não fornecido ou usuário não autenticado.")
    
    if 'imagem' not in request.files:
        return render_template('error.html', msg="Nenhuma imagem fornecida.")

    imagem = request.files['imagem']

    if imagem.filename == '':
        return render_template('error.html', msg="Nenhum arquivo selecionado.")

    if imagem:
        nome_arquivo = secure_filename(imagem.filename)
        nome_objeto = f'imagens/{nome_arquivo}'

        try:
            s3_client.upload_fileobj(imagem, bucket_name, nome_objeto)
            imagem_url = f"https://{bucket_name}.s3.amazonaws.com/{nome_objeto}"
        except Exception as e:
            print(f"Erro ao fazer upload: {str(e)}")
            return render_template('error.html', msg="Erro ao fazer upload da imagem para o S3.")
    
    comandoSQL = '''
    INSERT INTO passeio (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, valor, categoria, descricaoPasseio, idGuia)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    valores = (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, valor, categoria, descricaoPasseio, idGuia)

    try:
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL, valores)
        idPasseio = cursorDB.lastrowid 

        comandoSQL_imagem = '''
        INSERT INTO imagens (nomeArquivo, caminhoS3, idPasseio)
        VALUES (%s, %s, %s)
        '''
        valores_imagem = (nome_arquivo, imagem_url, idPasseio)
        cursorDB.execute(comandoSQL_imagem, valores_imagem)

        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    return redirect('/adm')


@app.route('/agendarPasseio/<int:id>', methods=['POST'])
def agendarPasseio(id):
    creds = main()

    service = build("calendar", "v3", credentials=creds)
    idUsuario = session.get('idUsuario')

    dataAgendamento = request.form['dataAgendamento']
    horaAgendamento = request.form['horaAgendamento']
    duracao = int(request.form['duracao'])
    qtdMaxTur = request.form['qtdMaxTur']

    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeio = cursorDB.fetchone()

    hora_final = (dt.datetime.strptime(f'{dataAgendamento} {horaAgendamento}', '%Y-%m-%d %H:%M')
                  + dt.timedelta(hours=duracao)).strftime('%Y-%m-%dT%H:%M:%S')

    parametrosApi = '''
    SELECT g.calendar_id
    FROM adGuia g
    JOIN passeio p ON g.idUsuario = p.idGuia
    WHERE p.idPasseio = %s;
    '''
    cursorDB.execute(parametrosApi, (passeio[0],))
    api = cursorDB.fetchone()

    try:
        calendar_id = api[0]
        evento = {
        'summary': f'{passeio[1]}',
        'location': f'{passeio[4]} - {passeio[3]}/{passeio[2]}',  
        'description': 'Turistas:',
        'start': {
            'dateTime': f'{dataAgendamento}T{horaAgendamento}:00',
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': hora_final,
            'timeZone': 'America/Sao_Paulo',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

        event = service.events().insert(calendarId=calendar_id, body=evento).execute()
        event_id = event['id']
    except HttpError as error:
        print(f"Erro ao criar evento: {error}")

    cursorDB = conexaoDB.cursor()
    comandoInsert = '''
        INSERT INTO agendamento (qtdMaxTur, dataAgendamento, horaAgendamento, idPasseio, idGuiaAg, duracaoAgendamento, event_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    '''
    cursorDB.execute(comandoInsert, (qtdMaxTur, dataAgendamento, horaAgendamento, id, idUsuario, duracao, event_id))
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/home')

@app.route("/cadastrar", methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def handle_wrong_methods():
    return redirect('/') 

@app.route("/cadpasseio")
def novopasseio():
    tipo_usuario = session.get('tipo')
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('login.html')
    
    return render_template("cadPasseio.html",tipo=tipo_usuario)

@app.route('/login')
def login():
    if not verifica_sessao(): 
        return render_template('/login.html')
    else: 
        return redirect("/adm")

@app.route('/redirecionarGuia', methods=['GET'])
def redirecionar_guia():
    return redirect('/cadGuia')

@app.route('/cadGuia')
def cad_guia():
    return render_template('cadGuia.html')

@app.route('/redirecionarTurista', methods=['GET'])
def redirecionar_turista():
    return redirect('/cadTurista')

@app.route('/cadTurista')
def cad_turista():
    return render_template('cadTurista.html')

@app.route('/logout')
def logout():
    if verifica_sessao():
        session.clear() #limpa a sessão 
    
    return redirect('/') #retorno pra home

@app.route("/acesso", methods=['POST'])
def acesso():
    usuario_informado = request.form['usuario']
    senha_informado = request.form['senha']

    # Conectar ao banco de dados
    cursorDB = conexaoDB.cursor()

    # Consultar o banco de dados para verificar se o email e a senha estão corretos
    comandoSQL = "SELECT * FROM usuario WHERE email = %s AND senha = %s"
    cursorDB.execute(comandoSQL, (usuario_informado, senha_informado))
    resultado = cursorDB.fetchone()  # Busca o idUsuario associado ao usuário
    cursorDB.close()

    # Se encontrou um usuário com as credenciais fornecidas
    if resultado:
        session['login'] = True  # Autoriza a entrada
        session['idUsuario'] = resultado[0]  # Armazena o idUsuario na sessão
        if resultado[11]:  # Aqui, resultado[1] é o campo booleano "tipo"
            session['tipo'] = True
        else:
            session['tipo'] = False

        return redirect('/adm')

    else:
        # Caso contrário, renderiza a página de login com uma mensagem de erro
        return render_template('login.html', msg="Usuário e senha estão incorretos")

@app.route('/deletar/<int:id>')
def excluir(id):
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    
    comandoSQL = f'DELETE FROM agendamento WHERE idAgendamento = {id}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/adm')

@app.route('/detalhes/<int:id>', methods=['GET', 'POST'])
def detalhes(id):   
    cursorDB = conexaoDB.cursor()

    if request.method == 'POST':
        qtdTurAg = int(request.form.get('qtdTurAg', 1))
        
        pesquisaValor = f'SELECT p.valor FROM agendamento a JOIN passeio p ON a.idPasseio = p.idPasseio WHERE a.idAgendamento = {id};'
        cursorDB.execute(pesquisaValor)
        valor_passeio = cursorDB.fetchone()[0]

        total = valor_passeio * qtdTurAg
    else:
        pesquisaValor = f'SELECT p.valor FROM agendamento a JOIN passeio p ON a.idPasseio = p.idPasseio WHERE a.idAgendamento = {id};'
        cursorDB.execute(pesquisaValor)
        valor_passeio = cursorDB.fetchone()[0]
        total = valor_passeio
        qtdTurAg = 1

    pesquisaAgendamento = f'''SELECT 
        ag.idAgendamento,
        ag.event_id,
        p.idPasseio,
        p.nome AS nomePasseio,
        p.estadoPasseio,
        p.cidadePasseio,
        p.bairroEndPasseio,
        p.valor,
        c.nome AS nomeCategoria,
        p.descricaoPasseio,
        ag.qtdMaxTur,
        ag.dataAgendamento,
        ag.horaAgendamento,
        ag.duracaoAgendamento,
        ag.idGuiaAg
    FROM 
        agendamento ag
    JOIN 
        passeio p ON ag.idPasseio = p.idPasseio
    JOIN 
        categoria c ON p.categoria = c.idCategoria 
    WHERE 
        idAgendamento = {id};'''
    cursorDB.execute(pesquisaAgendamento)
    agendamento = cursorDB.fetchone()

    pesquisaGuia = f'SELECT * FROM usuario WHERE idUsuario = { agendamento[14]}'
    cursorDB.execute(pesquisaGuia)
    dadosGuia = cursorDB.fetchone()
    
    # Informações para o carrossel de outros passeios
    pesquisaCarrosel = '''SELECT 
        ag.idAgendamento,
        ag.event_id,
        p.idPasseio,
        p.nome AS nomePasseio,
        p.estadoPasseio,
        p.cidadePasseio,
        p.bairroEndPasseio,
        p.valor,
        c.nome AS nomeCategoria,
        p.descricaoPasseio,
        ag.qtdMaxTur,
        ag.dataAgendamento,
        ag.horaAgendamento,
        ag.duracaoAgendamento
    FROM 
        agendamento ag
    JOIN 
        passeio p ON ag.idPasseio = p.idPasseio
    JOIN 
        categoria c ON p.categoria = c.idCategoria;'''
    cursorDB.execute(pesquisaCarrosel)
    pCarrossel = cursorDB.fetchall()

    tipo_usuario = session.get('tipo')
    cursorDB.close()

    # Renderizando o template com todos os dados necessários
    return render_template("detalhes.html", agendamento=agendamento, pCarrossel=pCarrossel, tipo=tipo_usuario, guia=dadosGuia, total=total, qtdTurAg=qtdTurAg,valor=valor_passeio, id=id)

@app.route("/cadastrarTurista", methods=['POST'])
def cadTurista():
    nome = request.form['nome']
    cpf_cnpj = request.form['cpf_cnpj']
    telefone = request.form['telefone']
    data_nascimento = request.form['data_nascimento']
    cep = request.form['cep']
    ruaEndUser = request.form['ruaEndUser']
    bairroEndUser = request.form['bairroEndUser']
    numEndUser = request.form['numEndUser']
    email = request.form['email']
    senha = request.form['senha']

    tipo = False

    # Inserir na tabela `usuario`
    comandoSQL_usuario = """
        INSERT INTO usuario (nome, cpfCnpj, numTelefone, dataNasc, cepEndUser, ruaEndUser, bairroEndUser, numEndUser, email, senha, tipo) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    valores_usuario = (nome, cpf_cnpj, telefone, data_nascimento, cep, ruaEndUser, bairroEndUser, numEndUser, email, senha, tipo)

    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL_usuario, valores_usuario)
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/home')

@app.route("/confirmaPag/<int:id>", methods=['GET', 'POST'])
def confirmaPag(id):
    cursorDB = conexaoDB.cursor()

    if not verifica_sessao(): 
        return render_template('/login.html')
    
    pesquisaAgendamento = f'''SELECT 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome AS nomePasseio,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome AS nomeCategoria,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            ag.idGuiaAg
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            categoria c ON p.categoria = c.idCategoria 
        WHERE 
            idAgendamento = {id};'''
    cursorDB.execute(pesquisaAgendamento)
    agendamento = cursorDB.fetchone()   
    
    if request.method == 'POST':
        qtdTurAg = int(request.form.get('qtdTurAg', 1))
        total = agendamento[7] * qtdTurAg

    else:
        comandoSQL = f'SELECT p.valor FROM agendamento a JOIN passeio p ON a.idPasseio = p.idPasseio WHERE a.idAgendamento = {id};'
        cursorDB.execute(comandoSQL)
        valor_passeio = cursorDB.fetchone()[0]
        total = valor_passeio
        qtdTurAg = 1
    
    
    cursorDB.close()
    return render_template("confirmaPag.html", agendamento=agendamento, total=total, qtdTurAg=qtdTurAg)

@app.route("/confirmarGrupoPasseio/<int:id>/<int:qtdTurAg>", methods=['POST'])
def confirmarGrupoPasseio(id, qtdTurAg):
    creds = main()
    cursorDB = conexaoDB.cursor()

    service = build("calendar", "v3", credentials=creds)

    idTurista = session.get('idUsuario')  

    pago = 0

    pesquisaGrupoPasseio = f'''
    SELECT ag.idGuiaAg, p.valor
    FROM agendamento ag 
    JOIN passeio p ON ag.idPasseio = p.idPasseio 
    WHERE ag.idAgendamento = {id};
    '''
    cursorDB.execute(pesquisaGrupoPasseio)
    idGuiaAg_valorPasseio = cursorDB.fetchone()
    total = idGuiaAg_valorPasseio[1] * qtdTurAg 

    insertGrupoPasseio = '''
    INSERT INTO grupopasseios (idAgendamento, idTuristaAg, idGuiaAg, qtdTurGpAgendamento, pago, vTotal)
    VALUES (%s, %s, %s, %s, %s, %s);
    '''
    cursorDB.execute(insertGrupoPasseio, (id, idTurista, idGuiaAg_valorPasseio[0], qtdTurAg, int(pago), total))
    conexaoDB.commit()


    pesquisasNomeTur = 'SELECT nome FROM usuario WHERE idUsuario = %s'
    cursorDB.execute(pesquisasNomeTur, (idTurista,))
    nomeTur = cursorDB.fetchone()

    parametrosApi = f'''
        SELECT 
            ag.event_id, 
            g.calendar_id
        FROM 
            agendamento ag
        JOIN 
            adGuia g ON ag.idGuiaAg = g.idUsuario
        WHERE 
            ag.idAgendamento = {id};
    '''
    cursorDB.execute(parametrosApi)
    api = cursorDB.fetchone()

    try:
        eventDescricaoAnt = service.events().get(calendarId=api[1], eventId=api[0]).execute()

        descricao_atual = eventDescricaoAnt.get('description', '')

        nova_linha = f'\n{nomeTur[0]} - {qtdTurAg} x {idGuiaAg_valorPasseio[1]} = {total}'
        descricao_atualizada = descricao_atual + nova_linha

        event_patch = {
            'description': descricao_atualizada,
        }

        service.events().patch(
            calendarId=api[1], 
            eventId=api[0], 
            body=event_patch
        ).execute()

    except Exception as e:
        return f"Erro ao atualizar evento: {str(e)}"
    
    cursorDB.close()
    return redirect("/home")

@app.route('/listaPasseios')
def lista():
    cursorDB = conexaoDB.cursor()
    
    if not verifica_sessao(): 
        return render_template('/login.html')

    tipo_usuario = session.get('tipo')
    cursorDB = conexaoDB.cursor()
    consultaAgendamentos = '''
        SELECT 
            ag.idAgendamento,
            ag.event_id,
            p.idPasseio,
            p.nome AS nomePasseio,
            p.estadoPasseio,
            p.cidadePasseio,
            p.bairroEndPasseio,
            p.valor,
            c.nome AS nomeCategoria,
            p.descricaoPasseio,
            ag.qtdMaxTur,
            ag.dataAgendamento,
            ag.horaAgendamento,
            ag.duracaoAgendamento,
            u.nome AS guiaNome
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            categoria c ON p.categoria = c.idCategoria
        JOIN 
            usuario u ON p.idGuia = u.idUsuario
    '''
    cursorDB.execute(consultaAgendamentos)
    agendamentos = cursorDB.fetchall()

    agendamentos_com_grupos = []

    for agendamento in agendamentos:
        idAgendamento = agendamento[0]
        cursorDB.execute('''
            SELECT 
                u.nome, 
                gp.qtdTurGpAgendamento, 
                gp.pago,
                gp.idGrupoPasseios
            FROM 
                grupoPasseios gp
            JOIN 
                usuario u ON gp.idTuristaAg = u.idUsuario
            WHERE 
                gp.idAgendamento = %s;
        ''', (idAgendamento,))
        grupos = cursorDB.fetchall()
        agendamentos_com_grupos.append({
            'agendamento': agendamento,
            'grupos': grupos
        })

    cursorDB.close()

    return render_template("listaPasseios.html", agendamentos_com_grupos=agendamentos_com_grupos, tipo=tipo_usuario)

@app.route("/<int:id>/pago", methods=['POST'])
def altPago(id):
    if not verifica_sessao(): 
        return render_template('/login.html')
    
    tipo_usuario = session.get('tipo')

    comandoSQL = 'UPDATE grupoPasseios SET pago = TRUE WHERE idGrupoPasseios = %s'
    
    try:
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL, (id,))
        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    
    return redirect('/listaPasseios')

# --------------------------------------------------------
# --------------------------------------------------------
# --------------------------------------------------------



@app.route('/editPasseio/<int:id>', methods=['GET'])
def editarPasseio(id):
    if not verifica_sessao(): 
        return render_template('/login.html')
    
    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeios = cursorDB.fetchone()
    cursorDB.close()
    return render_template('editPasseio.html', passeio=passeios)

@app.route('/<int:id>/editadoPasseio', methods=['POST'])
def editadoPasseio(id):
    comandoSQL = f"SELECT * FROM passeio WHERE idPasseio = {id}"
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeio_atual = cursorDB.fetchone()

    nome = request.form['nome'] if request.form['nome'] else passeio_atual[1]
    estadoPasseio = request.form['estadoPasseio'] if request.form['estadoPasseio'] else passeio_atual[2]
    cidadePasseio = request.form['cidadePasseio'] if request.form['cidadePasseio'] else passeio_atual[3]
    bairroEndPasseio = request.form['bairroEndPasseio'] if request.form['bairroEndPasseio'] else passeio_atual[4]
    qtdPessoas = request.form['qtdPessoas'] if request.form['qtdPessoas'] else passeio_atual[5]
    valor = request.form['valor'] if request.form['valor'] else passeio_atual[6]
    tempoPasseio = request.form['tempoPasseio'] if request.form['tempoPasseio'] else passeio_atual[7]
    descricaoPasseio = request.form['descricao'] if request.form['descricao'] else passeio_atual[9]

    comandoSQL_update = '''
    UPDATE passeio 
    SET nome = %s, estadoPasseio = %s, cidadePasseio = %s, bairroEndPasseio = %s, qtdPessoas = %s, valor = %s, tempoPasseio = %s,  descricaoPasseio = %s
    WHERE idPasseio = %s
    '''
    valores = (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, qtdPessoas, valor, tempoPasseio, descricaoPasseio, id)

    try:
        cursorDB.execute(comandoSQL_update, valores)
        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    
    return redirect('/adm')

@app.errorhandler(405)
def erro405(error):
    return redirect("/")

@app.errorhandler(404)
def erro404(error):
    return redirect("/")

app.run(host='0.0.0.0', port=5000, debug = True)