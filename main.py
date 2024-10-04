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

#HOMEPAGE
@app.route('/')
def home():
    comandoSQL ='''SELECT 
        p.idPasseio,
        p.nome AS nomePasseio,
        p.estadoPasseio,
        p.cidadePasseio,
        p.bairroEndPasseio,
        p.qtdPessoas,
        p.valor,
        c.nome,
        p.tempoPasseio,
        p.descricaoPasseio
    FROM 
        passeio p
    JOIN 
        categoria c ON p.categoria = c.idCategoria;
    '''
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
    estadoPasseio = request.form['estadoPasseio']
    cidadePasseio = request.form['cidadePasseio']
    bairroEndPasseio = request.form['bairroEndPasseio']
    qtdPessoas = request.form['qtdPessoas']
    valor = request.form['valor']
    tempo = request.form['tempo']
    categoria = request.form['categoria']
    descricao = request.form['descricao']
    
    idUsuario = session.get('idUsuario')  # Recupera o idGuia da sessão

    if idUsuario is None:
        return render_template('error.html', msg="ID do Guia não fornecido ou usuário não autenticado.")
    
    # Query SQL ajustada para corresponder à estrutura da tabela
    comandoSQL = '''
    INSERT INTO passeio (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, qtdPessoas, valor, tempo, categoria, descricao, idUsuario)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    valores = (nome, estadoPasseio, cidadePasseio, bairroEndPasseio, qtdPessoas, valor, tempo, categoria, descricao, idUsuario)

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

@app.route('/detalhes/<int:id>', methods=['GET', 'POST'])
def detalhes(id):   
    cursorDB = conexaoDB.cursor()

    if request.method == 'POST':
        # Pegando o valor selecionado de qtdTurAg
        qtdTurAg = int(request.form.get('qtdTurAg', 1))
        
        # Seleciona o valor do passeio para calcular o total
        comandoSQL = f'SELECT valor FROM passeio WHERE idPasseio = {id}'
        cursorDB.execute(comandoSQL)
        valor_passeio = cursorDB.fetchone()[0]  # Asume que o resultado é uma tupla com um único valor
        
        # Calculando o valor total
        total = valor_passeio * qtdTurAg
    else:
        comandoSQL = f'SELECT valor FROM passeio WHERE idPasseio = {id}'
        cursorDB.execute(comandoSQL)
        valor_passeio = cursorDB.fetchone()[0]  # Asume que o resultado é uma tupla com um único valor
        total = valor_passeio
        qtdTurAg = 1

    # Informações do passeio para visualização
    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB.execute(comandoSQL)
    passeio = cursorDB.fetchone()

    # Informações do guia
    comandoSQL = f'SELECT * FROM usuario WHERE idUsuario = {passeio[10]}'
    cursorDB.execute(comandoSQL)
    dadosGuia = cursorDB.fetchone()
    
    # Informações para o carrossel de outros passeios
    comandoSQL = '''SELECT 
        p.idPasseio,
        p.nome AS nomePasseio,
        p.estadoPasseio,
        p.cidadePasseio,
        p.bairroEndPasseio,
        p.qtdPessoas,
        p.valor,
        c.nome AS categoriaNome,
        p.tempoPasseio,
        p.descricaoPasseio
    FROM 
        passeio p
    JOIN 
        categoria c ON p.categoria = c.idCategoria;'''
    cursorDB.execute(comandoSQL)
    pCarrossel = cursorDB.fetchall()

    tipo_usuario = session.get('tipo')
    cursorDB.close()

    # Renderizando o template com todos os dados necessários
    return render_template("detalhes.html", passeio=passeio, pCarrossel=pCarrossel, tipo=tipo_usuario, guia=dadosGuia, total=total, qtdTurAg=qtdTurAg,valor=valor_passeio, id=id)

#ROTA PARA O TURISTA CONFIRMAR AGENDAMENTO
@app.route("/confirmaPag/<int:id>", methods=['GET', 'POST'])
def confirmaPag(id):
    cursorDB = conexaoDB.cursor()
            # Obter detalhes do passeio para exibição
    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB.execute(comandoSQL)
    passeio = cursorDB.fetchone()

    if request.method == 'POST':
        # Captura a quantidade de turistas e a data do agendamento do formulário
        qtdTurAg = int(request.form.get('qtdTurAg', 1))
        # Calcula o valor total com base na quantidade de turistas
        total = passeio[6] * qtdTurAg  # Assumindo que passeio[6] é o valor do passeio

        # Renderizar a página de confirmação com o valor calculado
        return render_template("confirmaPag.html", passeio=passeio, total=total, qtdTurAg=qtdTurAg)

    # Se o método for GET, apenas exibe a página com os detalhes do passeio
    else:
        comandoSQL = f'SELECT valor FROM passeio WHERE idPasseio = {id}'
        cursorDB.execute(comandoSQL)
        valor_passeio = cursorDB.fetchone()[0]
        total = valor_passeio
        qtdTurAg = 1

        return render_template("confirmaPag.html", passeio=passeio, total=total, qtdTurAg=qtdTurAg)

@app.route("/confirmarAgendamento/<int:id>", methods=['POST'])
def confirmarAgendamento(id):
    cursorDB = conexaoDB.cursor()
    idUsuario = session.get('idUsuario')  # Recupera o id do usuário da sessão

    # Captura os valores enviados pelo formulário
    qtdTurAg = int(request.form.get('qtdTurAg', 1))
    dataAg = request.form['dataAg']

    # Obter detalhes do passeio
    comandoSQL = f'SELECT * FROM passeio WHERE idPasseio = {id}'
    cursorDB.execute(comandoSQL)
    passeio = cursorDB.fetchone()

    # Inserir em agendamento
    comandoInsert = '''
    INSERT INTO agendamento (qtdTurAgendamento, pago, idPasseio, idTurista)
    VALUES (%s, %s, %s, %s);
    '''
    cursorDB.execute(comandoInsert, (qtdTurAg, False, id, idUsuario))
    idAgendamento = cursorDB.lastrowid  # Captura o ID do agendamento inserido
    
    # Calcula o valor total com base na quantidade de turistas
    total = passeio[6] * qtdTurAg  # Assumindo que passeio[6] é o valor do passeio
    
    # Inserir em grupopasseios com a data do agendamento
    comandoInsert1 = '''
    INSERT INTO grupopasseios (dataAgendamento, idAgendamento, idTuristaAg, vTotal)
    VALUES (%s, %s, %s, %s);
    '''
    cursorDB.execute(comandoInsert1, (dataAg, idAgendamento, idUsuario, total))
    
    # Confirmar as inserções no banco de dados
    conexaoDB.commit()
    
    return redirect("/home")  # Redirecionar para página de confirmação ou sucesso


#ROTA DA PÁGINA ADMINISTRATIVA
@app.route('/adm')
def adm():
    if not verifica_sessao(): #verificação se tem sessao / um acesso login na pagina 
        return render_template('/login.html')
    
    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão
    tipo_usuario = session.get('tipo')

    comandoSQL1 = f'SELECT nome FROM usuario WHERE idUsuario = {idUsuario}'
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL1)
    usuario = cursorDB.fetchone()


    comandoSQL = f'SELECT * FROM passeio WHERE idGuia = {idUsuario} ORDER BY idPasseio DESC '
    cursorDB = conexaoDB.cursor()
    cursorDB.execute(comandoSQL)
    passeios = cursorDB.fetchall()
    cursorDB.close()
    return render_template("adm.html",passeios=passeios, tipo=tipo_usuario , usuario=usuario)

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
    if not verifica_sessao():  # Verificação se tem sessão / um acesso login na página 
        return render_template('/login.html')

    tipo_usuario = session.get('tipo')
    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão
    
    cursorDB = conexaoDB.cursor()  # Conexão com o banco de dados
    
    if tipo_usuario:  # Se for guia

    # Consulta SQL para buscar os agendamentos de acordo com a data
        comandoSQL = '''
            SELECT 
                gp.idGrupoPasseios,
                gp.dataAgendamento,
                p.nome,
                ag.idAgendamento, 
                ag.qtdTurAgendamento, 
                ag.pago, 
                gp.vTotal,
                p.valor, 
                u.nome AS nomeTurista, 
                u.email
            FROM 
                grupopasseios gp
            JOIN 
                agendamento ag ON gp.idAgendamento = ag.idAgendamento 
            JOIN 
                passeio p ON ag.idPasseio = p.idPasseio 
            JOIN 
                usuario u ON ag.idTurista = u.idUsuario 
            ORDER BY 
                gp.dataAgendamento;
            '''

            # Executa a consulta com a data fornecida
        cursorDB.execute(comandoSQL)
        agendamentos = cursorDB.fetchall()

    else:  # Se for turista
        #COMANDO TESTE PARA  NÃO DAR ERRO
        comandoSQL1 = '''
            SELECT 
                gp.idGrupoPasseios,
                gp.dataAgendamento,
                p.nome,
                ag.idAgendamento, 
                ag.qtdTurAgendamento, 
                ag.pago, 
                gp.vTotal,
                p.valor, 
                u.nome AS nomeTurista, 
                u.email
            FROM 
                grupopasseios gp
            JOIN 
                agendamento ag ON gp.idAgendamento = ag.idAgendamento 
            JOIN 
                passeio p ON ag.idPasseio = p.idPasseio 
            JOIN 
                usuario u ON ag.idTurista = u.idUsuario 
            ORDER BY 
                gp.dataAgendamento;
        '''
        cursorDB.execute(comandoSQL1)  # Executa comando SQL para turistas
        agendamentos = cursorDB.fetchall()
    
    cursorDB.close()  # Fechar a conexão com o banco de dados

    return render_template("listaPasseios.html", agendamentos=agendamentos, tipo=tipo_usuario)

#ROTA PARA EXIBIR A DIV CONFIRMAR PAGAMENTO
@app.route("/listaPasseio/<int:idAgendamento>/<int:idPasseio>/<int:idGuia>/", methods=['GET'])
def listaPasseios(idAgendamento, idPasseio, idGuia):
    cursorDB = conexaoDB.cursor()
    idUsuario = session.get('idUsuario')  # Recupera o idUsuario da sessão

    # Primeiro comando SQL (Lista todos os agendamentos associados ao id do guia)
    comandoSQL1 = '''
        SELECT 
            ag.idAgendamento, 
            ag.idUsuario, 
            ag.dataPasseio, 
            ag.qtdTurAgendamento,
            p.nome, 
            p.valor,
            p.idUsuario, 
            u.nome,
            ag.idPasseio
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            usuario u ON ag.idUsuario = u.idUsuario
        WHERE 
            p.idUsuario = %s;
    '''
    cursorDB.execute(comandoSQL1, (idUsuario, ))  # Executa comando SQL
    agendamentos = cursorDB.fetchall()  # Faz uma lista com os dados

    # Segundo comando SQL para buscar agendamento específico baseado nos parâmetros da URL
    comandoSQL = '''
        SELECT 
            ag.idAgendamento, 
            ag.idUsuario, 
            ag.dataPasseio, 
            ag.qtdTurAgendamento,
            p.nome AS nomePasseio, 
            p.valor, 
            p.idUsuario AS idGuia, 
            u.nome AS nomeTurista
        FROM 
            agendamento ag
        JOIN 
            passeio p ON ag.idPasseio = p.idPasseio
        JOIN 
            usuario u ON ag.idUsuario = u.idUsuario
        WHERE 
            p.idUsuario = %s AND ag.idAgendamento = %s AND ag.idPasseio = %s;
    '''
    
    # Usando os parâmetros da rota no comando SQL
    cursorDB.execute(comandoSQL, (idGuia, idAgendamento, idPasseio))
    resultadosAg = cursorDB.fetchall()  # Retorna todos os resultados da consulta

    cursorDB.close()

    tipo_usuario = session.get('tipo')

    # Renderiza a página com os dados dos agendamentos e resultadosAg
    return render_template("listaPasseios.html", resultadosAg=resultadosAg, tipo=tipo_usuario, agendamentos=agendamentos)

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
    estadoPasseio = request.form['estadoPasseio'] if request.form['estadoPasseio'] else passeio_atual[2]
    cidadePasseio = request.form['cidadePasseio'] if request.form['cidadePasseio'] else passeio_atual[3]
    bairroEndPasseio = request.form['bairroEndPasseio'] if request.form['bairroEndPasseio'] else passeio_atual[4]
    qtdPessoas = request.form['qtdPessoas'] if request.form['qtdPessoas'] else passeio_atual[5]
    valor = request.form['valor'] if request.form['valor'] else passeio_atual[6]
    tempoPasseio = request.form['tempoPasseio'] if request.form['tempoPasseio'] else passeio_atual[7]
    descricaoPasseio = request.form['descricao'] if request.form['descricao'] else passeio_atual[9]

    # Atualiza os dados do passeio no banco de dados
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

#SE USER TENTAR ACESSAR UMA ROTA NÃO AUTORIZADA 
@app.errorhandler(405)
def erro405(error):
    return redirect("/")

#SE USER TENTAR ACESSAR UMA ROTA QUE NÃO EXISTE 
@app.errorhandler(404)
def erro404(error):
    return redirect("/")

#FINAL - RODAR O APP BONITINHO 
app.run(host='0.0.0.0', port=5000, debug = True) #ACESSAR ACESSO NO AR - liberação endereço publico no ar