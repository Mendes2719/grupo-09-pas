# Grupo 09

Repositório da atividade "Um problema, cinco realidades", da disciplina 12462, Padrões e Arquitetura de Software, PUC-Campinas, Sistemas de Informação, 2026-2. Professor Douglas Henrique Siqueira Abreu.

## Caso e envelope

**Caso:** Saúde, rede municipal de atenção à saúde. A secretaria municipal vai unificar os sistemas da rede, hoje com 70 UBS, 5 UPAs e um hospital de referência, cada unidade usando um sistema diferente e alguns ainda em papel.

**Envelope C:** a própria prefeitura, com equipe interna. Dez desenvolvedores e duas pessoas de infraestrutura, servidores próprios sem nuvem pública por exigência legal, orçamento anual fixo. O sistema legado de regulação de leitos não pode ser desligado e expõe uma API antiga e pouco documentada.

**Exigência que domina:** dados on-premise, com o legado ativo durante toda a transição.

## Integrantes

| Integrante | RA |
| --- | --- |
| Lucas Silva Brites | 24009893 |
| Mateo Shimizu Arbulu | 24013271 |
| Murilo de Santana Mendes | 24012855 |
| Pedro Henrique Lange Souza | 24008468 |
| Rafael Zilioti Zorzetto | 22008059 |

## Como navegar

| Pasta | Conteúdo | Situação |
| --- | --- | --- |
| [`1-matriz/`](1-matriz/) | Entrega 1, matriz dos doze estilos aplicada ao nosso caso e envelope, com os estilos descartados e o motivo | Entregue |
| [`2-arquitetura/`](2-arquitetura/) | Entrega 2, documento de arquitetura com os três níveis de C4, o mapa de restrições e decisões e os seis ADRs | Entregue |
| [`3-spike/`](3-spike/) | Entrega 3, o código pequeno que prova o ADR 0005, a decisão mais arriscada | Entregue |
| `4-leitura-cruzada/` | Entrega 4, objeções enviadas ao Grupo 04 e respostas às objeções recebidas do Grupo 01 | Pendente |
| `5-final/` | Entrega 5, versão revisada e o CHANGELOG do que mudou depois da leitura cruzada | Pendente |

Na leitura cruzada revisamos o Grupo 04, que tem o mesmo caso com o Envelope D, e somos revisados pelo Grupo 01, que tem o mesmo caso com o Envelope B.

## Referência

ABREU, Douglas Henrique Siqueira. *Estilos Arquiteturais de Software: guia de consulta.* 2026. Livro da disciplina, usado como referência ao longo de todas as entregas.

Os números de dimensionamento citados nos documentos são premissas do enunciado da atividade, escolhidas para fins didáticos. Não são dados oficiais de nenhum órgão.
