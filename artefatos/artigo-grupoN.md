---
title: Otimização no casamento de operações de ativos de renda fixa artificial utilizando redes neurais e aprendizado por reforço
author: Gabrio Lina da Silva, Moisés Cazé de Souza Santos, Pedro Romão Cerdeira Dias, Sergio Brito Amorim Lucas, Thomas Barton, Thomas Frajhof Brand e Yasmin Vitória Rocha de Jesus
date: Fevereiro de 2024
abstract: Como parte das atividades do módulo 9, cada grupo deverá redigir um texto descrevendo os resultados do projeto no formato de um artigo científico. Este arquivo no formato markdown contém a estrutura básica deste artigo. Cada grupo deverá editar este arquivo com a descrição do projeto que desenvolveu.
---
# Introdução

O mercado financeiro oferece várias formas de interação, incluindo duas categorias comuns de ativos: renda fixa e renda variável. Os ativos de renda fixa são investimentos com retornos ou pagamentos de juros previsíveis no momento da aplicação, como CDBs ou Tesouro Direto. Por outro lado, os ativos de renda variável apresentam retornos que não são predeterminados e podem flutuar conforme as condições de mercado.

No Brasil, uma taxa crucial no mercado financeiro é o CDI (Certificado de Depósito Interbancário), que reflete a média das taxas de juros em operações de empréstimos de curto prazo entre bancos. Normalmente, os ativos de renda fixa baseiam seus rendimentos no CDI; por exemplo, se o CDI é de 6% ao ano e um ativo rende 100% do CDI, sua rentabilidade será de 6% ao ano.

Entretanto, existem estratégias no mercado de renda variável que podem simular a renda fixa, conhecidas como "renda fixa sintética". Um exemplo dessas estratégias é o "cash and carry" ou "basis trading", que é uma forma de arbitragem que envolve a compra de um ativo no mercado à vista (spot market) e a venda de um contrato futuro desse mesmo ativo. O objetivo é lucrar com o aumento do preço do ativo no futuro, aproveitando a diferença de preço entre a compra e a venda, conhecida como "basis".

Este projeto está inserido no contexto das operações cotidianas da área de fundos de investimento do banco BTG Pactual, reconhecido como o melhor banco de investimentos do Brasil por publicações de renome mundial no setor, como a Euromoney [3]. O foco está nas operações de basis trading, que são essenciais para a manutenção do ativo de renda fixa sintética do banco.

O banco centraliza várias operações de compras à vista e vendas a termo de diversos clientes e corretoras. Embora esteja garantido que estas operações tenham uma correspondência direta, conforme definido anteriormente no conceito de basis trading, ou seja, a venda de um contrato futuro de um ativo implica a compra do mesmo no mercado à vista, o grande volume de operações e a variação de suas possíveis origens dificultam o controle direto sobre qual compra corresponde a qual venda. Isso cria a necessidade de um analista realizar manualmente os casamentos entre essas operações.

Esse trabalho manual tem várias desvantagens, pois ao envolver o fator humano, aumentam-se as chances de erros e imprecisões na correspondência real das operações. Ao longo deste trabalho, será utilizado o termo "emulação da verdade" em referência à tentativa de simular o casamento correto entre as operações que efetivamente pertencem umas às outras. Essa emulação é particularmente importante em casos de homologação do fundo, pois órgãos reguladores exigem essas informações para proteger tanto o banco quanto os investidores contra possíveis fraudes.

A precisão dessa emulação da verdade é essencial para o funcionamento do ativo de renda fixa sintética. A solução proposta neste trabalho parte do princípio de que é necessário chegar o mais próximo possível da operação real que aconteceu, emulando a verdade. Dada a quantidade de dados e as possíveis complicações relacionadas às informações, alcançar a verdade absoluta é computacionalmente improvável. Portanto, o objetivo dessa emulação é atender ao padrão do mercado financeiro para taxas de juros de renda fixa, que é 100% do CDI.

Do ponto de vista técnico, considera-se este um problema que pode ser resolvido eficientemente por uma rede neural que utiliza aprendizado por reforço para se aproximar da resposta ideal, esta abordagem é embasada em literatura existente, como o trabalho de Xiaoxue Li *et al.* [4], publicado em 2020, que abordou o casamento de perfis de usuários em diferentes redes sociais com base em informações-chave como nome, rede de amigos e data de nascimento. Essa abordagem se assemelha ao projeto em questão, pois também dispõe-se de diversas informações existentes que podem ser utilizadas para determinar a possibilidade de um casamento entre os dados. No entanto, cada casamento tem um resultado específico e uma certa proximidade ao CDI.

