from distutils.command.config import config
import discord
from discord.ext import commands"

intents = discord.Intents.all()

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f"Estou pronto! Estou conectado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg = message.content

    def shiftPlayerString(log):
        keyword = 'Healing' + ': '
        startIndex = log.find(keyword)
        auxSubstring = log[startIndex:]
        endSubstring = auxSubstring[auxSubstring.find('\n') + 1:]
        return endSubstring

    def parseFirstKeyword(log, keyword):
        keyword = keyword + ': '
        startIndex = log.find(keyword) + len(keyword)
        substring = log[startIndex:]
        valueString = substring[:substring.find('\n')]
        value = int(valueString.replace(',', ''))
        return value, startIndex + substring.find('\n')

    def findPerHour(log, keyword, multiplier):
        keyword = keyword + ':'
        startIndex = log.find(keyword) + len(keyword)
        outputSubstring = log[startIndex:]
        outputSubstringWithComma = outputSubstring[:outputSubstring.find('\n')]
        output = int(outputSubstringWithComma.replace(',', ''))
        return int(output * multiplier)

    def pretty_print(players):
        for player in players:
            print(player[0] + ': ' + str(player[1]))

    def findSession(log, keyword):
        keyword = keyword + ': '
        startIndex = log.find(keyword) + len(keyword)
        output = log[startIndex:startIndex + 5].replace(':', '')
        return int(output[:2]), int(output[2:4])

    if msg == ('!t'):
        await message.channel.send(
            'Bem vindo ao TibiaUtils! Para ver os comandos disponíveis, digite !t -help'
        )

    if msg.startswith('!t '):
        result = msg.lstrip('!t ')

        if result.startswith('-help'):
            await message.channel.send(
                '### Comandos disponíveis ###\n\n\!t -hora <log hunt analyzer>\n\tMostra o total de profit/exp que seria feito em uma hora.\n\n!t -loot <log party hunt analyzer>\n\tMostra quem precisa pagar quem na party.\n\n!t -rashid\n\tMostra onde o Rashid está hoje'
            )

        elif result.startswith('-hora '):
            result = result.lstrip('-hora ')

            sessionHours = findSession(result, 'Session')[0]
            sessionMinutes = findSession(result, 'Session')[1]

            if sessionHours == 0:
                if sessionMinutes != 0:
                    multiplier = 60 / sessionMinutes
                    balancePerHour = findPerHour(result, 'Balance', multiplier)
                    expPerHour = findPerHour(result, 'XP Gain', multiplier)
                    output = 'Exp por hora: %s exp\nLoot por hora: %s gp' % (
                        f'{expPerHour:,}', f'{balancePerHour:,}')
                    await message.channel.send(output)
                else:
                    await message.channel.send(
                        "Erro: Log contém 0 minutos de duração, você precisa caçar por pelo menos 1 minuto."
                    )
            else:
                await message.channel.send(
                    "Erro: Bot ainda não foi programado para logs maiores de uma hora!"
                )

        elif result.startswith('-rashid'):
            rashidLocations = {
                'Monday': 'Svargrond - Taverna no sul do templo',
                'Tuesday': 'Liberty Bay - Taverna na esquerda do depot',
                'Wednesday': 'Port Hope - Tarverna na esquerda do depot',
                'Thursday': 'Ankrahmun - Sul esquerda da cidade',
                'Friday': 'Darashia - Sul da cidade',
                'Saturday': 'Edron - Em cima do depot',
                'Sunday': 'Carlin - Em cima do depot'
            }
            weekDay = (datetime.datetime.today() -
                       datetime.timedelta(hours=8)).strftime('%A')
            await message.channel.send(rashidLocations[weekDay])
        elif result.startswith('-loot '):
            result = result.lstrip('-loot ')
            error = False
            errorMsg = 'Erro. Não foi possível realizar o cálculo corretamente. Verifique se o log copiado está correto.'
            playersWithBalances = []
            partyBalance, index = parseFirstKeyword(result, 'Balance')
            playersSubstring = result[index:].partition('\n')[2]

            # pega balance e nome de cada player e desloca o log para achar o prox player
            while playersSubstring.count('\n') != 0:
                playerName = playersSubstring[:playersSubstring.find('\n')]
                playerBalance = parseFirstKeyword(playersSubstring,
                                                  'Balance')[0]
                playersWithBalances.append(list((playerName, playerBalance)))
                playersSubstring = shiftPlayerString(playersSubstring)

            # remove a tag do party leader
            for player in playersWithBalances:
                player[0] = player[0].replace(' (Leader)', '')

            # print antes de começar os pagamentos
            print("\nANTES")
            pretty_print(playersWithBalances)

            # definição de quanto cada um vai receber
            playerShare = int(partyBalance / len(playersWithBalances))
            print("\nShare: " + str(playerShare))

            # inicio do loop de pagamentos até todo mundo ficar igual
            maisRico = '', 999999999
            transacoes = []
            erroCount = 0

            # enquanto o mais rico estuiver desbalanceado com os demais
            while ((maisRico[1] - playerShare) > 50):
                maisRico = '', -999999999
                maisPobre = '', 999999999

                # para cada jogador, se o jogador for mais rico que o mais rico atual,
                # este se torna o mais rico, e o mesmo se aplica para o mais pobre
                for player in playersWithBalances:
                    if player[1] > maisRico[1]:
                        maisRico = player
                    if player[1] < maisPobre[1]:
                        maisPobre = player

                # calcula o dinheiro disponivel do jogador mais rico para pagemtno
                maisRicoDisponivel = maisRico[1] - playerShare

                # se o mais pobre tiver negativado, inverte o calculo
                # TODO: acho que nem precisa disso, tá só invertido os valores ali
                if maisPobre[1] <= 0:
                    maisPobreNecessita = maisPobre[1] * -1 + playerShare
                else:
                    maisPobreNecessita = playerShare - maisPobre[1]

                # se o mais rico tiver o suficiente para pagar o mais pobre, realiza
                # o pagamento.
                if maisRicoDisponivel > maisPobreNecessita:

                    # procura os jogadores que participarão da transação
                    for player in playersWithBalances:
                        if player[0] == maisRico[0]:
                            player[1] = player[1] - maisPobreNecessita
                            transacoes.append(
                                (player[0], maisPobreNecessita, maisPobre[0]))
                        if player[0] == maisPobre[0]:
                            player[1] = player[1] + maisPobreNecessita

                # senao, o mais rico paga apenas o que tiver disponivel
                else:
                    for player in playersWithBalances:
                        if player[0] == maisRico[0]:
                            player[1] = player[1] - maisRicoDisponivel
                            transacoes.append(
                                (player[0], maisRicoDisponivel, maisPobre[0]))
                        if player[0] == maisPobre[0]:
                            player[1] = player[1] + maisRicoDisponivel

                    # gera novo teste de condicao de parada
                    for player in playersWithBalances:
                        if player[1] > maisRico[1]:
                            maisRico = player

                # caso entre em loop infinito por algum motivo, limita a 20 vezes
                # e seta a flag erro
                erroCount = erroCount + 1
                if erroCount > 20:
                    error = True
                    break

            print("\nDEPOIS")
            pretty_print(playersWithBalances)

            # testa se deu certo o calculo
            for player in playersWithBalances:
                if abs(player[1] - playerShare) > 1000:
                    print("\nDEPOIS")
                    pretty_print(playersWithBalances)
                    await message.channel.send(errorMsg)
                    return

            # se nao deu erro, vai mandar no chat o resultado
            if not error:
                await message.channel.send('Share: ' + str(playerShare))
                for transacao in transacoes:
                    await message.channel.send(transacao[0] + ' -> ' +
                                               'transfer ' +
                                               str(transacao[1]) + ' to ' +
                                               transacao[2])
            else:
                await message.channel.send(errorMsg)
        else:
            await message.channel.send('Comando não reconhecido.')


token = config("TOKEN")
print(token)
bot.run(token)

