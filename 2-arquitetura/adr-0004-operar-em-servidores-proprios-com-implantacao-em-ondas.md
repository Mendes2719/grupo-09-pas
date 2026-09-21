# ADR 0004: operar em servidores próprios com implantação em ondas e observabilidade por correlação

**Status:** aceito

**Contexto:** Os dados ficam no data center municipal, sem nuvem pública, por exigência legal, e o orçamento é anual e fixo. A operação é feita por duas pessoas. São 76 unidades, sendo 70 UBS com internet instável e 5 UPAs com nó local. A arquitetura usa um barramento de eventos, que é infraestrutura com estado. A migração do legado dura dois anos e atravessa trocas de pessoas.

**Decisão:** Implantar o núcleo como artefato único com um pipeline só, e distribuir o nó da UPA em ondas, com tempo de observação entre unidades antes de seguir. Exigir identificador de correlação em toda requisição e em todo evento, e tratar três funções de aptidão como critério de aceitação no mesmo pipeline dos testes: dependência entre módulos, dependência com o legado fora da camada anticorrupção, e orçamento de latência das capacidades migradas.

**Alternativas consideradas:**
- Implantar em todas as 76 unidades de uma vez: descartada porque a seção 13.5 mostra que implantação que já causou indisponibilidade total precisa virar experimento com população limitada, e uma falha simultânea em 76 unidades de saúde não tem rollback aceitável.
- Arquitetura celular completa, com célula por unidade e roteador: descartada pela seção 13.7, porque N instalações completas para observar, atualizar e diagnosticar não cabem em duas pessoas. Era a alternativa competitiva, e ficamos apenas com a disciplina de ondas que ela ensina.
- Plataforma de contêineres com observabilidade distribuída no data center: descartada porque seria assumir o custo operacional de microsserviços sem ter microsserviços, exatamente o que a seção 9.7 descreve como conta que não fecha.
- Observabilidade só por log de aplicação, sem correlação: descartada pela seção 11.7, que trata identificador de correlação e métrica de atraso por consumidor como pré-requisito, e não como melhoria posterior, em qualquer topologia orientada a eventos.

**Consequências:**
- Positivas: uma entrega do núcleo exige um pipeline e um conjunto de métricas, que é o que duas pessoas conseguem sustentar; a onda transforma cada implantação do nó da UPA em experimento com população limitada; as funções de aptidão impedem que a fronteira entre módulos e a fronteira com o legado apodreçam em silêncio ao longo dos dois anos.
- Negativas: a implantação em ondas alonga o ciclo de entrega, porque cada onda exige tempo de observação; o barramento passa a ser infraestrutura crítica com estado, com retenção, partições e monitoramento de atraso a cargo das mesmas duas pessoas, e é o maior risco operacional que assumimos; durante as ondas convivem duas versões do nó da UPA, o que obriga o contrato de evento a ser compatível para trás.
