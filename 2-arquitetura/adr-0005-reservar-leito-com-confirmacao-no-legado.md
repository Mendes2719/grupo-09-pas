# ADR 0005: reservar leito por concorrência otimista local confirmada no legado

**Status:** aceito

**Contexto:** São 400 leitos regulados e unidades disputando leito em tempo real, com a regra de que um leito só pode ser reservado por um paciente por vez. O sistema legado de regulação não pode ser desligado e continua recebendo reservas pelo terminal antigo, feitas por pessoas que não usam o nosso sistema. A API do legado é antiga, pouco documentada e não oferece operação idempotente nem chave de requisição. Uma dupla reserva não é erro de dado: é risco clínico, e não se corrige por retentativa.

**Decisão:** Serializar as disputas internas com concorrência otimista sobre uma versão por leito, gravando uma intenção de reserva em transação local, e só confirmar a reserva ao usuário depois que o legado aceitar a chamada feita pela fachada com chave de correlação determinística. Em caso de tempo limite, nunca repetir cegamente: reconciliar lendo de volta o estado do leito no legado e comparar o ocupante com a nossa chave.

**Alternativas consideradas:**
- Tratar o nosso banco como autoridade da ocupação e sincronizar com o legado depois: descartada porque o terminal antigo continua reservando por fora, e qualquer atraso de sincronização vira dupla reserva. Era a alternativa mais simples de implementar, e por isso a mais perigosa.
- Bloqueio distribuído entre o nosso sistema e o legado: descartada porque exigiria que o legado participasse do protocolo, e não temos autoridade nem documentação para alterá-lo.
- Reserva por evento assíncrono, com saga de compensação: descartada pela seção 11.6, que recusa evento quando há necessidade de resposta imediata e consistência forte entre componentes, e porque compensar uma reserva de leito significa desfazer uma decisão clínica já comunicada.
- Confirmar ao usuário logo após a intenção local, deixando a confirmação no legado em segundo plano: descartada porque anunciaria como garantido um leito que o legado ainda pode recusar. Era a alternativa competitiva, porque melhora muito o tempo de resposta percebido.
- Repetir a chamada após tempo limite com recuo exponencial, sem leitura de volta: descartada pela seção 18.4, que exige idempotência da operação chamada para que a retentativa seja segura, e a API do legado não a oferece.

**Consequências:**
- Positivas: o invariante de não reservar duas vezes é sustentado mesmo com um escritor concorrente fora do nosso controle; a rejeição por conflito de versão é explícita e tratável pela tela, em vez de silenciosa; o mecanismo continua válido depois que a reserva migrar para o nosso lado, porque a autoridade muda de endereço mas o protocolo não.
- Negativas: a reserva passa a ter dois tempos, e o usuário vê um estado intermediário de espera pela regulação; a leitura de volta dobra o número de chamadas ao legado nos casos de falha, justamente quando ele está mais lento; sob contenção alta no mesmo leito a taxa de rejeição por conflito sobe, e a tela precisa tratar isso com nova tentativa; se o legado perder a nossa chave de correlação em algum caminho não documentado, a reconciliação fica ambígua e exige intervenção humana, que é o cenário residual que aceitamos.

**Verificação:** esta é a decisão mais arriscada do projeto e é a provada pelo código pequeno da [Entrega 3](../3-spike/), que executa cenários de disputa simultânea, de escrita concorrente pelo terminal do legado e de tempo limite ambíguo, e verifica ao final de cada um que nenhum leito ficou com dois pacientes.
