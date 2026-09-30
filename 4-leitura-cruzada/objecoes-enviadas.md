# Entrega 4a: objeções enviadas ao Grupo 04

**Grupo 09** (Saúde, envelope C) revisando o **Grupo 04** (Saúde, envelope D).

Recebemos o PDF do documento de arquitetura, o PDF do spike, o `exemplo.py` e a `saida-esperada.txt`. Os ADRs e os arquivos `.mmd` citados no documento não vieram no pacote, então as objeções se apoiam nas seções do documento e no código. Todas levam em conta o envelope D: empresa que vende para várias cidades, 25 desenvolvedores em 3 times, nuvem pública multirregião, clientes de 10 a 200 unidades e a exigência de que uma cidade não derrube a outra.

## Objeção 1: não está definido quem escolhe a célula de cada requisição

**Trecho atacado.** Documento, seções 1, 8 e 11: o catálogo regional "mantém uma rota para a célula de cada cidade", o plano de controle "não transporta o tráfego clínico de rotina" e, se ele cair, "células já provisionadas continuam operando". No `exemplo.py`, uma única `CellRouter` roteia todas as cidades.

**Argumento.** Toda requisição precisa descobrir a célula da sua cidade antes de chegar lá. Se essa consulta vai ao catálogo, o plano de controle está no caminho clínico, o que contradiz a seção 1. Se o roteamento é um componente separado, ele é a única peça compartilhada por todas as cidades, e uma falha ou uma implantação ruim nele derruba todas ao mesmo tempo, que é o que o envelope D proíbe. O documento não diz onde esse componente roda, como é replicado nem o que acontece quando o catálogo está fora.

**O que teríamos feito.** Registrar o roteador em ADR próprio, seguindo a seção 13.7 do livro: fino, replicado, com meta de disponibilidade maior que a de qualquer célula e com o mapa de rotas em memória, carregado de forma assíncrona. Com isso a queda do catálogo impede cadastrar cliente novo, mas não impede o roteamento. Uma opção mais simples seria resolver a célula pelo subdomínio de cada cidade no DNS, sem roteador na aplicação.

## Objeção 2: o spike não tem como falhar

**Trecho atacado.** `exemplo.py`, função `run_simulation`, e a seção "O que aconteceria se a decisão estivesse errada?" do PDF do spike.

**Argumento.** As duas células são dois objetos Python sem nada em comum, e a falha de A é só `city_a.failed = True`. B continuar processando é consequência de como o código foi montado, e não da decisão de arquitetura. O PDF diz que com filas compartilhadas a falha de A poderia bloquear B, mas esse cenário nunca é executado. O evento `B-cross`, que o comentário apresenta como tenant incorreto, tem tenant `cidade-b` e vai para B normalmente. E como `Cell.enqueue` já recusa tenant errado antes da fila, o ramo que preenche `rejected` nunca executa. A verificação final compara contagens fixas (`len(city_b.processed) == 5`) em vez de medir se B foi afetado. A seção 11 do documento diz que o maior risco é o isolamento de tenant, e o spike não chega a exercitar isso.

**O que teríamos feito.** Simular o recurso que é compartilhado de verdade no desenho, como o roteador ou um pool de conexões com cota por tenant, e rodar o pico de A duas vezes, com e sem a cota, mostrando que só com a cota a vazão de B se mantém. Também testaríamos a regra da seção 3, mandando uma requisição com um tenant no corpo diferente do tenant do token e conferindo a recusa.

## Objeção 3: uma célula por cidade não combina com clientes de 10 a 200 unidades

**Trecho atacado.** Documento, seções 1 e 5 ("Cada cidade recebe uma célula") e mapa 9.1 ("células por cidade e catálogo regional").

**Argumento.** Cada célula tem gateway, seis serviços, barramento, banco transacional, projeções e adaptadores. Uma secretaria com 10 unidades paga a mesma estrutura fixa de uma com 200. A seção 13.7 do livro lembra que cada célula replica os componentes redundantes, perde economia de escala e ainda precisa de folga de capacidade, e a seção 13.6 diz que o estilo não compensa quando a base cabe em uma instalação bem dimensionada, que é o caso das cidades pequenas. O próprio documento parece prever mais de um cliente por célula, já que fala em filas e armazenamento "particionados por tenant_id" dentro dela, o que não faria sentido com uma cidade só.

**O que teríamos feito.** Separar por porte. Cidades grandes ganham célula própria; as pequenas dividem uma célula, com anteparo por tenant (cota de fila, de concorrência e de conexões, seção 18.4) para que o pico de uma não consuma a capacidade das outras. A seção 13.1 define célula como um subconjunto fixo de clientes, que pode ter mais de um. Deixaríamos escrito desde o início o critério para promover um cliente a célula própria, porque a seção 13.6 avisa que mover cliente entre células é um projeto, e não um comando.

