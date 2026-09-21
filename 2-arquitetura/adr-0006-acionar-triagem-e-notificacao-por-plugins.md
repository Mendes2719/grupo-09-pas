# ADR 0006: acionar protocolo de triagem e regra de notificação por plugins registrados

**Status:** aceito

**Contexto:** A lista de doenças de notificação compulsória e os protocolos de classificação de risco mudam por norma sanitária, em ritmo próprio, que não coincide com o calendário de entrega do sistema. Uma mudança de norma costuma ter prazo curto de vigência e atinge as 76 unidades ao mesmo tempo. O restante do fluxo de triagem e de notificação é estável e igual para todos os agravos.

**Decisão:** Manter o fluxo comum de triagem e de notificação no núcleo do módulo, sem conhecer nenhum agravo nem protocolo pelo nome, e acionar cada variação por um plugin registrado em um contrato versionado, carregado por configuração.

**Fronteiras desta composição:** o microkernel vale apenas dentro do módulo de vigilância e dentro do componente de classificação de risco do nó da UPA. O núcleo expõe ao plugin apenas os dados do contrato, e nenhum plugin acessa o banco diretamente. Nenhum outro módulo usa o estilo.

**Alternativas consideradas:**
- Estrutura condicional no código do módulo: descartada porque a variação não é pequena nem fechada, e cada mudança de norma exigiria reabrir e reimplantar o núcleo clínico inteiro das 76 unidades. Era a alternativa competitiva, e a seção 8.6 a recomenda quando três casos nunca vão virar trinta.
- Regras em tabela de configuração no banco, sem contrato: descartada porque as regras de classificação de risco têm lógica, e não só parâmetros, e uma tabela acabaria virando linguagem de programação mal definida.
- Um serviço separado de regras: descartada porque acrescentaria unidade de implantação e custo operacional, e a seção 8.6 lembra que o microkernel não resolve escala, já que os plugins vivem na mesma unidade de implantação de qualquer forma.

**Consequências:**
- Positivas: incluir um agravo novo ou ajustar um protocolo não reabre o núcleo clínico, o que encurta o tempo entre a publicação da norma e a vigência no sistema; o núcleo fica pequeno e estável, com o teste concentrado onde o risco clínico é maior.
- Negativas: cada plugin exige teste de conformidade com o contrato executado antes de entrar em produção, o que acrescenta uma etapa ao pipeline; o versionamento do contrato vira dívida permanente, e toda mudança incompatível obriga a manter duas versões em paralelo; existe o risco conhecido do núcleo que cresce, quando alguém acrescenta um caso especial só desta vez, e o sintoma a vigiar é precisar mexer no núcleo para acrescentar um plugin.
