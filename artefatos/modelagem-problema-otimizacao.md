# 1.2 Escolha da Abordagem de Otimização

Ao optar por uma implementação baseada na técnica de aprendizado por reforço, é fundamental abordar características que fazem parte do cerne dessa técnica, tal como o agente (tomador de decisão e que influencia o ambiente ao redor) e o ambiente, o qual o agente interage e atua, é onde as regras são definidas, além da representação do estado e como o agente influencia esse estado a partir da execução de suas ações. Sendo assim, a modelagem de otimização irá tratar de:
* Agentes;
* Ações;
* Recompensas/penalidades;
* Steps(etapas);
* Ambiente;
* Episódios.

## Modelagem
Focando em uma possível granularidade das ações disponíveis para o agente, cada ação tomada se refere ao contexto compra/venda no formato de uma única ação, ou seja, trata-se de ações individuais realizadas pela entidade agente, fazendo com esta ação seja uma composição no processo de casamento. Desse modo, no contexto do projeto, temos um “agente principal”, tal agente possui experiências/interações e realiza as seguintes ações listadas:

### “insertMatches”:
Ação que insere casamentos de a termo e a vista (tendo informações como preço, quantidade, data de vencimento…), ou seja, é a formação dos casamentos. Desse modo, o agente é responsável por formar casamentos de a termo e a vista com base nas unidades disponíveis no ambiente. Ele observa o estado atual do ambiente, toma decisões com base nessas observações e executa ações para formar casamentos.

|  |  |
| --- | --- |
| **Ambiente** | O ambiente consiste em uma lista de unidades disponíveis para formação de casamentos “Matches”. Cada unidade possui informações como preço, quantidade e data de vencimento. Para implementar, o ambiente precisa receber a ação do agente que formará os casamentos com base nos critérios específicos(quantidade limite dos títulos para a formação e características como preço, quantidade, data de vencimento). O agente será responsável por selecionar e combinar unidades disponíveis para formar casamentos que se encaixam nesses critérios. |
| **Recompensa** | A recompensa é definida com base na qualidade dos casamentos levando em consideração a porcentagem CDI alcançada, este sendo representado por “percentageCDI”, a quantidade limite (evitando a ultrapassagem) “idealQuantity” e a eficiência com que executam as operações de casamento entre a vista e a termo levando em consideração o número de steps. Casamentos que atingem uma porcentagem igual ou superior ao CDI e que utilizam combinações eficientes de unidades podem receber uma recompensa +1. Casamentos que não atingem a porcentagem desejada do CDI ou que violam as restrições de quantidade podem receber uma penalidade -1. |

Obs: os valores de recompensas e penalidades são exemplos, podendo ser modificáveis conforme definições do modelo.


**Ação disparada**:
1. O agente observa o estado atual do ambiente, que inclui informações sobre as unidades disponíveis para formação de casamentos, como preço, quantidade e data de vencimento;
2. Com base na observação do estado, o agente decide quais unidades serão combinadas para formar os casamentos desejados.
3. Após verificar, a ação de selecionar e combinar casamentos é executada no ambiente. Por exemplo, as unidades selecionadas são removidas da lista de unidades disponíveis, e os casamentos resultantes são adicionados à lista de casamentos já estabelecidos;
4. O ambiente atualiza seu estado, inserindo novos casamentos;
5. O ambiente verifica se as restrições e critérios definidos para a formação de casamentos foram atendidos.
5. Após a atualização do estado, o ambiente fornece feedback ao agente sobre os resultados da ação de formação de casamentos. Isso pode incluir informações sobre os casamentos formados, como a porcentagem do CDI alcançada, além de possíveis penalidades.
8. Este processo é repetido várias vezes, cada vez que termina um episódio. O agente então inicia um novo episódio, observando novamente o estado atual do ambiente e repetindo o processo de formação de casamentos.


### “removeMatch” ou "removePossibleMatch":
Refere-se a remoção de casamentos existentes(ou possíveis) dos ativos, essa remoção, por exemplo, pode acontecer através de um ID que identifica determinado casamento ou por meio de critérios específicos levados em consideração, como data de vencimento.

|  |  |
| --- | --- |
| **Ambiente** | O ambiente consiste em uma lista de casamentos, onde cada casamento possui informações como cliente, data da operação, corretora e título. Além disso, o ambiente inclui um estado que representa o momento atual, o qual é influenciado pela presença e pelo estado dos casamentos na lista. Para implementar, o ambiente precisa receber a ação do agente que removerá os casamentos com base na data de vencimento como critério de remoção. |
| **Recompensa** |  A recompensa é definida se a remoção for considerada uma ação positiva dependendo da seleção efetuada, ou seja, se passou da data de vencimento(que não é útil para o sistema) pode-se definir como +1 para servir como um tipo de incentivo. Por outro lado, se o casamento removido for uma ação errônea, de modo que traga o risco de ser uma perda potencialmente útil, pode-se receber -1 como forma para o agente aprender que não deve repetir tal ato |

