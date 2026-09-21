#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entrega 3, codigo pequeno (spike) do Grupo 09.
Caso Saude, rede municipal. Envelope C, prefeitura com equipe interna.

Prova o ADR 0005: reservar leito por concorrencia otimista local confirmada no legado.
Esta simulado so o minimo para o mecanismo aparecer: o Banco da Rede com uma versao por
leito, o legado com vocabulario proprio e sem operacao idempotente, o terminal antigo que
reserva por fora do nosso sistema, e a rede como tempo limite injetado em chamadas dadas.
Nao ha threads: as disputas sao interleaves escritos a mao, para a saida ser deterministica.
Ponto de partida: a secao 4 dos capitulos de estilo do livro, adaptada ao caso.
"""

import sys

# O dominio fala por nome, o legado so aceita onze digitos: traduzir e o trabalho da ACL.
CARTOES = {"ANA": "70000000001", "BRUNO": "70000000002",
           "CARLA": "70000000003", "DIEGO": "70000000004"}
NOMES = {numero: nome for nome, numero in CARTOES.items()}

class TempoLimite(Exception):
    """A chamada ao legado nao respondeu e nao se sabe se ela foi aplicada."""

class ConflitoDeVersao(Exception):
    """Outra unidade gravou intencao neste leito primeiro."""

class DisjuntorAberto(Exception):
    """O legado falhou seguidas vezes e a fachada passou a recusar rapido."""

class Relogio:
    """Relogio logico. Evita hora de parede para a saida ser deterministica."""
    def __init__(self):
        self.t = 0
    def marcar(self):
        self.t += 1
        return f"t{self.t:03d}"

def log(relogio, ator, texto):
    print(f"[{relogio.marcar()}] {ator:<9} {texto}")

class RegulacaoLegada:
    """Sistema do fornecedor, que nao pode ser desligado nem alterado.

    Situacao 'L' ou 'O', paciente em onze digitos e um campo livre OBS de doze
    caracteres, unico lugar onde cabe a nossa chave. Nao e idempotente.
    """

    def __init__(self, relogio, leitos):
        self.relogio = relogio
        self.leitos = {cod: {"SIT": "L", "PAC": "", "OBS": ""} for cod in leitos}
        self.falhas = {}
        self.chamadas = 0
        self.fora_do_ar = False

    def programar_falha(self, numero_da_chamada, momento):
        self.falhas[numero_da_chamada] = momento  # momento: "antes" ou "depois" da escrita

    def consultar(self, cod):
        if self.fora_do_ar:
            log(self.relogio, "LEGADO", f"consultar {cod} nao respondeu")
            raise TempoLimite()
        reg = self.leitos[cod]
        log(self.relogio, "LEGADO", f"consultar {cod} devolve SIT={reg['SIT']} PAC={reg['PAC']} OBS={reg['OBS']}")
        return dict(reg)

    def reservar(self, cod, cartao, obs):
        self.chamadas += 1
        if self.fora_do_ar:
            log(self.relogio, "LEGADO", f"reservar {cod} nao respondeu")
            raise TempoLimite()
        momento = self.falhas.get(self.chamadas)
        if momento == "antes":
            log(self.relogio, "LEGADO", f"reservar {cod} nao respondeu, nada foi aplicado")
            raise TempoLimite()
        reg = self.leitos[cod]
        if reg["SIT"] == "O":
            log(self.relogio, "LEGADO", f"reservar {cod} recusado, ja ocupado por {reg['PAC']}")
            return "ERRO-OCUPADO"
        reg["SIT"], reg["PAC"], reg["OBS"] = "O", cartao, obs
        if momento == "depois":
            log(self.relogio, "LEGADO", f"reservar {cod} foi aplicado, mas a resposta se perdeu")
            raise TempoLimite()
        log(self.relogio, "LEGADO", f"reservar {cod} aceito para {cartao}")
        return "OK"

    def reservar_pelo_terminal(self, cod, nome):
        """O caminho que existe fora do nosso sistema e que nao podemos fechar."""
        reg = self.leitos[cod]
        if reg["SIT"] == "O":
            return "ERRO-OCUPADO"
        reg["SIT"], reg["PAC"], reg["OBS"] = "O", CARTOES[nome], "TERMINAL"
        log(self.relogio, "TERMINAL", f"reservou {cod} para {nome} por fora do nosso sistema")
        return "OK"

class FachadaIntegracao:
    """Camada anticorrupcao e ponto unico de conversa com o legado.

    Traduz o nosso vocabulario, trata tempo limite por leitura de volta em vez de
    repeticao cega, e abre o disjuntor depois de falhas seguidas (secao 18.4).
    """

    LIMITE_FALHAS = 3

    def __init__(self, legado, relogio):
        self.legado = legado
        self.relogio = relogio
        self.falhas_seguidas = 0

    def confirmar(self, intencao):
        # Devolve (status, ocupante); status e confirmada, perdida ou indefinida.
        if self.falhas_seguidas >= self.LIMITE_FALHAS:
            log(self.relogio, "FACHADA", "disjuntor aberto, recusando sem chamar o legado")
            raise DisjuntorAberto()
        status, ocupante = self._tentar(intencao)
        self.falhas_seguidas = self.falhas_seguidas + 1 if status == "indefinida" else 0
        return status, ocupante

    def _tentar(self, intencao):
        cod = intencao["leito"]
        cartao = CARTOES[intencao["paciente"]]
        obs = intencao["correlacao"][:12]
        try:
            resposta = self.legado.reservar(cod, cartao, obs)
        except TempoLimite:
            log(self.relogio, "FACHADA", "tempo limite, reconciliando por leitura de volta")
            return self._reconciliar(cod, cartao, obs)
        return self._traduzir_resposta(resposta, cod)

    def _reconciliar(self, cod, cartao, obs):
        try:
            reg = self.legado.consultar(cod)
        except TempoLimite:
            log(self.relogio, "FACHADA", "a leitura de volta tambem falhou, estado indefinido")
            return "indefinida", ""
        if reg["SIT"] == "O" and reg["OBS"] == obs and reg["PAC"] == cartao:
            log(self.relogio, "FACHADA", "a chamada tinha sido aplicada, nao repete")
            return "confirmada", ""
        if reg["SIT"] == "O":
            return "perdida", NOMES.get(reg["PAC"], "desconhecido")
        log(self.relogio, "FACHADA", "nada foi aplicado, repetindo com a mesma chave")
        try:
            resposta = self.legado.reservar(cod, cartao, obs)
        except TempoLimite:
            log(self.relogio, "FACHADA", "tempo limite de novo, estado indefinido")
            return "indefinida", ""
        return self._traduzir_resposta(resposta, cod)

    def _traduzir_resposta(self, resposta, cod):
        if resposta == "OK":
            return "confirmada", ""
        return "perdida", NOMES.get(self.legado.leitos[cod]["PAC"], "desconhecido")

class BancoDaRede:
    """Esquema do modulo de regulacao, com uma versao por leito."""

    def __init__(self, relogio, leitos):
        self.relogio = relogio
        self.leitos = {cod: {"versao": 0, "estado": "livre", "paciente": ""} for cod in leitos}

    def versao(self, cod):
        return self.leitos[cod]["versao"]

    def gravar_intencao(self, cod, paciente, versao_lida):
        reg = self.leitos[cod]
        if reg["versao"] != versao_lida:
            log(self.relogio, "BANCO", f"conflito em {cod}: esperava versao {versao_lida}, atual {reg['versao']}")
            raise ConflitoDeVersao()
        reg["versao"] += 1
        reg["estado"] = "intencao"
        reg["paciente"] = paciente
        log(self.relogio, "BANCO", f"intencao em {cod} para {paciente}, versao {reg['versao']}")
        return reg["versao"]

    def confirmar(self, cod):
        reg = self.leitos[cod]
        reg["versao"] += 1
        reg["estado"] = "reservado"
        log(self.relogio, "BANCO", f"{cod} reservado para {reg['paciente']}")

    def compensar(self, cod, motivo, ocupante_externo=""):
        reg = self.leitos[cod]
        anterior = reg["paciente"]
        reg["versao"] += 1
        reg["estado"] = "ocupado_externo" if ocupante_externo else "livre"
        reg["paciente"] = ocupante_externo
        log(self.relogio, "BANCO", f"intencao de {anterior} em {cod} desfeita: {motivo}")

    def marcar_indefinido(self, cod):
        self.leitos[cod]["versao"] += 1
        self.leitos[cod]["estado"] = "indefinido"
        log(self.relogio, "BANCO", f"{cod} fica indefinido e vai para conferencia humana")

class ModuloRegulacao:
    """Dominio. Nunca confirma ao usuario antes da resposta do legado."""

    def __init__(self, banco, fachada, relogio):
        self.banco = banco
        self.fachada = fachada
        self.relogio = relogio

    def solicitar(self, cod, paciente, unidade, versao_lida):
        log(self.relogio, unidade, f"pede {cod} para {paciente} tendo lido a versao {versao_lida}")
        try:
            versao = self.banco.gravar_intencao(cod, paciente, versao_lida)
        except ConflitoDeVersao:
            log(self.relogio, unidade, "recebeu recusa por conflito, sem segunda intencao")
            return "recusada_por_conflito"
        intencao = {"leito": cod, "paciente": paciente,
                    "correlacao": f"{unidade}{cod[-3:]}{versao:03d}"}
        try:
            status, ocupante = self.fachada.confirmar(intencao)
        except DisjuntorAberto:
            self.banco.compensar(cod, "regulacao indisponivel")
            log(self.relogio, unidade, "recebeu recusa explicita: use a contingencia")
            return "recusada_por_indisponibilidade"
        if status == "confirmada":
            self.banco.confirmar(cod)
            log(self.relogio, unidade, f"recebeu {cod} confirmado para {paciente}")
        elif status == "perdida":
            self.banco.compensar(cod, f"o legado ja deu o leito a {ocupante}", ocupante)
            log(self.relogio, unidade, "recebeu recusa: o leito foi ocupado pela regulacao legada")
        else:
            self.banco.marcar_indefinido(cod)
            log(self.relogio, unidade, "recebeu aviso de que a confirmacao esta pendente")
        return status

def verificar_invariante(banco, legado):
    """Nenhum leito pode terminar com dois pacientes diferentes."""
    problemas = []
    for cod, nosso in banco.leitos.items():
        deles = legado.leitos[cod]
        ocupantes = set()
        if nosso["estado"] == "reservado":
            ocupantes.add(nosso["paciente"])
        if deles["SIT"] == "O":
            ocupantes.add(NOMES.get(deles["PAC"], "terminal"))
        if len(ocupantes) > 1:
            problemas.append(f"{cod} ficou com {sorted(ocupantes)}")
        if nosso["estado"] == "reservado" and deles["SIT"] != "O":
            problemas.append(f"{cod} reservado do nosso lado e livre no legado")
    if problemas:
        print("  INVARIANTE VIOLADO: " + "; ".join(problemas))
        return False
    print("  invariante verificado: nenhum leito com dois pacientes")
    return True

def montar(leitos):
    relogio = Relogio()
    legado = RegulacaoLegada(relogio, leitos)
    banco = BancoDaRede(relogio, leitos)
    return legado, banco, ModuloRegulacao(banco, FachadaIntegracao(legado, relogio), relogio)

def cenario_1():
    print("\nCENARIO 1: duas unidades pedem o mesmo leito ao mesmo tempo")
    legado, banco, regulacao = montar(["HRC-201"])
    v_upa, v_ubs = banco.versao("HRC-201"), banco.versao("HRC-201")
    regulacao.solicitar("HRC-201", "ANA", "UPA-LESTE", v_upa)
    regulacao.solicitar("HRC-201", "BRUNO", "UBS-NORTE", v_ubs)
    return verificar_invariante(banco, legado)

def cenario_2():
    print("\nCENARIO 2: o terminal antigo reserva antes da nossa confirmacao")
    legado, banco, regulacao = montar(["HRC-202"])
    versao = banco.versao("HRC-202")
    legado.reservar_pelo_terminal("HRC-202", "CARLA")
    regulacao.solicitar("HRC-202", "ANA", "UPA-LESTE", versao)
    return verificar_invariante(banco, legado)

def cenario_tempo_limite(numero, momento, cod, paciente, unidade):
    print(f"\nCENARIO {numero}: tempo limite {momento} de o legado aplicar a reserva")
    legado, banco, regulacao = montar([cod])
    legado.programar_falha(1, momento)
    regulacao.solicitar(cod, paciente, unidade, banco.versao(cod))
    return verificar_invariante(banco, legado)

def cenario_5():
    print("\nCENARIO 5: legado fora do ar, o disjuntor abre e a unidade recebe recusa")
    leitos = ["HRC-205", "HRC-206", "HRC-207", "HRC-208"]
    legado, banco, regulacao = montar(leitos)
    legado.fora_do_ar = True
    for cod, paciente in zip(leitos, ["ANA", "BRUNO", "CARLA", "DIEGO"]):
        regulacao.solicitar(cod, paciente, "UPA-LESTE", banco.versao(cod))
    return verificar_invariante(banco, legado)

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Spike do ADR 0005: reserva de leito com o legado ainda no circuito")
    print("Grupo 09, caso Saude, envelope C")
    resultados = [cenario_1(), cenario_2(), cenario_tempo_limite(3, "depois", "HRC-203", "ANA", "UPA-LESTE"),
                  cenario_tempo_limite(4, "antes", "HRC-204", "DIEGO", "UPA-SUL"), cenario_5()]
    print(f"\nRESUMO: {sum(resultados)} de {len(resultados)} cenarios com o invariante mantido")
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
