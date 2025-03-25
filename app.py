from flask import Flask, render_template, request, redirect, url_for
import os
import random

app = Flask(__name__)

def carregar_times():
    times = []
    try:
        with open('times.txt', 'r') as f:
            for line in f:
                nome, conferencia = line.strip().split('|')
                times.append({'nome': nome, 'conferencia': conferencia})
    except FileNotFoundError:
        pass  # Caso o arquivo não exista, retorna lista vazia
    return times

def salvar_times(times):
    with open('times.txt', 'w') as f:
        for time in times:
            # Salva no formato 'nome_do_time|conferencia'
            f.write(f"{time['nome']}|{time['conferencia']}\n")
        gerar_e_salvar_confrontos(times)

# Função para gerar confrontos ida e volta e salvar no arquivo
def gerar_e_salvar_confrontos(times):
    if not times:  # Verifica se a lista de times está vazia
        print("Erro: Nenhum time cadastrado.")
        return

    # Pegamos apenas os nomes dos times
    times = [time['nome'] for time in times]  

    num_times = len(times)
    if num_times < 2:
        print("Erro: É necessário pelo menos dois times para gerar confrontos.")
        return

    print(f"Gerando confrontos para {num_times} times...")  # Depuração

    rodadas = []
    random.shuffle(times)

    # Geração do primeiro turno
    for rodada in range(num_times - 1):
        confrontos = []
        for i in range(num_times // 2):
            casa = times[i]
            fora = times[num_times - 1 - i]
            confrontos.append((casa, fora, "x", "x"))  # Adiciona placares padrão "x x"
        rodadas.append(confrontos)
        times.insert(1, times.pop())  # Algoritmo Round Robin

    # Geração do segundo turno (invertendo os mandos de campo)
    rodadas_retorno = [[(fora, casa, "x", "x") for casa, fora, _, _ in jogos] for jogos in rodadas]

    # Junta os turnos
    rodadas.extend(rodadas_retorno)

    # Salvar no arquivo
    with open("resultados.txt", "w") as arquivo:
        for rodada_idx, jogos in enumerate(rodadas, start=1):
            for jogo in jogos:
                linha = f"Rodada {rodada_idx}: {jogo[0]} x {jogo[1]} - {jogo[2]} {jogo[3]}\n"
                arquivo.write(linha)

    print("Arquivo resultados.txt gerado com sucesso!")  # Depuração

# Função para carregar confrontos do arquivo
def carregar_confrontos():
    confrontos = []
    if os.path.exists("resultados.txt"):
        with open("resultados.txt", "r") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha:
                    continue
                partes = linha.split(": ")
                if len(partes) < 2:
                    continue
                rodada_info, partida_info = partes[0], partes[1]
                try:
                    rodada = int(rodada_info.split(" ")[1])  # Pegando apenas o número da rodada
                    time_casa, restante = partida_info.split(" x ", 1)
                    time_fora, placar = restante.rsplit(" - ", 1)
                    placar_casa, placar_fora = placar.split(" ")

                    while len(confrontos) < rodada:
                        confrontos.append([])

                    confrontos[rodada - 1].append((time_casa.strip(), time_fora.strip(), placar_casa.strip(), placar_fora.strip()))
                except ValueError:
                    print(f"Erro ao processar linha: {linha}")  # Depuração
                    continue
    return confrontos

# Função para carregar os resultados dos confrontos
def carregar_resultados():
    confrontos = []
    if os.path.exists("resultados.txt"):
        with open("resultados.txt", "r") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha:
                    continue
                partes = linha.split(": ")
                if len(partes) < 2:
                    continue
                rodada_info, partida_info = partes[0], partes[1]
                try:
                    rodada = int(rodada_info.split(" ")[1])  # Pegando apenas o número da rodada
                    time_casa, restante = partida_info.split(" x ", 1)
                    time_fora, placar = restante.rsplit(" - ", 1)
                    placar_casa, placar_fora = placar.split(" ")

                    confrontos.append((time_casa.strip(), time_fora.strip(), placar_casa.strip(), placar_fora.strip()))

                except ValueError:
                    print(f"Erro ao processar linha: {linha}")  # Depuração
                    continue
    return confrontos

def calcular_classificacao():
    times = carregar_times()
    resultados = carregar_resultados()
    vitorias_iniciais = {"Milwaukee Bucks": -1}
    derrotas_iniciais = {"Milwaukee Bucks": 1}
    # Criar um dicionário único para todas as conferências
    tabela = {time['nome']: {'Conferencia': time['conferencia'], 'Pontos': 0, 'Vitórias': vitorias_iniciais.get(time['nome'], 0), 'Derrotas': derrotas_iniciais.get(time['nome'], 0), 'Saldo': 0, 'Feitos': 0, 'Sofridos': 0} for time in times}

    for time_casa, time_fora, placar_casa, placar_fora in resultados:
        if placar_casa == 'x' or placar_fora == 'x':
            continue  # Ignora jogos sem resultado

        try:
            gols_casa, gols_fora = int(placar_casa), int(placar_fora)

            # Atualiza gols marcados e sofridos
            tabela[time_casa]['Feitos'] += gols_casa
            tabela[time_casa]['Sofridos'] += gols_fora
            tabela[time_fora]['Feitos'] += gols_fora
            tabela[time_fora]['Sofridos'] += gols_casa

            # Atualiza vitórias, derrotas e pontos
            if gols_casa > gols_fora:
                tabela[time_casa]['Vitórias'] += 1
                tabela[time_casa]['Pontos'] += 3
                tabela[time_fora]['Derrotas'] += 1
            elif gols_fora > gols_casa:
                tabela[time_fora]['Vitórias'] += 1
                tabela[time_fora]['Pontos'] += 3
                tabela[time_casa]['Derrotas'] += 1
            else:
                tabela[time_casa]['Pontos'] += 1
                tabela[time_fora]['Pontos'] += 1

            # Atualiza saldo de gols
            tabela[time_casa]['Saldo'] = tabela[time_casa]['Feitos'] - tabela[time_casa]['Sofridos']
            tabela[time_fora]['Saldo'] = tabela[time_fora]['Feitos'] - tabela[time_fora]['Sofridos']

        except ValueError:
            print(f"Erro ao processar resultado: {time_casa} x {time_fora} ({placar_casa} - {placar_fora})")
            continue

    # Separar as classificações por conferência
    classificacao_leste = sorted(
        [item for item in tabela.items() if item[1]['Conferencia'] == 'Leste'],
        key=lambda x: (#x[1]['Pontos'], 
            x[1]['Vitórias'], x[1]['Saldo']),
        reverse=True
    )

    classificacao_oeste = sorted(
        [item for item in tabela.items() if item[1]['Conferencia'] == 'Oeste'],
        key=lambda x: (x[1]['Pontos'], x[1]['Vitórias'], x[1]['Saldo']),
        reverse=True
    )

    # Salvar a classificação por conferência
    with open("classificacao.txt", "w") as arquivo:
        nome_max = max(len(time) for time, _ in tabela.items()) + 2
        arquivo.write("Classificação Leste:\n")
        arquivo.write("=" * 60 + "\n")
        arquivo.write(f"{'Time':{nome_max}}{'Vitórias':>10}{'Derrotas':>10}{'Saldo':>10}\n")
        arquivo.write("-" * 60 + "\n")
        for time, stats in classificacao_leste:
            arquivo.write(f"{time:{nome_max}}{stats['Vitórias']:>10}{stats['Derrotas']:>10}{stats['Saldo']:>10}\n")
        arquivo.write("=" * 60 + "\n")

        arquivo.write("Classificação Oeste:\n")
        arquivo.write("=" * 60 + "\n")
        arquivo.write(f"{'Time':{nome_max}}{'Vitórias':>10}{'Derrotas':>10}{'Saldo':>10}\n")
        arquivo.write("-" * 60 + "\n")
        for time, stats in classificacao_oeste:
            arquivo.write(f"{time:{nome_max}}{stats['Vitórias']:>10}{stats['Derrotas']:>10}{stats['Saldo']:>10}\n")
        arquivo.write("=" * 60 + "\n")
    
    print("Classificação salva em classificacao.txt")

    return classificacao_leste, classificacao_oeste

@app.route('/classificacao')
def classificacao():
    times = carregar_times()
    classificacao_leste, classificacao_oeste = calcular_classificacao()

    return render_template(
        'classificacao.html',
        classificacao_leste=classificacao_leste,
        classificacao_oeste=classificacao_oeste
    )

# Rota inicial (home)
@app.route('/')
def index():
    times = carregar_times()
    if not times:
        return redirect(url_for('cadastro'))
    return render_template('index.html', times=times)

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        times = []
        for i in range(len(request.form.getlist('times'))):
            nome_time = request.form.getlist('times')[i]
            conferencia = request.form.getlist('conferencia')[i]
            times.append({'nome': nome_time, 'conferencia': conferencia})
        salvar_times(times)  # Salva os times no arquivo
        return redirect(url_for('index'))
    return render_template('cadastro.html')

# Rota para exibir o calendário de jogos
@app.route('/calendario')
def calendario():
    rodadas = carregar_confrontos()
    return render_template('calendario.html', rodadas=rodadas, enumerate=enumerate)

# Rota para editar os resultados dos jogos
@app.route('/editar_resultado', methods=['POST'])
def editar_resultado():
    rodada = int(request.form['rodada'])
    time_casa = request.form['time_casa']
    time_fora = request.form['time_fora']
    placar_casa = request.form['placar_casa']
    placar_fora = request.form['placar_fora']
    
    # Carregar os confrontos do arquivo
    confrontos = carregar_confrontos()

    # Atualizar o confronto com os novos resultados
    for i, confronto in enumerate(confrontos[rodada - 1]):
        if confronto[0] == time_casa and confronto[1] == time_fora:
            confrontos[rodada - 1][i] = (time_casa, time_fora, placar_casa, placar_fora)
            break
    
    # Salvar os confrontos atualizados no arquivo
    with open("resultados.txt", "w") as arquivo:
        for rodada_idx, jogos in enumerate(confrontos, start=1):
            for jogo in jogos:
                linha = f"Rodada {rodada_idx}: {jogo[0]} x {jogo[1]} - {jogo[2]} {jogo[3]}\n"
                arquivo.write(linha)
    
    # Recalcular a classificação após editar os resultados
    calcular_classificacao()

    # Redirecionar de volta para o calendário
    return redirect(url_for('calendario'))

if __name__ == '__main__':
    app.run(debug=True)
