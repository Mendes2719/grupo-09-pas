# ADR 0002: registrar o prontuário como trilha somente acréscimo e manter um dono por dado

**Status:** aceito

**Contexto:** O prontuário tem guarda obrigatória por 20 anos e exige saber quem viu e quem alterou cada registro, sob auditoria sanitária. O mesmo dado é lido por equipes diferentes, e a vigilância precisa de relatórios por bairro e período enquanto o agendamento sofre pico de 20 vezes em campanha. O prontuário é dado sensível sob a LGPD, e a retenção legal convive com o direito de acesso do paciente. Hoje cada unidade guarda o seu próprio registro e o prontuário não circula.

**Decisão:** Guardar o histórico clínico como uma trilha de alterações somente acréscimo, da qual o estado atual é reproduzido, e registrar os acessos de leitura em uma segunda trilha separada. Dar a cada módulo um esquema próprio no Banco da Rede, sem consulta cruzada entre esquemas, e manter modelo de leitura separado apenas para vigilância e agendamento.

**Fronteiras desta composição:** event sourcing vale somente dentro do módulo de cadastro e prontuário, e termina na interface pública dele. CQRS vale somente em vigilância e agendamento, com os dois modelos no mesmo processo. Regulação de leitos e farmácia ficam fora dos dois, com leitura e escrita no mesmo modelo e consistência imediata. Pipes and filters vale apenas na construção das projeções de vigilância.

**Alternativas consideradas:**
- Estado atual sobrescrito com uma tabela de auditoria ao lado: descartada porque a trilha vira um campo que alguém pode esquecer de gravar, enquanto a seção 15.1 coloca a sequência de eventos como a própria fonte de verdade. Era a alternativa competitiva, por ser mais barata.
- Event sourcing no sistema inteiro: descartada pela seção 15.6, que chama a generalização de erro de adoção mais comum e mostra que cadastro resolvido pelo estado atual não paga o preço.
- CQRS no sistema inteiro: descartada pela seção 14.6, que classifica isso como erro de escopo, e porque leitura que precisa refletir a escrita na hora, como saldo de leito e receita válida, não tolera atraso de projeção.
- Registrar o acesso de leitura como evento de domínio na mesma trilha: descartada porque leitura não muda o estado do agregado e porque inflaria o fluxo com milhões de linhas, agravando o crescimento de armazenamento que a seção 15.7 já aponta.

**Consequências:**
- Positivas: a trilha de alterações responde diretamente ao requisito de auditoria do caso; perguntas retroativas sobre dados de meses atrás ficam possíveis, conforme a seção 15.5; os esquemas por módulo preparam a extração futura descrita na seção 6.9.
- Negativas: o armazenamento cresce sem parar contra uma guarda de 20 anos em servidores próprios com orçamento fixo, e snapshots, retenção e reprocessamento viram rotina; a curva de aprendizado é alta para um time de dez pessoas; a exclusão de dado pessoal exige manter o dado fora do fluxo ou usar destruição criptográfica com chave por titular, que acrescenta cifra em toda leitura e escrita mais gestão de chaves; o atraso da projeção de vigilância e agendamento vira requisito a ser medido e tratado como incidente.
