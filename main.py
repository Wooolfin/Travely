from flask import Flask, render_template, redirect, request, session
import mysql.connector
#pip install mysql-connector-python BAIXAR - AJUDA A CONETAR MYSQL COM O PYTHON

#REDIRECT manda o user pra ROTA
#RENDER_TEMPLATE manda o user pra HTML CSS


conexaoDB = mysql.connector.connect(
    host="localhost",
    user="root",
    password="aluno",
    database="Trevely"
)

app = Flask(__name__)
app.secret_key = "travely" #session  nescessita da secret_key

#FUNÇÃO PARA VERIFICAR LOGIN
def verifica_sessao():
    if "login" in session and session ['login']: #verifica se a página está rodando com um login 
        return True
    else:
        return False #faz o controle de usuario/ para ele não acessar páginas pelo link 

#HOMEPAGE
@app.route('/')
def home():
    comandoSQL = 'SELECT * FROM passeio' #comando sql
    cursorDB = conexaoDB.cursor() #deixa conexao estavel
    cursorDB.execute(comandoSQL) #executa comando sql
    passeios = cursorDB.fetchall()#faz uma lista com os dados
    cursorDB.close()#fecha banco de dados
    tipo_usuario = session.get('tipo')

    return render_template("home.html", passeios=passeios, tipo=tipo_usuario)

#ROTA PARA ABRIR O FORMULÁRIO DE CADASTRO
@app.route("/cadpasseio")
def novopasseio():
    tipo_usuario = session.get('tipo')
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('login.html')
    
    return render_template("cadPasseio.html",tipo=tipo_usuario)