**Ação disparada**:
1. O agente observa o estado atual do ambiente, o qual terá a lista de potenciais casamentos;
2. Com base na restrição definida(data de vencimento), o agente toma a decisão de realizar a remoção das unidades a fim de não incluí-las nos casamentos de a termo e a vista;
3. Após verificar, a ação é executado no ambiente;
4. O ambiente atualiza seu estado, removendo unidades que não podem compor um casamento;
5. O agente então, recebe um feedback que é a recompensa, o que for recebido é com base no que a ação vai trazer de impacto após o descarte;
6. O processo é repetido várias vezes, a fim de garantir que o agente aprenda cada vez mais com base nas recompensas recebidas. Ou seja, cada episódio representa a instância completa desse ciclo de interação agente-ambiente, então para cada remoção efetuada e recompensa obtida, chegando a um resultado seja negativo ou positivo que auxilia na aprendizagem do agente, é definido o fim de um episódio.

Abaixo é exemplificado como seria uma simples implementação em código Python:

    def RemoveMatch(vencimentos):
        for match in match_list:
            if match.data_vencimento(vencimentos):
                remove_match(match)
    def data_vencimento(match, vencimentos):
        return match.date > vencimentos[‘data_vencimento’]


### “CompareAndReplaceMatches":
Comparar unidades de diferentes casamentos e substituir por outras unidades a fim de tornar uma melhor combinação, por exemplo, temos dois casamentos, o casamento 1 e 2, o primeiro é composto por A1 e C2, enquanto o segundo possui Z4 e B6, porém o B6 seria uma melhor unidade para combinar com A1 ao invés de C2, então o primeiro casamento na verdade torna-se composto por A1 e B6. Aqui a estratégia seria diversificar as boletas a vista que seriam casadas com os termos. Nesse contexto, aborda-se a variância que implica em várias boletas à vista em diferentes momentos ao entrar em x termo, a característica principal é a quantidade de cotas e o preço médio, então ao combinar diversas em um termo, optou-se por ter uma máxima variância. O agente é responsável por comparar os casamentos existentes e decidir se uma substituição de unidades é vantajosa ou não para diversificar as boletas à vista que serão casadas com os termos. Ele observa os casamentos disponíveis, avalia suas composições e decide se uma substituição é necessária para maximizar a variância, se a substituição é vantajosa, então é feita a execução desse processo.

|  |  |
| --- | --- |
| **Ambiente** | Mais uma vez, reforçando a respeito do ambiente, ele consiste em uma lista de casamentos, onde cada casamento é composto por unidades específicas. Cada unidade representa um ativo financeiro, com características como tipo, preço médio e quantidade. |
| **Recompensa** |  A recompensa é definida com base na eficácia da substituição para maximizar a variância das boletas à vista que serão casadas com os termos. Se a substituição resultar em uma diversificação eficaz, o agente recebe uma recompensa +1. Caso contrário, se o casamento tiver que retornar por exemplo(isso pode ser feito por um agente validador), pode receber penalidade -1 por efetuar mais steps. |

**Ação disparada**:
1. O agente observa os casamentos existentes e decide se uma substituição de unidades é benéfica ou não;
2. Após tomar a decisão de substituir unidades, o agente executa a ação de substituição no ambiente. Isso envolve remover as unidades selecionadas dos casamentos existentes e substituí-las por outras unidades mais adequadas para maximizar a variância;
3. O ambiente atualiza a composição dos casamentos de acordo com a substituição realizada pelo agente. As unidades substituídas são removidas dos casamentos existentes, enquanto as novas unidades são adicionadas para formar a nova combinação;
4. Após a atualização dos casamentos, o ambiente avalia a qualidade da nova combinação. Isso pode envolver cálculos para determinar a variância das boletas à vista que serão casadas com os termos, comparando-a com a variância anterior ou passar por um agente validador;
5. Com base na avaliação da nova combinação, o ambiente fornece feedback ao agente sobre a qualidade da substituição realizada. Se a variância das boletas à vista for maximizada com sucesso, o agente pode receber um feedback positivo. Caso contrário, o feedback pode ser negativo se houver o retorno de um casamento.

