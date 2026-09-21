# ADR 0001: adotar monolito modular no núcleo, com nó local separado na UPA

**Status:** aceito

**Contexto:** A rede tem 70 UBS, 5 UPAs e um hospital de referência, com 12 mil atendimentos por dia e sete subdomínios de naturezas distintas. A equipe é de dez desenvolvedores e duas pessoas de infraestrutura, em servidores próprios sem nuvem pública e com orçamento anual fixo. As UBS têm internet instável, com quedas diárias de minutos a horas, e a UPA precisa triar e atender com a rede fora do ar. Não existe hoje observabilidade distribuída, malha de serviços nem entrega contínua de vários artefatos.

**Decisão:** Construir o núcleo da rede como um monolito modular em uma única unidade de implantação, com cadastro e prontuário, regulação, farmácia, vigilância e agendamento como módulos de fronteira verificada, cada um organizado por dentro como aplicação hexagonal. Manter o nó local da UPA como uma segunda unidade de implantação, uma instância por UPA, organizada em camadas, comunicando-se com o núcleo apenas por evento.

**Fronteiras desta composição:** o monolito modular termina no limite do processo do núcleo; dentro dele, cada módulo é um hexágono cujo domínio não conhece banco, tela nem barramento. O nó da UPA começa onde a rede deixa de ser confiável, e cobre apenas triagem e atendimento; tudo que exige estado global, como reserva de leito, fica fora dele. Entre as duas unidades só existe conector de evento, nunca chamada síncrona.

**Alternativas consideradas:**
- Microsserviços: descartada porque a seção 9.5 trata plataforma pronta como pré-requisito e a seção 9.6 diz que com time pequeno o custo fixo consome a capacidade de entrega sem devolver nada. Era a alternativa competitiva, dada a diferença de natureza entre os subdomínios.
- Monolito em camadas para a rede inteira: descartada pela seção 5.6, porque os perfis de carga são muito distintos, com campanha de 20 vezes ao lado da regulação, e em camadas só se escala o conjunto.
- Núcleo único incluindo a UPA: descartada porque a seção 6.6 mostra que os módulos dividem processo e memória e o raio de impacto é o sistema inteiro, o que deixaria a UPA sem atendimento a cada queda de rede ou incidente no núcleo.
- Arquitetura celular com uma célula por unidade: descartada pela seção 13.6, porque o domínio exige consultas que atravessam todas as unidades, e porque a seção 13.7 mostra que N instalações completas não cabem em duas pessoas de infraestrutura.

**Consequências:**
- Positivas: modificabilidade e testabilidade altas com custo operacional baixo, que são as três moedas escassas do envelope; transação local cobrindo prontuário, farmácia e agendamento, sem saga; módulos com fronteira verificada já são candidatos naturais à extração futura por estrangulamento, conforme a seção 6.9.
- Negativas: o núcleo escala inteiro ou não escala, e um vazamento de memória em um módulo derruba os demais; a implantabilidade é baixa, porque qualquer entrega passa por um artefato só; o nó da UPA introduz consistência eventual entre a unidade e o núcleo, com todo o custo de idempotência que a seção 11.7 descreve; passamos a manter duas bases de código com ciclos de vida diferentes.