Esse desafio também é comum na engenharia, especialmente em situações em que a previsão da produção futura de reservas de materiais, como petróleo e gás, é complicada devido a propriedades como porosidade e permeabilidade, que nem sempre têm uma relação linear ou direta com dados históricos. Esse problema é conhecido como "history matching problem" (problema de correspondência histórica). No caso do projeto em questão, embora tenham-se parâmetros mais precisos e diretamente relacionados ao problema, a análise de trabalhos como o de Omar S. Alolayan *et al.* mostra que o aprendizado por reforço pode alcançar excelente precisão mesmo em situações onde as informações não correspondem diretamente, reforçando a validade de nossa abordagem técnica.

Nas próximas seções, será detalhada a descrição do problema, abordando os dados existentes, seu tratamento atual e como a abordagem manual é realizada. Ademais, serão discutidos o planejamento, objetivos e as restrições enfrentadas ao adotar a aprendizagem por reforço através de redes neurais como esta solução.

Aprofundaremos nos trabalhos selecionados, examinando como a literatura nos apoia e de que maneira nosso estudo pode contribuir para o avanço da comunidade científica. Destacaremos as complexidades desse desafio no mercado financeiro e como sua aplicação pode beneficiar pesquisas futuras.

Além disso, justificaremos tecnicamente a escolha de nossa estratégia específica, contextualizando-a no âmbito do aprendizado por reforço. Explicaremos as decisões que o agente deve tomar para resolver o problema e avaliaremos a eficiência do nosso algoritmo do ponto de vista da complexidade e correção. Por fim, apresentaremos os resultados obtidos.

As contribuições deste artigo podem ser resumidas a seguir: 

* Propomos uma solução inovadora para o problema de casamento em operações de *basis trading* , abordando-o como uma sequência de decisões e aplicando técnicas de deep learning e aprendizado por reforço.
* Nossos experimentos utilizam mais de 10 anos de dados fornecidos pelo banco BTG Pactual, garantindo uma resposta robusta e resultados confiáveis, sustentados pelo volume de informações. Este extenso período de dados, abrangendo diferentes ciclos econômicos e flutuações de mercado, contribui para a robustez de nosso modelo, validando sua aplicabilidade e eficácia em um espectro amplo de cenários financeiros. A utilização de uma base de dados tão abrangente assegura que os resultados não sejam limitados a condições de mercado específicas, aumentando a generalização e a confiabilidade das nossas conclusões.
* A metodologia desenvolvida pode ser adaptada para resolver problemas similares de casamento em diferentes conceitos ou áreas, com base nos resultados obtidos.

# Metodologia

## Definição do problema
Ao concentrar-se em ativos sintéticos de renda fixa, tais formados pelo casamento de venda e compra de ações, vislumbra-se a dificuldade de encontrar combinações ideais para maximizar a rentabilidade que varie em torno de 100% do CDI que, neste caso, abrange negociações à vista e a termo. Para Qian (2023), a microestrutura do mercado é muito complexa e é afetada por um grande número de fatores e, como resultado, métodos tradicionais de precificação e de opções não geram preços exatos. Desse modo, o modelo de reinforcement learning serve como uma boa estrutura para analisar quais fatores podem fazer parte de um método de base útil levando em consideração atributos como preço e vencimento. 

A busca por otimizar a precificação a fim de garantir tanto a maximização da rentabilidade, quanto assegurar maior eficiência na distribuição de retorno que promove uma riqueza equitativa, pode ser exemplificada tratando de uma abordagem semelhante à otimização de portfólio. Apesar de terem aplicações diferentes, enquanto a renda fixa sintética possui foco mais específico, o portfólio de acordo com Markowitz (1952), tem por objetivo encontrar as carteiras que melhor convêm aos objetivos do investidor, este visa a amplificação, o qual envolve a seleção e combinação de diversos ativos, seja de renda-fixa ou variável. A partir disso, é possível identificar tais composições divergentes e ao mesmo tempo buscar o principal aspecto comum, ambos compartilham e permeiam desafios a respeito da otimização e o equilíbrio entre o risco e o potencial de retorno. Para resolver este problema, Araújo (2023) apresenta algoritmos como Deep Deterministic Policy Gradient (DDPG), Proximal Policy Optimization (PPO) e Policy Gradient (PG), tal estudo é elucidado por Kolm & Ritter (2019), baseando-se em problemas de otimização dinâmicos e aprendizagem por reforço a fim de solucionar aplicações financeiras. 

