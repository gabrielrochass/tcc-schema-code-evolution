"""Gera PDF da proposta de TCC no formato CIn/UFPE."""

from fpdf import FPDF

# ---------------------------------------------------------------------------
# Dados da proposta
# ---------------------------------------------------------------------------

ALUNO = "Gabriel Rocha de Souza Santos"
CURSO = "Ciencia da Computacao"
EMAIL = "grss@cin.ufpe.br"
TITULO = ("Co-evolucao entre Schema e Codigo de Aplicacao "
          "em Projetos Django Open-Source")
AREA = "Engenharia de Software"
ORIENTADOR = "Leopoldo Motta Teixeira"
AVALIADORES = "[A definir]"
DATA = "Recife, __ de __________ de 2026"

RESUMO = (
    "Sistemas de software evoluem continuamente, e mudancas no esquema de "
    "banco de dados frequentemente exigem adaptacoes coordenadas no codigo "
    "da aplicacao. Em projetos Django, essa evolucao e formalizada por meio "
    "de migrations \u2014 arquivos Python gerados automaticamente que descrevem "
    "alteracoes no esquema relacional. Apesar da importancia dessa coordenacao "
    "para a manutencao de software, poucos estudos investigaram empiricamente "
    "como mudancas de schema se propagam para as diferentes camadas do codigo "
    "em projetos reais. Trabalhos anteriores (Qiu et al., 2013; Meurice et al., "
    "2016) analisaram co-evolucao schema-codigo em outros contextos, mas nenhum "
    "focou especificamente no ecossistema Django, onde o ORM impoe uma estrutura "
    "canonica que torna a analise sistematica viavel."
    "\n\n"
    "Este trabalho propoe um estudo empirico quantitativo baseado em mineracao "
    "de repositorios de software (MSR), analisando 124 projetos Django "
    "open-source (86 aplicacoes e 38 bibliotecas) que somam 11.855 migrations. "
    "A metodologia consiste em: (i) extrair operacoes de migration via parsing "
    "AST, (ii) correlacionar cada migration ao commit que a introduziu via git "
    "log, e (iii) classificar os arquivos co-modificados por camada arquitetural "
    "Django (model, view, admin, serializer, form, template). Tres perguntas de "
    "pesquisa guiam a investigacao: o grau de acoplamento entre mudancas de "
    "schema e codigo (RQ1), quais camadas sao mais afetadas e sua relacao com "
    "o tipo de operacao (RQ2), e se os padroes diferem entre aplicacoes "
    "full-stack e bibliotecas reutilizaveis (RQ3)."
)

# ---------------------------------------------------------------------------
# Geracao do PDF
# ---------------------------------------------------------------------------

FONT_DIR = "C:/Windows/Fonts"


FONT_NAME = "TimesNR"


class PropostaPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.add_font(FONT_NAME, "", f"{FONT_DIR}/times.ttf")
        self.add_font(FONT_NAME, "B", f"{FONT_DIR}/timesbd.ttf")
        self.add_font(FONT_NAME, "I", f"{FONT_DIR}/timesi.ttf")
        self.set_auto_page_break(auto=True, margin=25)
        self.set_margins(30, 25, 30)


def build_pdf(output_path: str):
    pdf = PropostaPDF()
    pdf.add_page()

    # --- Cabecalho ---
    pdf.set_font(FONT_NAME, "B", 13)
    pdf.cell(0, 7, "Graduacao em Ciencia da Computacao", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(FONT_NAME, "B", 14)
    pdf.ln(4)
    pdf.cell(0, 7, "PROPOSTA DE TRABALHO DE CONCLUSAO DE CURSO", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(18)

    # --- Campos do formulario ---
    def campo(label: str, valor: str):
        pdf.set_font(FONT_NAME, "B", 12)
        pdf.write(6, f"{label}: ")
        pdf.set_font(FONT_NAME, "", 12)
        pdf.write(6, valor)
        pdf.ln(8)

    campo("Nome completo do(a) aluno(a)", ALUNO)
    campo("Curso", CURSO)
    campo("E-mail do(a) aluno(a)", EMAIL)
    campo("Titulo do trabalho", TITULO)
    campo("Area", AREA)
    campo("Nome do orientador", ORIENTADOR)
    campo("Possiveis avaliadores (dois)", AVALIADORES)

    pdf.ln(6)

    # --- Resumo ---
    pdf.set_font(FONT_NAME, "B", 12)
    pdf.write(6, "Resumo da proposta:")
    pdf.ln(8)

    pdf.set_font(FONT_NAME, "", 12)
    for paragraph in RESUMO.split("\n\n"):
        pdf.multi_cell(0, 6, paragraph.strip(), align="J")
        pdf.ln(3)

    # --- Data ---
    pdf.ln(12)
    pdf.set_font(FONT_NAME, "", 12)
    pdf.cell(0, 6, DATA, align="L", new_x="LMARGIN", new_y="NEXT")

    # --- Assinaturas ---
    pdf.ln(25)

    # Assinatura do orientador (centralizada)
    center_x = (pdf.w - 80) / 2
    pdf.set_x(center_x)
    pdf.cell(80, 0, "", border="T", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT_NAME, "B", 12)
    pdf.cell(0, 7, ORIENTADOR, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(FONT_NAME, "", 11)
    pdf.cell(0, 6, "Orientador", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_path)
    print(f"PDF gerado: {output_path}")


if __name__ == "__main__":
    build_pdf("docs/proposta-tcc.pdf")