@app.route("/cadPasseio", methods=['POST'])
def cadpasseio():
    nome = request.form['nome']
    cepEndPasseio = request.form['cepEndPasseio']
    ruaEndPasseio = request.form['ruaEndPasseio']
    bairroEndPasseio = request.form['bairroEndPasseio']
    numEndPasseio = request.form['numEndPasseio']
    qtdPessoas = request.form['qtdPessoas']
    tempo = request.form['tempo']  # Supondo que seja no formato HH:MM:SS
    valor = request.form['valor']
    descricao = request.form['descricao']
    
    idUsuario = session.get('idUsuario')  # Recupera o idGuia da sessão

    if idUsuario is None:
        return render_template('error.html', msg="ID do Guia não fornecido ou usuário não autenticado.")
    
    # Query SQL ajustada para corresponder à estrutura da tabela
    comandoSQL = '''
    INSERT INTO passeio (nome, cepEndPasseio, ruaEndPasseio, bairroEndPasseio, numEndPasseio, qtdPessoas, valor, tempoPasseio, descricaoPasseio, idUsuario)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    valores = (nome, cepEndPasseio, ruaEndPasseio, bairroEndPasseio, numEndPasseio, qtdPessoas, valor, tempo, descricao, idUsuario)

    try:
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL, valores)
        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    
    return redirect('/adm')

#ROTA PARA PREVINIR QUE USER TENTE ENTRAR NA /CADASTRAR 
@app.route("/cadastrar", methods=['GET', 'PUT', 'DELETE', 'PATCH']) #POST grava info, GET pega info, PUT atualiza info, DELETE exclusão info, PATCH faz mudança parcial na info
def handle_wrong_methods():
    return redirect('/') # Trata todos os outros métodos, redirecionando para a página inicial (/).

#ROTA PARA ABRIR DETALHES DO PASSEIO
@app.route('/detalhes/<int:id>', methods=['GET']) #Pega o passeio que o user escolheu 
def detalhes(id):
    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}' #Seleciona o passeios em idpasseios / funciona como filtros de paginas, trazendo só oque foi selecionado 
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeio = cursorDB.fetchone() # fetchone apenas 1 valor
    cursorDB.close()
    tipo_usuario = session.get('tipo')
    return render_template("detalhes.html",passeio=passeio,tipo=tipo_usuario)

#ROTA PARA ABRIR CONFIRMÇÃO DE PAGAMENTO E FAZER AGENDAMENTO DO PASSEIO
@app.route("/<int:id>/cadAgendamento", methods=['POST'])
def cadAgendamento(id):
    comandoSQL1 = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL1)
    passeio = cursorDB.fetchone() # fetchone apenas 1 valor
    cursorDB.close()
    dataAg = request.form['dataAg']
    qtdTurAg = request.form['qtdTurAg']
    
    idUsuario = session.get('idUsuario')  # Recupera o idGuia da sessão
    pago = False
    

    if idUsuario is None:
        return render_template('error.html', msg="ID do Guia não fornecido ou usuário não autenticado.")
    
    # Query SQL ajustada para corresponder à estrutura da tabela
    comandoSQL = '''
    INSERT INTO agendamento (dataPasseio, qtdTurAgendamento, pago, idUsuario, idPasseio)
    VALUES (%s, %s, %s, %s, %s)
    '''
    valores = (dataAg, qtdTurAg, pago, idUsuario, passeio[0])

    try:
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL, valores)
        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    
    return redirect('/adm')

#ROTA DA PÁGINA ADMINISTRATIVA
@app.route('/adm')
def adm():
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    
    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão
    tipo_usuario = session.get('tipo')

    comandoSQL = f'SELECT * FROM passeio WHERE idUsuario = {idUsuario} ORDER BY idPasseio DESC '
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeios = cursorDB.fetchall()
    cursorDB.close()
    return render_template("adm.html",passeios=passeios, tipo=tipo_usuario )

#ROTA DA PÁGINA DE LOGIN
@app.route('/login')
def login():
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    else: 
        return redirect("/adm") #SE JÁ TIVER SESSÃO ATIVA NO SERVER, ELE MANDA PRA ADM #TCC- VAMOS TER QUE SEPARAR AQUI GUIA/TURISTA

#ROTA DA PÁGINA LISTA PASSEIO
@app.route('/listaPasseios')
def lista():
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')

    tipo_usuario = session.get('tipo')
    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão
    
    if tipo_usuario:
        comandoSQL = (
            f"SELECT ag.idAgendamento, ag.dataPasseio, ag.qtdTurAgendamento, ag.pago, ag.idUsuario, ag.idPasseio, "
            f"p.nome, p.cepEndPasseio, p.ruaEndPasseio, p.bairroEndPasseio, p.numEndPasseio, "
            f"p.qtdPessoas, p.valor, p.tempoPasseio, p.descricaoPasseio, p.idUsuario "
            f"FROM agendamento ag "
            f"JOIN passeio p ON ag.idPasseio = p.idPasseio "
            f"WHERE p.idUsuario = {idUsuario};"
        )
        cursorDB = conexaoDB.cursor()  # Deixa conexão estável
        cursorDB.execute(comandoSQL)  # Executa comando SQL
        agendamentos = cursorDB.fetchall()  # Faz uma lista com os dados
        cursorDB.close()  # Fecha banco de dados
        return render_template("listaPasseios.html", agendamentos=agendamentos, tipo=tipo_usuario)

    else:
        comandoSQL1 = (
            f"SELECT ag.idAgendamento, ag.dataPasseio, ag.qtdTurAgendamento, ag.pago, ag.idUsuario, ag.idPasseio, "
            f"p.nome, p.cepEndPasseio, p.ruaEndPasseio, p.bairroEndPasseio, p.numEndPasseio, "
            f"p.qtdPessoas, p.valor, p.tempoPasseio, p.descricaoPasseio, p.idUsuario "
            f"FROM agendamento ag "
            f"JOIN passeio p ON ag.idPasseio = p.idPasseio "
            f"WHERE ag.idUsuario = {idUsuario};"
        )
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL1)
        agendamentos = cursorDB.fetchall()
        cursorDB.close()
        return render_template("listaPasseios.html", agendamentos=agendamentos, tipo=tipo_usuario)

#ROTA PARA ABRIR CONFIRMÇÃO DE PAGAMENTO E FAZER AGENDAMENTO DO PASSEIO
@app.route("/<int:id>/pago", methods=['PUT'])
def altPago(id):
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    tipo_usuario = session.get('tipo')
    #PUXAR DADOS DO PASSEIO SELICIONADO
    comandoSQL = f'UPDATE agendamento SET pago = TRUE WHERE idAgendamento = {id}'
    
    try:
        cursorDB = conexaoDB.cursor()
        cursorDB.execute(comandoSQL)
        conexaoDB.commit()
    except mysql.connector.IntegrityError as err:
        print(f"Error: {err}")
        conexaoDB.rollback()
        return render_template('error.html', msg="Erro de integridade ao tentar cadastrar o passeio.")
    finally:
        cursorDB.close()
    return redirect('/home', tipo=tipo_usuario)
    


#REDIRECIONA PARA PAGINA GUIA
@app.route('/redirecionarGuia', methods=['GET'])
def redirecionar_guia():
    return redirect('/cadGuia')

@app.route('/cadGuia')
def cad_guia():
    return render_template('cadGuia.html')

#ROTA PARA RECEBER A POSTAGEM DO FORMULÁRIO DE CADASTRO GUIA
@app.route("/cadastrarGuia", methods=['POST'])
def cadGuia():
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

    # Inserir na tabela `adGuia` utilizando o id_usuario
    comandoSQL_adGuia = """
        INSERT INTO adGuia (cadastur, chavePix, idUsuario) 
        VALUES (%s, %s, %s)
    """
    valores_adGuia = (cadastur, chavePix, id_usuario)
    cursorDB.execute(comandoSQL_adGuia, valores_adGuia)
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/adm')

#ROTA PARA RECEBER A POSTAGEM DO FORMULÁRIO DE CADASTRO TURISTA
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

#REDIRECIONA PARA PAGINA TURISTA
@app.route('/redirecionarTurista', methods=['GET'])
def redirecionar_turista():
    return redirect('/cadTurista')

@app.route('/cadTurista')
def cad_turista():
    return render_template('cadTurista.html')

#ACESSO PAGINA ADMIN
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
  
#LOGOUT PAGINA ADMIN
@app.route('/logout')
def logout():
    if verifica_sessao():
        session.clear() #limpa a sessão 
    
    return redirect('/') #retorno pra home

#DELETAR PASSEIO
@app.route('/deletar/<int:id>')
def excluir(id):
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    
    comandoSQL = f'DELETE FROM passeio WHERE idPasseio = {id}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/adm')

#EDITAR PASSEIO
@app.route('/editPasseio/<int:id>', methods=['GET'])
def editarPasseio(id):
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    
    #PUXAR DADOS DO PASSEIO SELICIONADO
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
    cepEndPasseio = request.form['cepEndPasseio'] if request.form['cepEndPasseio'] else passeio_atual[2]
    ruaEndPasseio = request.form['ruaEndPasseio'] if request.form['ruaEndPasseio'] else passeio_atual[3]
    bairroEndPasseio = request.form['bairroEndPasseio'] if request.form['bairroEndPasseio'] else passeio_atual[4]
    numEndPasseio = request.form['numEndPasseio'] if request.form['numEndPasseio'] else passeio_atual[5]
    qtdPessoas = request.form['qtdPessoas'] if request.form['qtdPessoas'] else passeio_atual[6]
    tempoPasseio = request.form['tempo'] if request.form['tempo'] else passeio_atual[7]
    valor = request.form['valor'] if request.form['valor'] else passeio_atual[8]
    descricaoPasseio = request.form['descricao'] if request.form['descricao'] else passeio_atual[9]

    # Atualiza os dados do passeio no banco de dados
    comandoSQL_update = '''
    UPDATE passeio 
    SET nome = %s, cepEndPasseio = %s, ruaEndPasseio = %s, bairroEndPasseio = %s, numEndPasseio = %s, 
    qtdPessoas = %s, valor = %s, tempoPasseio = %s,  descricaoPasseio = %s
    WHERE idPasseio = %s
    '''
    valores = (nome, cepEndPasseio, ruaEndPasseio, bairroEndPasseio, numEndPasseio, qtdPessoas, valor, tempoPasseio, descricaoPasseio, id)

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

#SE USER TENTAR ACESSAR UMA ROTA NÃO AUTORIZADA 
@app.errorhandler(405)
def erro405(error):
    return redirect("/")

#SE USER TENTAR ACESSAR UMA ROTA QUE NÃO EXISTE 
@app.errorhandler(404)
def erro404(error):
    return redirect("/")

#FINAL - RODAR O APP BONITINHO 
app.run(debug = True) #ACESSAR ACESSO NO AR - liberação endereço publico no ar