Embora nos últimos anos a aplicação de aprendizado por reforço ao mercado financeiro, assim como no exemplo já citado sobre gerenciamento de portfólio ainda seja limitado, em contraste, a abordagem aqui proposta, busca maneiras de como o problema de otimização de casamentos de renda-fixa sintética pode ser solucionado através da implementação de um agente capaz de explorar continuamente diferentes combinações de ativos e estratégias de precificação e diversificação para identificar aquelas que maximizam a rentabilidade em torno do CDI de 100%, isso a partir da capacidade de aprender com a experiência, principalmente com recompensas recebidas enquanto evita a subotimização e a minimização da distribuição desigual de riqueza. 


## Ambiente de Simulação

O ambiente de simulação, crucial para a interação do agente de Reinforcement Learning. Baseando-se nos princípios apresentados por Hambly et al. (2023), a estrutura foi arquitetada para projetar o dinamismo e a complexidade do problema abordado, com foco específico em operações de compra à vista e venda a termo. Utilizando a infraestrutura da biblioteca Gym da OpenAI, o ambiente é customizado para refletir as nuances das decisões de casamento, incluindo diferenças de preços, volumes de negociação e demais fatores imprescindíveis no cenário em questão. A implementação utiliza a classe `TransformedEnv` para aplicar transformações essenciais às observações do estado, incluindo normalização (`ObservationNorm`), conversão de tipos de dados (`DoubleToFloat`) e contagem de etapas para monitoramento das ações do agente (`StepCounter`), preparando o ambiente para a interação eficiente do agente. Ademais, uma etapa inicial de normalização estatística é realizada para garantir que as entradas do agente reflitam com precisão as condições do mercado, essencial para a tomada de decisões. A simulação também incorpora o calendário de negociações do mercado brasileiro através do `brazil_calendar`, obtido através da biblioteca `pandas_market_calendars` Wen et al. (2021). O que permite que o ambiente simule precisamente os dias de negociação, respeitando feriados e finais de semana, que são cruciais para calcular a duração das operações a termo e seu impacto na rentabilidade.

Alguns cálculos financeiros específicos são feitos no processo, como o Cálculo de Rentabilidade (`calc_rent`), uma função específica para calcular a rentabilidade das operações, considerando o valor de compra, o valor de venda, o índice de dias úteis (`du_idx`), e a rentabilidade do DI. Este cálculo permite ao agente avaliar o desempenho das operações em comparação ao CDI, direcionando suas estratégias para maximizar não a rentabilidade, mas sua aproximação a 100% do CDI. Além do cálculo de rentabilidade, também é feito o Cálculo de Dias Úteis (`calc_du_idx`), uma função utilizada para determinar o número de dias úteis entre a data de operação e o vencimento, utilizando o calendário de negociações brasileiro. Este cálculo é fundamental para ajustar as expectativas de rentabilidade das operações a termo, fornecendo ao agente uma base realista para suas decisões de casamento.

## Algoritmos utilizados
Após verificar diferentes algoritmos de reinforcement learning retratados em diferentes contextos da área financeira, incluindo os já citados anteriormente, nesta seção, a abordagem irá além dos quais já foram apresentados, indo de encontro com o ponto focal, dessa vez, em um conjunto diferente de algoritmos que demonstrou ser promissor para o trabalho presente. Para ilustrar a aplicabilidade do modelo no contexto de casamento de à vista e a termo em renda fixa sintética, foi selecionado o algoritmo Generalized Advantage Estimator(GAE). Y. Chen et al. (2021) define o GAE como um crítico típico do equilíbrio entre variância e viés, combinando retornos de amostra e funções de valor com um parâmetro de peso fixo. Este algoritmo foi escolhido a fim de estimar a vantagem de tomar certas ações em relação a outras, contribuindo para o aprendizado do agente em buscar as melhores políticas, Song et al. (2023), afirma que o GAE reduz substancialmente a variância das estimativas do gradiente político em detrimento do enviesamento. Sendo assim, em termos de expectativa de recompensas futuras, a vantagem é referida como uma medida do quão boa uma ação é comparada à política atual do agente para melhor alocação de ativos.

