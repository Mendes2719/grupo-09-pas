# Entrega 3: código pequeno (spike)

**Grupo 09.** Caso Saúde, rede municipal de atenção à saúde. Envelope C, prefeitura com equipe interna.

## Qual ADR ele prova

[ADR 0005: reservar leito por concorrência otimista local confirmada no legado](../2-arquitetura/adr-0005-reservar-leito-com-confirmacao-no-legado.md), que é a decisão mais arriscada do projeto. Ela responde à segunda pergunta obrigatória do caso: como duas unidades disputando o mesmo leito nunca conseguem reservá-lo ao mesmo tempo, com o sistema legado ainda no circuito.

## O que ele prova

Que o invariante "nenhum leito com dois pacientes" se mantém em cinco situações, mesmo existindo um escritor concorrente que não está sob o nosso controle, que é o terminal antigo do legado.

1. Duas unidades pedem o mesmo leito ao mesmo tempo. A concorrência otimista por versão deixa só uma intenção existir, e a segunda unidade recebe recusa por conflito em vez de uma segunda reserva.
2. O terminal antigo reserva o leito antes da nossa confirmação. A intenção local é desfeita por compensação e o leito é marcado como ocupado por fora.
3. A chamada ao legado dá tempo limite **depois** de ele ter aplicado a reserva. A fachada reconcilia lendo de volta, reconhece a própria chave de correlação e não reserva de novo.
4. A chamada dá tempo limite **antes** de ele aplicar. A leitura de volta mostra o leito livre e a chamada é repetida com a mesma chave, resultando em uma reserva só.
5. O legado fica fora do ar. Depois de três falhas seguidas o disjuntor abre e a unidade recebe recusa explícita, em vez de ficar pendurada esperando.

O programa termina com código de saída 0 se o invariante valeu nos cinco cenários, e 1 se algum foi violado.

## Como rodar

Nenhuma dependência além da biblioteca padrão do Python 3.12. Na pasta `3-spike`:

```bash
python3 exemplo.py
```

A saída é determinística, porque o relógio é lógico e as disputas são interleaves escritos à mão em vez de threads. O resultado esperado está em [saida-esperada.txt](saida-esperada.txt) e pode ser conferido com `python3 exemplo.py | diff - saida-esperada.txt`.

## O que está simulado

Só o mínimo para o mecanismo aparecer: o Banco da Rede como dicionário em memória com uma versão por leito, o sistema legado com vocabulário próprio (situação `L` ou `O`, paciente em onze dígitos e um campo livre `OBS` de doze caracteres) e sem operação idempotente, o terminal antigo que grava por fora, e a rede como exceção de tempo limite injetada em chamadas escolhidas.

## O que aconteceria se a decisão estivesse errada

O jeito mais simples de implementar a reserva seria tratar o nosso banco como autoridade da ocupação e sincronizar com o legado depois. Nesse desenho o cenário 2 falha: o terminal antigo dá o leito à Carla, nós confirmamos o mesmo leito para a Ana, e os dois lados ficam consistentes cada um consigo mesmo. Nada quebra, nenhum erro aparece no log, e a divergência só vira visível quando duas ambulâncias chegam ao mesmo leito.

A segunda forma de errar é repetir a chamada ao legado depois de um tempo limite, com recuo exponencial, sem ler de volta. No cenário 3 isso produz uma segunda reserva sobre um leito que já era nosso, ou uma recusa que nos faz liberar uma reserva que na verdade existia. A seção 18.4 do livro é explícita ao dizer que retentativa só é segura quando a operação chamada é idempotente, e a API do legado não oferece isso.

A terceira é confirmar ao usuário logo depois da intenção local, deixando a confirmação no legado em segundo plano. Ganha-se tempo de resposta e perde-se o invariante, porque a tela passa a anunciar como garantido um leito que o legado ainda pode recusar.

Em qualquer uma das três, o custo não é um dado errado que se corrige com um script de reconciliação: é um paciente encaminhado para um leito ocupado.
