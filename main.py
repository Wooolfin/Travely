from flask import Flask, render_template, redirect, request, session
import mysql.connector
#pip install mysql-connector-python BAIXAR - AJUDA A CONETAR MYSQL COM O PYTHON

#REDIRECT manda o user pra ROTA
#RENDER_TEMPLATE manda o user pra HTML CSS

conexaoDB = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
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
1

#HOMEPAGE
@app.route('/')
def home():
    comandoSQL = 'SELECT * FROM passeio' #comando sql
    cursorDB = conexaoDB.cursor() #deixa conexao estavel
    cursorDB.execute(comandoSQL) #executa comando sql
    passeios = cursorDB.fetchall()#faz uma lista com os dados
    cursorDB.close()#fecha banco de dados

    return render_template("home.html", passeios=passeios)

#ROTA PARA ABRIR O FORMULÁRIO DE CADASTRO
@app.route("/cadpasseio")
def novopasseio():
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('login.html')
    
    return render_template("cadPasseio.html")

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
    return render_template("detalhes.html",passeio=passeio)

#ROTA DA PÁGINA ADMINISTRATIVA
@app.route('/adm')
def adm():
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    
    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão


    comandoSQL = f'SELECT * FROM passeio WHERE idUsuario = {idUsuario} ORDER BY idPasseio DESC '
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeios = cursorDB.fetchall()
    cursorDB.close()
    return render_template("adm.html",passeios=passeios)

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

    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão

    comandoSQL = f'SELECT * FROM passeio WHERE idUsuario = {idUsuario}' #comando sql
    cursorDB = conexaoDB.cursor() #deixa conexao estavel
    cursorDB.execute(comandoSQL) #executa comando sql
    passeios = cursorDB.fetchall()#faz uma lista com os dados
    cursorDB.close()#fecha banco de dados

    return render_template("listaPasseios.html", passeios=passeios)
   

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

    # comandoSQL = f'INSERT INTO usuario VALUES (null, "{nome}","{cpf_cnpj}","{telefone}","{data_nascimento}","{cep}","{ruaEndUser}","{bairroEndUser}","{numEndUser}","{email}","{senha}","{True}");
    # INSERT INTO adGuia VALUES (null, "{cadastur}", "{chavePix}")'

# Inserir na tabela `usuario`
    comandoSQL_usuario = """
        INSERT INTO usuario (nome, cpfCnpj, numTelefone, dataNasc, cepEndUser, ruaEndUser, bairroEndUser, numEndUser, email, senha, tipo) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    valores_usuario = (nome, cpf_cnpj, telefone, data_nascimento, cep, ruaEndUser, bairroEndUser, numEndUser, email, senha, tipo)

    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL_usuario, valores_usuario)
    # cursorDB.execute(valores_adGuia)
    
    
    conexaoDB.commit()

    id_usuario = cursorDB.lastrowid

    # Inserir na tabela `adGuia` utilizando o id_usuario
    comandoSQL_adGuia = """
        INSERT INTO adGuia (cadastur, chavePix, idUsuario) 
        VALUES (%s, %s, %s)
    """
    valores_adGuia = (cadastur, chavePix, id_usuario)
    cursorDB.execute(comandoSQL_adGuia, valores_adGuia)
  

    
    # cursorDB.execute(comandoSQL)
    conexaoDB.commit()
    cursorDB.close()
    return redirect('/adm')

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
    comandoSQL = "SELECT idUsuario FROM usuario WHERE email = %s AND senha = %s"
    cursorDB.execute(comandoSQL, (usuario_informado, senha_informado))
    resultado = cursorDB.fetchone()  # Busca o idUsuario associado ao usuário
    cursorDB.close()

    # Se encontrou um usuário com as credenciais fornecidas
    if resultado:
        session['login'] = True  # Autoriza a entrada
        session['idUsuario'] = resultado[0]  # Armazena o idUsuario na sessão
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