Adicionalmente, optou-se a adoção do Probabilistic Actor-Critic (PAC), Bahare et al. (2023) elucida o PAC como um algoritmo de controle contínuo aprimorado graças  à sua capacidade de mitigar o compromisso entre exploration-exploitation. O PAC consegue isso integrando perfeitamente políticas e críticas estocásticas, criando uma sinergia dinâmica entre a estimativa da incerteza crítica e o treinamento dos agentes. Ou seja, define como um agente escolhe ações em um ambiente, considerando as probabilidades das ações levarem a resultados positivos, sendo um padrão comum em políticas de aprendizado por reforço. 

Ademais, em outro estudo, salienta-se o uso do Q-learning, um dos algoritmos mais famosos, Yamagata et. al (2023) define o algoritmo Q-learning como um procedimento que estima os valores de Q para cada ação em cada estado de um processo de decisão de Markov (MDP), sem a necessidade de um modelo do ambiente. Ele é descrito como um método fora da política, o que significa que aprende a política ótima enquanto comporta-se seguindo outra política. Nesse sentido, se torna útil para o mercado financeiro, visto que maximiza a recompensa total acumulada ao longo do tempo. Este algoritmo a princípio, foi uma das apostas consideradas promissoras para concretizar o atual modelo.

Ao implementar esses algoritmos, foi feito uso de bibliotecas auxiliares para que o processo seja realizado, tal como Pytorch, torchrl e Gym, sendo referências extraídas de outros trabalhos que utilizaram tais bibliotecas. Macaluso (2020) projeta um sistema de controle para Cozmo um pequeno robô de brinquedo desenvolvido pela empresa Anki, explorando o Cozmo SDK, PyTorch e OpenAI Gym para construir um ambiente padronizado no qual aplicar qualquer algoritmo de aprendizagem por reforço. Já com torchrl, é introduzido por Moens (2023) como uma biblioteca de controle generalista para PyTorch que fornece componentes bem integrados, mas independentes. Dessa maneira, tanto GAE quanto PAC são métodos adotados e apoiados por ferramentas como PyTorch e Gym que permitem uma tomada de decisão mais eficaz na seleção de combinações de ativos à vista e a termo, buscando maximizar retornos, assim como gerenciar eficientemente o trade-off em explorar novas oportunidades e as já existentes. Ademais resulta na otimização contínua, visto que é guiada por uma avaliação de recompensa de cada ação tomada pelo agente, equipando o modelo a fim de identificar e aproveitar as melhores combinações.

## Arquitetura do Agente

A arquitetura do agente de RL é projetada para decifrar eficientemente o espaço de estados complexo derivado do mercado financeiro e tomar decisões informadas de casamento. No coração desta arquitetura, uma rede neural profunda é empregada para processar as observações do estado e gerar ações de análise das variáveis de estado - preços dos ativos, volumes de negociação e demais indicadores.

As variáveis que constituem o espaço de estados são especialmente selecionadas para refletir elementos. Essas variáveis são integradas em um espaço contínuo, configurado por meio da utilização da `observation_space` da biblioteca `Gym` da OpenAI. Esse espaço é definido como `gym.spaces.Box`, caracterizando assim a alta dimensionalidade e a natureza contínua das informações que o agente deve avaliar. Essa representação detalhada permite que o agente receba e processe informações complexas do ambiente, fundamentais para a formulação de estratégias de decisão.

O espaço de ações, por sua vez, é configurado para permitir ao agente realizar operações de junção ou disjunção, refletindo a natureza multifacetada das decisões do problema abordado Hambly et al. (2023). Este espaço, também definido como um `gym.spaces.Box` com limites entre 0 e 1, indica a capacidade do agente de tomar ações que são frações de uma ação máxima, possibilitando uma alocação de recursos de maneira precisa e estratégica.

Além disso, a arquitetura do agente incorpora um sistema de recompensas projetado para quantificar o sucesso dos casamentos em relação ao objetivo de rendimento. A função de recompensa avalia a rentabilidade dos casamentos do agente em comparação à taxa definida como benchmark, incentivando o agente a aprender e implementar estratégias que visem a aproximação máxima de uma rentabilidade de 100% do CDI.