## Objeção 4: seis serviços por célula multiplicam a operação para três times

**Trecho atacado.** Documento, seções 1 e 3: cada célula tem os serviços de prontuário, atendimento, regulação, farmácia, agendamento e vigilância, e "microsserviços estabelecem fronteiras de domínio dentro de cada célula".

**Argumento.** Com vinte cidades clientes, por exemplo, seriam 120 implantações de serviço, vinte barramentos e vinte bancos para três times acompanharem. A seção 13.9 do livro diz que, quanto mais simples o interior da célula, mais barata fica a operação de muitas células, e a seção 9.7 aponta como sinal de que a conta não fecha ter mais serviços do que gente capaz de operá-los. Pela observação de Conway citada na seção 9.5, três times tendem a produzir três fronteiras, e não seis.

**O que teríamos feito.** Reduzir o interior da célula a poucas unidades alinhadas aos três times, por exemplo uma clínica (prontuário, atendimento e farmácia), uma de regulação e uma de agendamento e vigilância, ou então um monolito modular por célula. Só separaríamos em serviço próprio o que precisa escalar sozinho, como o agendamento durante a campanha.

## Objeção 5: a reserva de leito tem dois donos enquanto o legado estiver ativo

**Trecho atacado.** Documento, seção 10.2 ("O serviço de regulação é o único dono da reserva... O legado é consultado e reconciliado pelo adaptador") e seção 6.

**Argumento.** O caso diz que o legado de regulação continua ativo por até dois anos, e o documento não diz que ele para de aceitar reservas. Se os usuários do legado continuam reservando por ele, há dois lugares gravando reserva do mesmo leito, e a restrição única (tenant_id, leito_id, intervalo_ativo) só protege o banco novo. Reconciliar depois significa descobrir a dupla reserva quando ela já aconteceu. O documento também não trata a chamada ao legado que dá tempo limite sem que se saiba se ela foi aplicada. A seção 18.4 do livro diz que repetir só é seguro quando a operação é idempotente, e a API antiga não garante isso.

**O que teríamos feito.** Definir, para cada cliente, em que fase da migração a reserva é decidida pelo legado e quando passa a ser decidida pelo serviço novo, nunca pelos dois ao mesmo tempo. Enquanto quem decide for o legado, o serviço novo só confirma a reserva ao usuário depois que o legado aceitar, e diante de tempo limite lê o estado do leito no legado antes de tentar de novo.

## Objeção 6: um adaptador só para o legado, mas cada cliente tem o seu

**Trecho atacado.** Documento, seções 6 e 10.5: "o adaptador do legado" e "o anti-corruption layer [...] traduz a API antiga", sempre no singular.

**Argumento.** No envelope D o sistema é vendido para várias secretarias, e o legado de regulação é de cada cliente, não da empresa. Nada garante que duas cidades usem o mesmo sistema, a mesma versão ou a mesma API, e algumas podem nem ter um. Um adaptador único precisa mudar a cada cliente novo, e uma mudança feita para uma cidade pode quebrar a integração de outra, o que é mais uma forma de uma cidade afetar a outra.

**O que teríamos feito.** Tratar a integração com o legado como ponto de extensão por cliente. É o caso que a seção 8.5 do livro descreve para o microkernel: regras que se multiplicam por cliente cabem em plugins, com um núcleo estável e contrato versionado. Cada célula carregaria só o adaptador do seu cliente, e o teste de conformidade com o contrato da seção 8.7 rodaria para cada adaptador antes de ir para produção.

## Objeção 7: o pico da campanha é de escrita, e o CQRS só resolve a leitura

**Trecho atacado.** Documento, seção 3 ("CQRS existe apenas em consultas com pico ou agregações caras"), seção 8 (escalonamento por fila e latência dentro da célula) e mapa 9.1 ("CQRS seletivo, projeções e escalonamento orientado por fila").

**Argumento.** Na campanha o cidadão não só consulta vagas, ele agenda, e as vagas são limitadas. Isso é escrita concorrente sobre os mesmos registros, no banco transacional da célula. As projeções aliviam a consulta, e mais réplicas do serviço não aumentam a capacidade do banco. Com concorrência otimista, quanto mais gente disputando a mesma vaga, maior a taxa de conflito, como a seção 15.5 do livro observa. O envelope pergunta como escalar só onde precisa, e o documento não diz como o banco de uma cidade em campanha aguenta vinte vezes a carga de agendamento.

**O que teríamos feito.** Controlar a entrada no agendamento com limitação de taxa e resposta clara de quando tentar de novo (seção 18.4), em vez de deixar todo mundo disputar ao mesmo tempo. Distribuir as vagas por unidade e por dia, para a disputa não se concentrar nos mesmos registros. E, como campanha tem data marcada, aumentar antes a capacidade do banco da célula que vai entrar em campanha, o que a nuvem do envelope D permite.