<br>

    É importante salientar que o ambiente é composto por várias variáveis, estas variáveis vão além da distância em relação ao CDI, optando por porcentagem que sejam iguais ou acima de 100%, além desta, a quantidade a ser alcançada de títulos, faz com que o modelo bloqueio qualquer tipo de operação para não atingir o limite imposto.

    Lembrando que, o ambiente dá retornos ao agente, tais retornos são variáveis "orders" ou valores determinados como a quantidade imposta de orders já citada anteriormente, determinando tipos de cenários.

Além do agente principal, consideramos uma futura implementação de um “agente validador”. Este agente é a própria função recompensa, ele seria como um filtrador, decidindo o que retorna ou não. Por exemplo, o agente validador tem o poder de validar se os casamentos possuem a melhor combinação, se não, será retornado ou, se incluir a quantidade de steps(corresponde a uma única ação, é a iteração ação-recompensa) como uma forma de recompensa, sendo descontado -1 ou atribuído +1 pontos caso afete o modelo, de forma que culmine num tempo prolongado de processamento, interpretabilidade complexa ou até mesmo contribua para um possível desvanecimento do gradiente. As ações do agente validador estão listadas abaixo, estas refletem também em como o agente validador pode monitorar outros agentes:
* Interagir com outros agentes e decidir quais combinações(casamentos) devem retornar ou não, validando as transações para que elas atendam os critérios definidos; 
* Desconectar casamentos;
* Fornecer feedbacks em busca de melhorar o desempenho desses agentes, verificando padrões, recompensas acumuladas, frequência de restrições violadas ou taxa de sucesso, tempo de treinamento etc;
* Validar resultados para garantir a corretude e confiabilidade dos outputs.

Ademais, futuramente, o modelo tem o potencial de ter multiagentes ao invés de apenas um, esses agentes tornam o modelo muito mais vantajoso, pois garante maior exploração e do espaço e paralelismo, ou seja, vários agentes interagem com o ambiente simultaneamente, o que diminui o tempo de treinamento, contribuindo para uma maior eficiência computacional e diversidade de estratégias conforme a aprendizagem.


### Pseudocódigo

<br>

**insertMatches:**

    Inicializa dados para potenciais casamentos(orders)

    Filtragem por compatibilidade de acordo com critérios(preço, quantidade, vencimento, corretora);

        Se a combinação atender aos critérios então:

            Cria casamento e adiciona à lista de casamentos potenciais;

        Return lista de casamentos potenciais;

<br>

**RemoveMatch:**

    Itera lista de casamentos atuais;

    Para(for) cada casamento na lista:

        Se a data de vencimento da order do casamento excede o limite então:

            Remove potencial casamento da lista;

            Atualiza o estado do ambiente;

        Retornar o estado atualizado do ambiente

         Senão:

            Mantém casamento;

<br>

**CompareAndReplaceMatches:**

    Verifica a lista de casamentos atuais e suas respectivas variâncias;

    Para(for) cada casamento na lista:

        Se existe uma unidade substituta que maximize a variância e se uma melhor unidade for encontrada então:

            Substituir a unidade no casamento para melhorar a diversificação;

            Atualiza o estado do ambiente para refletir as substituições;

            Retorna o estado atualizado e as recompensas associadas às substituições;


    ValidarCasamentos (Agente Validador): 

    Itera lista de casamentos atuais após ações de "insertMatches" e "RemoveMatch"

    Para cada casamento:

            Se os casamentos atendem a todos os critérios definidos

    Senão:

        aplicar penalidade(-1);

    Se todas as validações passarem, então:

        Fornece recompensa(+1)

    Registra feedback e ajusta estratégias de casamento;

<br>

**Episódio completo:**

Carrega curvas de DI para referência de cálculo da rentabilidade em %CDI
Inicializa o ambiente com o estado atual do mercado - planilhas com operações
Inicializa o agente com a política atual de decisão

    Para(for) cada episódio de treinamento até convergência:
        Inicializa as recompensas acumuladas do episódio como zero
        Obtém estado inicial do ambiente baseado em casamentos já feitos

    Enquanto(while) o estado do ambiente não estiver no estado final:
        Executar ação 'insertMatches' para formar novos casamentos
        Receber recompensa com base na qualidade dos novos casamentos
        Executar ação 'RemoveMatch' para remover casamentos vencidos
        Atualizar o estado do ambiente após remoção de casamentos
        Receber recompensa ou penalidade com base na ação de remoção
        Agente Validador executa 'CompareAndReplaceMatches'
        Receber recompensa com base na eficácia das substituições realizadas
        Ajustar a política de decisão do agente com base nas recompensas acumuladas
        Verificar condição de término do episódio ou transição para o próximo estado

    Concluir o episódio e preparar para o próximo ciclo de treinamento

    Após o término do treinamento, otimizar a política visando resultados e melhores rendimentos.