O mecanismo de decisão do agente, apoiado pela rede neural profunda e pelo algoritmo de otimização Proximal Policy Optimization (PPO), habilita uma exploração equilibrada do espaço de ações e a otimização da política de ação do agente. Esse processo de aprendizado iterativo e a capacidade de ajustar estratégias com base na análise contínua das variáveis de estado são fundamentais para a capacidade do agente de adaptar-se e prosperar no complexo ambiente de casamentos.

## Configuração Experimental

A configuração experimental define o cenário sob o qual o agente é meticulosamente treinado e avaliado, alinhando-se com os objetivos específicos do estudo que visa otimizar estratégias de casamento das dadas operações financeiras.

Para garantir um treinamento eficaz do agente, uma série de parâmetros de treinamento são cuidadosamente selecionados e aplicados ao longo do processo, como a taxa de aprendizado (`lr`), configurada para 1e<sup>⁻5</sup>, valor escolhido para promover uma convergência suave e estável durante o treinamento do agente, evitando oscilações excessivas nos pesos da rede neural.

O Tamanho do Batch (`frames_per_batch`) foi definido em 1.000 frames por batch, equilibrando a eficiência computacional com a capacidade de aprendizado, permitindo ao agente absorver e integrar conhecimento de um volume substancial de dados por etapa de treinamento. 
O Número Total de Frames (`total_frames`), por sua vez, foi definido com um limite de 300.000, a fim de definir a duração total do treinamento, assegurando exposição e interação extensivas com o ambiente de simulação.

A estratégia de otimização escolhida é o Proximal Policy Optimization (PPO), que costuma ser notada por sua eficácia e estabilidade em ambientes de ação contínua e discreta Meng & Khushi (2019). Os parâmetros específicos do PPO, como o tamanho do sub-batch (`sub_batch_size` = 128), o número de épocas por batch de dados coletados (`num_epochs` = 10), e o clip epsilon (`clip_epsilon` = 0.2), são ajustados para otimizar o equilíbrio entre exploração e explotação, promovendo o aprendizado de estratégias de casamento eficientes e robustas.

## Métricas utilizadas
Para avaliar o desempenho de agentes em contextos de aprendizado por reforço, é essencial discutir como as métricas, sendo representadas pela função de recompensa, taxa de exploração e tempo de convergência são fundamentais para a compreensão e avanço da área. Nesta seção, o trabalho desenvolvido englobando métricas que medem o desempenho de um agente se baseia na análise feita por Henderson et al. (2017), que enfatiza a importância da reprodutibilidade e da avaliação precisa em aprendizado por reforço profundo. Esta metrificação pontua os principais aspectos que se diferem e se complementam, a recompensa acumulada reflete com que o agente maximiza a soma de recompensas ao longo do tempo, representando sua capacidade geral de alcançar o objetivo desejado. Ela é um indicador direto da habilidade do agente em cumprir a tarefa designada que neste caso, busca estabelecer os melhores casamentos a partir de diversas iterações e comparações até chegar em uma combinação. Já o tempo de convergência mede o período necessário para que o agente aprenda uma política ótima. Esta métrica é crucial para entender a eficiência do aprendizado, indicando quão rapidamente um agente pode adaptar-se e otimizar seu comportamento em resposta ao ambiente. 

Por fim, a taxa de exploração diz respeito ao balanceamento da exploração do espaço de ações com a explotação de ações conhecidas para maximizar a recompensa. Uma taxa de exploração bem ajustada permite ao agente descobrir novas estratégias potencialmente recompensadoras, enquanto evita ficar preso em espaços limitados. Dados tais detalhes, assimila-se que as métricas abordadas foram empregadas com cenário adaptado que se difere da maioria dos procedimentos existentes envolvendo a área financeira, mais especificamente de renda fixa-sintética.


# Descrição do problema

# Trabalhos relacionados

# Descrição da estratégia adotada para resolver o problema

# Análise da complexidade da solução proposta

Neste artigo, cada grupo precisará fazer a análise de complexidade da solução proposta, utilizando as notações $O(.)$, $\Omega(.)$ e $\Theta(.)$.

A seguir temos a citação de alguns trechos de DASGUPTA et. al. (2011) para mostrar como estas notações são em \LaTeX.

> Sejam $f(n)$ e $g(n)$ duas funções de inteiros positivos em reais positivos. Dizemos que $f = O(g)$ (que significa que "$f$ não cresce mais rápido do que $g$") se existe uma constante $c > 0$ tal que $f(n) \leq c \cdot g(n)$.

Ainda em outro trecho de DASGUPTA et. al. (2011), temos:

