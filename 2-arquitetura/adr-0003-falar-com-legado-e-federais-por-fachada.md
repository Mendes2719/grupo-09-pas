# ADR 0003: falar com o legado de regulação e com os federais por uma fachada com camada anticorrupção

**Status:** aceito

**Contexto:** O sistema legado de regulação não pode ser desligado e expõe uma API antiga e pouco documentada. Os sistemas federais de saúde têm janelas de indisponibilidade conhecidas e contrato formal, e a notificação compulsória precisa sair em até 24 horas. O prazo do envelope para substituir o legado é de dois anos, com dez desenvolvedores e duas pessoas de infraestrutura. Nenhum sistema externo está sob a nossa autoridade para mudar.

**Decisão:** Concentrar toda saída para o legado e para os federais em uma fachada de integração única, que carrega a camada anticorrupção e a tabela de roteamento do estrangulamento, e proibir por regra verificada que qualquer outro componente fale diretamente com eles. Aplicar na fachada, nesta ordem, tempo limite, retentativa com recuo exponencial, disjuntor, anteparo e limitação de taxa.

**Fronteiras desta composição:** o barramento de serviços entra apenas nesta fachada, na forma reduzida de gateway e tradução, e nunca como produto de ESB com orquestração. Nenhuma regra de negócio vive na fachada. A camada anticorrupção termina na interface pública dos módulos: o vocabulário do legado não atravessa essa linha em nenhuma direção.

**Alternativas consideradas:**
- Cada módulo chamando o legado direto: descartada porque a tabela de roteamento do estrangulamento só funciona se todo o tráfego passar por um ponto, e porque o modelo do legado contaminaria o domínio, com códigos de uma letra e datas numéricas.
- Produto de ESB completo com orquestração e regra no barramento: descartada pela seção 10.6, porque a equipe do barramento viraria gargalo de qualquer mudança e o acoplamento reapareceria concentrado no centro. Era a alternativa competitiva, porque o cenário de integração heterogênea é exatamente o que a seção 10.5 descreve.
- Escrita dupla no banco antigo e no novo durante a migração: descartada pela seção 19.5, porque não existe transação atômica entre dois armazenamentos independentes e a divergência resultante é silenciosa.
- Reescrever a regulação de uma vez e desligar o legado: descartada porque o envelope proíbe o desligamento, e porque a seção 19.1 mostra que durante a reescrita a equipe passa a manter duas bases ao mesmo tempo, com o valor chegando só no fim.

**Consequências:**
- Positivas: um ponto único e verificável de autenticação, autorização e trilha para toda troca externa, que é o que a auditoria sanitária cobra; a queda de um sistema federal não trava a unidade, porque a fila segura e o disjuntor recusa rápido; a fachada é barata de instalar e fácil de reverter, já que começa repassando tudo ao legado sem mudar comportamento.
- Negativas: um salto extra em cada chamada externa, com o custo de latência que a seção 19.6 manda transformar em orçamento verificado; a fachada é ponto central e precisa de redundância própria; a camada anticorrupção exige escrever e manter tradução nos dois sentidos sobre uma API que ninguém documentou, o que só se descobre por teste; toda essa estrutura é transitória e precisa nascer com data de remoção, sob pena de virar permanente.