> Assim como $O(.)$ é análogo a $\leq$, podemos definir análogos de $\geq$ e $=$ como se segue:

> $f = \Omega(g)$ significa $g = O(f)$

# Análise da corretude da solução proposta

# Resultados obtidos

# Conclusão

# Referências Bibliográficas

1. Alolayan, Omar S.; ALOMAR, Abdullah O.; WILLIAMS, John R. Parallel Automatic History Matching Algorithm Using Reinforcement Learning.  **AI Technologies in Oil and Gas Geological Engineering** , [ *s. l.* ], 12 jan. 2023. DOI https://doi.org/10.3390/en16020860. Disponível em: https://www.mdpi.com/1996-1073/16/2/860. Acesso em: 29 fev. 2024.

Araújo, Thiago. Otimização de portfólio financeiro utilizando aprendizado por reforço, 2023. Disponível em: https://lume.ufrgs.br/handle/10183/271947

Bahare et al., 2023. Probabilistic Actor-Critic: Learning to Explore with PAC-Bayes Uncertainty. Disponível em: https://arxiv.org/abs/2402.03055

EUROMONEY. **Awards for Excellence 2019: Best Investment Bank in Brazil.** [ *S. l.* ], 10 jul. 2019. Disponível em: https://www.euromoney.com/article/b1gd2y7b6c7rjz/awards-for-excellence-2019-best-investment-bank-in-brazil. Acesso em: 29 fev. 2024.

H. Markowitz. Portfolio selection. J. Finance, 7(1):77–91, 1952. Disponível em: https://edisciplinas.usp.br/pluginfile.php/2663149/mod_resource/content/1/HarryMarkowitz_1952.pdf

Hambly, B., Xu, R., & Yang, H.,2023. Recent advances in reinforcement learning in finance. Mathematical Finance, 33, 437–503. https://doi.org/10.1111/mafi.12382 

Henderson et al., 2017. Deep Reinforcement Learning that Matters. Disponível em: https://arxiv.org/abs/1709.06560

Kolm & Ritter, 2019. Modern Perspectives on Reinforcement Learning in Finance. Disponível em: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3449401

Li, Shengbo Eben. Deep reinforcement learning, 2023. In: Reinforcement Learning for Sequential Decision and Optimal Control. Singapore: Springer Nature Singapore, 2023. p. 365-402.

Li, Xiaoxue; CAO, Yanan; LI, Qian; SHANG, Yanmin; LI, Yangxi; LIU, Yanbing; XU, Guandong. RLINK: Deep reinforcement learning for user identity linkage. World Wide Web, [s. l.], 7 ago., 2020. DOI https://doi.org/10.1007/s11280-020-00833-8. Disponível em: https://link.springer.com/article/10.1007/s11280-020-00833-8. Acesso em: 29 fev. 2024.

LUO, Fan-Ming et al. A survey on model-based reinforcement learning. Science China Information Sciences, v. 67, n. 2, p. 121101, 2024.

Macaluso, Piero. DEEP REINFORCEMENT LEARNING FOR AUTONOMOUS SYSTEMS, 2020. Disponível em: https://webthesis.biblio.polito.it/14352/

Meng TL, Khushi M. Reinforcement Learning in Financial Markets. Data. 2019; 4(3):110. https://doi.org/10.3390/data4030110 

Moens, Vincent. TorchRL: A data-driven decision-making library for PyTorch, 2023. Disponível em: https://arxiv.org/abs/2306.00577

Qian, Samson. Multi-Agent Deep Reinforcement Learning and GAN-Based Market Simulation for Derivatives Pricing and Dynamic Hedging, 2023. Disponível em: https://dspace.mit.edu/handle/1721.1/150206

Song et al., 2023. Partial advantage estimator for proximal policy optimization. Disponível em: https://arxiv.org/abs/2301.10920

Wen, W., Yuan, Y., & Yang, J. Reinforcement Learning for Options Trading, 2021. Applied Sciences, 11(23), 11208. https://doi.org/10.3390/app112311208

Y. Chen et al., 2021. Adaptive Advantage Estimation for Actor-Critic Algorithms. Disponível em: https://ieeexplore.ieee.org/document/9534005

Yamagata et al., 2023. Q-learning Decision Transformer: Leveraging Dynamic Programming for Conditional Sequence Modelling in Offline RL.Disponível em: https://proceedings.mlr.press/v202/yamagata23a.html














