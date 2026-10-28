#!/usr/bin/env python3
"""Baixa, para relatorios/anexos/, os dados das fontes levantadas na Fase 1.

Usa apenas a biblioteca padrão do Python (urllib, csv, zipfile, re), para rodar
em qualquer máquina sem instalar pacotes. Arquivos já existentes são pulados,
então o script pode ser reexecutado sem repetir downloads (coleta responsável).

Uso:
    python3 scripts/baixar_anexos_fase1.py            # baixa tudo
    python3 scripts/baixar_anexos_fase1.py ana atlas  # só os blocos indicados

Blocos: inct, ana, dmae, zenodo, atlas, datapoa, observapoa, ibge, osm, readme

Arquivos acima de ~50 MB (geopackage da UFRGS, CSV/XLSX completos do Atlas) só são
baixados com a opção --grandes e ficam fora do git (relatorios/anexos/.gitignore).
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ANEXOS = RAIZ / "relatorios" / "anexos"
UA = "projeto-enchentes-poa/0.1 (disciplina Coleta de Dados; estudantes; contato no README)"
HOJE = date.today().isoformat()
LOG: list[dict] = []  # registro de cada arquivo baixado, para o README
BAIXAR_GRANDES = "--grandes" in sys.argv
# arquivos grandes: nunca entram no git; só são baixados com --grandes
GRANDES = [
    "04_ufrgs_zenodo_cheias_rhguaiba_2024/cheias_rhguaiba_2024_db_v12.gpkg",
    "05_atlas_digital_desastres_sedec_mdr/atlas_desastres_BD_1991_2025_v1-1_consolidado.csv",
    "05_atlas_digital_desastres_sedec_mdr/atlas_desastres_BD_1991_2025_v1-1_consolidado.xlsx",
]


def _data_arquivo(p: Path) -> str:
    """Data de modificação do arquivo (= data em que foi baixado), ISO."""
    return date.fromtimestamp(p.stat().st_mtime).isoformat()


def _abrir(url: str, timeout: int = 180, dados: bytes | None = None) -> urllib.response.addinfourl:
    req = urllib.request.Request(url, data=dados, headers={"User-Agent": UA, "Accept": "*/*"})
    return urllib.request.urlopen(req, timeout=timeout)


def baixar(url: str, destino: Path, descricao: str, fonte: str, timeout: int = 600,
           dados: bytes | None = None, tentativas: int = 3) -> Path | None:
    """Baixa `url` em `destino`. Pula se já existir. Registra no LOG."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if str(destino.relative_to(ANEXOS)) in GRANDES and not BAIXAR_GRANDES and not destino.exists():
        print(f"  [pulado, use --grandes] {destino.relative_to(RAIZ)}")
        LOG.append({"arquivo": str(destino.relative_to(ANEXOS)), "descricao": descricao + " — NÃO BAIXADO por padrão (use --grandes); fora do git",
                    "fonte": fonte, "url": url, "coletado_em": "—"})
        return None
    if destino.exists() and destino.stat().st_size > 0:
        print(f"  [ok, já existe] {destino.relative_to(RAIZ)}")
        LOG.append({"arquivo": str(destino.relative_to(ANEXOS)), "descricao": descricao,
                    "fonte": fonte, "url": url, "coletado_em": _data_arquivo(destino)})
        return destino
    for i in range(1, tentativas + 1):
        try:
            print(f"  baixando {url}\n      -> {destino.relative_to(RAIZ)}")
            t0 = time.time()
            with _abrir(url, timeout=timeout, dados=dados) as r, open(destino, "wb") as f:
                while True:
                    bloco = r.read(1 << 20)
                    if not bloco:
                        break
                    f.write(bloco)
            tam = destino.stat().st_size
            print(f"      {tam/1e6:.1f} MB em {time.time()-t0:.0f}s")
            LOG.append({"arquivo": str(destino.relative_to(ANEXOS)), "descricao": descricao,
                        "fonte": fonte, "url": url, "coletado_em": HOJE})
            return destino
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            print(f"      erro ({i}/{tentativas}): {e}")
            if destino.exists():
                destino.unlink()
            time.sleep(5 * i)
    print(f"  FALHOU: {url}")
    LOG.append({"arquivo": str(destino.relative_to(ANEXOS)), "descricao": descricao,
                "fonte": fonte, "url": url, "coletado_em": "FALHOU"})
    return None


def gdrive(id_arquivo: str) -> str:
    return f"https://drive.google.com/uc?export=download&id={id_arquivo}&confirm=t"


# ---------------------------------------------------------------- 01 INCT
def bloco_inct():
    pasta = ANEXOS / "01_inct_simai_ferramenta_atual"
    baixar("http://vhlab.com.br/INCT/floods/", pasta / "flood_inct_index.html",
           "Página inicial da ferramenta Flood (snapshot)", "INCT SiMAI / VHLab PUCRS", timeout=120)
    baixar("http://vhlab.com.br/INCT/floods/main-NLG32SEF.js", pasta / "flood_inct_main.js",
           "Bundle JS principal (contém as rotas da API e a estação ANA 87450004)",
           "INCT SiMAI / VHLab PUCRS", timeout=120)


# ----------------------------------------------------------------- 02 ANA
ESTACOES = {
    "87450004": ("cais_maua_c6", 2014),
    "87450020": ("usina_do_gasometro", 2024),
}


def _parse_xml_ana(texto: str) -> list[dict]:
    regs = []
    for bloco in re.findall(r"<DadosHidrometereologicos[^>]*>(.*?)</DadosHidrometereologicos>", texto, flags=re.S):
        reg = {}
        for campo in ("CodEstacao", "DataHora", "Vazao", "Nivel", "Chuva"):
            m = re.search(rf"<{campo}>(.*?)</{campo}>", bloco)
            reg[campo] = m.group(1).strip() if m else ""
        regs.append(reg)
    return regs


def bloco_ana():
    pasta = ANEXOS / "02_ana_telemetria_nivel_guaiba"
    pasta.mkdir(parents=True, exist_ok=True)
    base = "https://telemetriaws1.ana.gov.br/ServiceANA.asmx/"
    baixar(base + "ListaEstacoesTelemetricas?statusEstacoes=&origem=",
           pasta / "ana_lista_estacoes_telemetricas.xml",
           "Lista completa de estações telemétricas da ANA (metadados, inclui 87450004 e 87450020)",
           "ANA", timeout=300)
    ano_atual = date.today().year
    for cod, (nome, ano_ini) in ESTACOES.items():
        saida = pasta / f"ana_{cod}_{nome}_nivel_15min_{ano_ini}-{ano_atual}.csv"
        if saida.exists():
            print(f"  [ok, já existe] {saida.relative_to(RAIZ)}")
            LOG.append({"arquivo": str(saida.relative_to(ANEXOS)),
                        "descricao": f"Série de 15 min da estação {cod} ({nome}); Nivel em cm; consolidado dos XML anuais",
                        "fonte": "ANA / telemetriaws1", "url": base + "DadosHidrometeorologicos",
                        "coletado_em": _data_arquivo(saida)})
            continue
        todos: list[dict] = []
        for ano in range(ano_ini, ano_atual + 1):
            url = (base + "DadosHidrometeorologicos?codEstacao=" + cod
                   + f"&dataInicio=01/01/{ano}&dataFim=31/12/{ano}")
            for tent in range(3):
                try:
                    print(f"  ANA {cod} {ano} ...", end=" ", flush=True)
                    with _abrir(url, timeout=600) as r:
                        texto = r.read().decode("utf-8", "ignore")
                    regs = _parse_xml_ana(texto)
                    print(f"{len(regs)} registros")
                    todos.extend(regs)
                    break
                except Exception as e:  # noqa: BLE001
                    print(f"erro: {e}")
                    time.sleep(10)
        todos.sort(key=lambda r: r["DataHora"])
        with open(saida, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["CodEstacao", "DataHora", "Nivel", "Vazao", "Chuva"])
            w.writeheader()
            w.writerows(todos)
        print(f"      {len(todos)} registros -> {saida.name}")
        LOG.append({"arquivo": str(saida.relative_to(ANEXOS)),
                    "descricao": f"Série de 15 min da estação {cod} ({nome}); Nivel em cm; consolidado dos XML anuais",
                    "fonte": "ANA / telemetriaws1", "url": base + "DadosHidrometeorologicos", "coletado_em": HOJE})


# ---------------------------------------------------------------- 03 DMAE
def bloco_dmae():
    pasta = ANEXOS / "03_dmae_rhama_estudo_hidrologico_2026"
    pdf = baixar("https://prefeitura.poa.br/sites/default/files/usu_doc/sites/dmae/"
                 "P05%20-%20Estudo%20Hidrologico_SPCC_Parte%20I_R01.pdf",
                 pasta / "dmae_rhama_2026_P05_estudo_hidrologico_parte1.pdf",
                 "Estudo Hidrológico P05 Parte I (Rhama Analysis para o DMAE, 24/06/2026)", "DMAE / Prefeitura POA")
    if not pdf:
        return
    import subprocess
    try:
        txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"  pdftotext indisponível ({e}); tabelas não extraídas")
        return
    (pasta / "dmae_rhama_2026_P05_texto_extraido.txt").write_text(txt, encoding="utf-8")

    def extrair_tabela(titulo: str, nome: str, descricao: str):
        # a última ocorrência é a tabela em si; a primeira costuma ser a entrada no sumário
        i = txt.rfind(titulo)
        if i < 0:
            print(f"  tabela não encontrada: {titulo}")
            return
        bloco = txt[i:i + 7000]
        linhas = []
        for ln in bloco.splitlines():
            for m in re.finditer(r"(\d{4})\s+(\d,\d\d|S/d)\s*(?:\(([a-h])\))?", ln):
                linhas.append((int(m.group(1)), m.group(2).replace(",", "."), m.group(3) or ""))
        linhas = sorted(set(linhas))
        saida = pasta / nome
        with open(saida, "w", encoding="utf-8", newline="") as f:
            f.write("ano;cota_max_m;fonte_letra\n")
            for a, c, l in linhas:
                f.write(f"{a};{c};{l}\n")
        print(f"  {nome}: {len(linhas)} anos")
        LOG.append({"arquivo": str(saida.relative_to(ANEXOS)), "descricao": descricao,
                    "fonte": "DMAE/Rhama 2026 (extraído por código)", "url": "(derivado do PDF)", "coletado_em": HOJE})

    extrair_tabela("Tabela 2. Cotas máximas anuais do Guaíba (m) em diversos locais no Cais Mauá -\n",
                   "dmae_rhama_2026_tabela2_maximas_anuais_guaiba_1899_2024_nao_homogenea.csv",
                   "Tabela 2: cotas máximas anuais 1899–2024, série não homogênea (letra = régua de origem)")
    # Tabela 4 (série homogênea, Doca 4, datum Imbituba): no corpo do texto o título vem
    # com "- série" no fim da linha; no sumário vem em outra quebra, por isso usa-se a última ocorrência
    ocorrencias = list(re.finditer(r"Tabela 4\. Cotas \(m\) máximas anuais do Guaíba no Cais Mauá \(Doca 4\) - série\s*\n\s*homogênea", txt))
    if ocorrencias:
        m = ocorrencias[-1]
        extrair_tabela(txt[m.start():m.end()],
                       "dmae_rhama_2026_tabela4_maximas_anuais_guaiba_serie_homogenea_doca4.csv",
                       "Tabela 4: cotas máximas anuais homogeneizadas para a Doca 4 (datum Imbituba)")


# -------------------------------------------------------------- 04 ZENODO
def bloco_zenodo():
    pasta = ANEXOS / "04_ufrgs_zenodo_cheias_rhguaiba_2024"
    v12 = "https://zenodo.org/api/records/13227745/files/{}/content"
    v05 = "https://zenodo.org/api/records/11185049/files/{}/content"
    baixar("https://zenodo.org/api/records/13227745", pasta / "zenodo_13227745_metadados_v1-2.json",
           "Metadados do registro Zenodo v1.2 (autores, licença CC-BY 4.0, lista de arquivos)", "UFRGS / Zenodo")
    itens = [
        (v12, "cheias_rhguaiba_2024_db_v12_glossario.csv", "Glossário das camadas do geopackage v1.2"),
        (v12, "rs_crise_abrigos_24052024_20h.csv", "Abrigos (SOS RS) em 24/05/2024 20h, com capacidade e abrigados"),
        (v12, "insumos_inep_escolas_2023_rs.gpkg", "Insumo: escolas INEP 2023 do RS (pontos)"),
        (v12, "insumos_snisb_barragens_2022_rhguaiba.gpkg", "Insumo: barragens SNISB 2022 na RH Guaíba"),
        (v12, "insumos_nasa_deslizamentos_2024_rhguaiba.gpkg", "Insumo: deslizamentos 2024 (NASA) na RH Guaíba"),
        (v12, "insumos_sulgas_tubulacoes_rhguaiba.gpkg", "Insumo: tubulações Sulgás"),
        (v05, "analise_ada_rhguaiba_municipios_10052024.csv",
         "Área diretamente afetada por município em 10/05/2024 (139 municípios; só no registro v0.5)"),
        (v05, "cheias_rhguaiba_2024_db_v5_glossario.csv", "Glossário da versão v0.5 (compara camadas)"),
        (v12, "cheias_rhguaiba_2024_db_v12.gpkg",
         "Geopackage principal v1.2: manchas observadas e simuladas, bairros POA, pontos de nível etc. (196 MB)"),
    ]
    for base, nome, desc in itens:
        baixar(base.format(nome), pasta / nome, desc, "UFRGS (Possantti et al.) / Zenodo, CC-BY 4.0", timeout=1800)
    (pasta / "NAO_BAIXADOS.txt").write_text(
        "Insumos acima de 100 MB não foram baixados (ver zenodo_13227745_metadados_v1-2.json):\n"
        "insumos_openstreetmaps_vias_rhguaiba.gpkg (107 MB), insumos_ibge_rs.gpkg (110 MB),\n"
        "insumos_semars_basecarto25k_rs.gpkg (365 MB), insumos_ana_anadem_30m_rhguaiba.zip (1,3 GB),\n"
        "insumos_ibge_cnefe_microdados_2022_rs.gpkg (1,5 GB), insumos_googlebuildings_edificacoes_rhguaiba.gpkg (1,5 GB).\n"
        "URL: https://zenodo.org/api/records/13227745/files/<nome>/content\n", encoding="utf-8")


# --------------------------------------------------------------- 05 ATLAS
def bloco_atlas():
    pasta = ANEXOS / "05_atlas_digital_desastres_sedec_mdr"
    base = "https://atlasdigital.mdr.gov.br/arquivos/"
    csv_path = baixar(base + "2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv",
                      pasta / "atlas_desastres_BD_1991_2025_v1-1_consolidado.csv",
                      "Base completa 1991–2025 v1.1 (valores corrigidos), CSV ';' Windows-1252, 1 linha por registro municipal",
                      "Sedec/MIDR – Atlas Digital de Desastres", timeout=1800)
    baixar(base + "2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.xlsx",
           pasta / "atlas_desastres_BD_1991_2025_v1-1_consolidado.xlsx",
           "Base completa em XLSX (valores originais, corrigidos e fator de correção)", "Sedec/MIDR", timeout=1800)
    baixar(base + "Atlas_Digital_Desastres_Manual_Aplicacao.pdf", pasta / "atlas_desastres_manual_tratamento_base.pdf",
           "Manual de tratamento da base de dados", "Sedec/MIDR")
    baixar(base + "2026/2026.08-logs-correcoes.xlsx", pasta / "atlas_desastres_log_correcoes_2026-08.xlsx",
           "Log de correções da base", "Sedec/MIDR")
    saida = pasta / "atlas_desastres_extrato_RS_2024.csv"
    if not csv_path and saida.exists():
        LOG.append({"arquivo": str(saida.relative_to(ANEXOS)), "descricao": "Extrato: registros do RS com Data_Evento em 2024 (derivado do CSV completo), UTF-8",
                    "fonte": "derivado do CSV do Atlas", "url": "(derivado)", "coletado_em": _data_arquivo(saida)})
    if csv_path:
        n = 0
        with open(csv_path, encoding="cp1252", newline="") as f, open(saida, "w", encoding="utf-8", newline="") as g:
            rd = csv.reader(f, delimiter=";")
            wr = csv.writer(g, delimiter=";")
            cab = next(rd)
            wr.writerow(cab)
            i_uf, i_dt = cab.index("Sigla_UF"), cab.index("Data_Evento")
            for row in rd:
                if len(row) > i_dt and row[i_uf] == "RS" and row[i_dt].endswith("/2024"):
                    wr.writerow(row)
                    n += 1
        print(f"  extrato RS 2024: {n} registros")
        LOG.append({"arquivo": str(saida.relative_to(ANEXOS)), "descricao": f"Extrato: registros do RS com Data_Evento em 2024 ({n} linhas), UTF-8",
                    "fonte": "derivado do CSV do Atlas", "url": "(derivado)", "coletado_em": HOJE})


# ------------------------------------------------------------- 06 DATAPOA
def bloco_datapoa():
    pasta = ANEXOS / "06_datapoa_prefeitura_poa"
    api = "https://dadosabertos.poa.br/api/3/action/package_show?id="
    for ds in ("bairros-lc-12-112-16", "sie"):
        meta = baixar(api + ds, pasta / f"datapoa_{ds}_metadados_ckan.json",
                      f"Metadados CKAN do conjunto {ds}", "DataPOA (CKAN), CC-BY")
        if not meta:
            continue
        res = json.loads(meta.read_text(encoding="utf-8"))["result"]["resources"]
        for r in res:
            nome_orig = r["url"].rsplit("/", 1)[-1]
            if nome_orig.endswith(".pdf") and r["name"] == "Bairros":
                continue  # mapa em PDF de 45 MB, não é dado tabular
            prefixo = "datapoa_bairros_lc12112-16_" if ds.startswith("bairros") else "datapoa_sie_"
            baixar(r["url"], pasta / (prefixo + nome_orig), f"{r['name']} ({r['format']})",
                   "DataPOA (CKAN), CC-BY", timeout=600)


# ----------------------------------------------------------- 07 OBSERVAPOA
def bloco_observapoa():
    pasta = ANEXOS / "07_observapoa_prefeitura_poa"
    b = "https://prefeitura.poa.br/sites/default/files/usu_doc/hotsites/smpae/observapoa/"
    baixar(b + "Pop_Bairro_Censo_2022.csv", pasta / "observapoa_populacao_por_bairro_censo2022.csv",
           "População por bairro, Censo 2022 (universo), limites de 2016; Latin-1 com ';'", "ObservaPOA")
    baixar(b + "Pop_Bairro_Censo_2022.xlsx", pasta / "observapoa_populacao_por_bairro_censo2022.xlsx",
           "População por bairro, Censo 2022 (XLSX)", "ObservaPOA")
    baixar(gdrive("1uv0Gi4oU51K9akQCg5NX087EsXTv-V5D"), pasta / "observapoa_bairros_oficiais_shp.zip",
           "Bairros oficiais (LC 12.112/16), shapefile", "ObservaPOA (Google Drive)")
    baixar(gdrive("17gLbmV3DNjdu6Df9uMwogtnJxmbRhOqI"), pasta / "observapoa_bairros_oficiais.kml",
           "Bairros oficiais, KML", "ObservaPOA (Google Drive)")
    baixar(gdrive("1MR1sPnliwAbCpqkRk3wB0YZqnoH7KbCx"), pasta / "observapoa_setores_censitarios_2022_shp.zip",
           "Setores censitários 2022 (versão final), shapefile", "ObservaPOA (Google Drive)", timeout=900)
    # Se o Drive devolver HTML (página de confirmação), avisa
    for p in pasta.glob("observapoa_*"):
        if p.suffix in (".zip", ".kml") and p.stat().st_size < 200_000:
            cab = p.read_bytes()[:300].lower()
            if b"<html" in cab:
                print(f"  AVISO: {p.name} veio como HTML do Google Drive; baixar manualmente")
                p.rename(p.with_suffix(p.suffix + ".FALHOU.html"))


# ---------------------------------------------------------------- 08 IBGE
def bloco_ibge():
    pasta = ANEXOS / "08_ibge_censo2022_agregados_por_bairro"
    base = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
    with _abrir(base + "Agregados_por_Bairro_csv/", timeout=120) as r:
        html = r.read().decode("utf-8", "ignore")
    zips = sorted(set(re.findall(r'href="(Agregados_por_bairros_[^"]+\.zip)"', html)))
    for z in zips:
        baixar(base + "Agregados_por_Bairro_csv/" + z, pasta / ("ibge_censo2022_" + z),
               f"Agregados por bairro: {z.replace('Agregados_por_bairros_', '').replace('.zip', '')} (Brasil)", "IBGE", timeout=900)
    with _abrir(base, timeout=120) as r:
        html = r.read().decode("utf-8", "ignore")
    dic = re.findall(r'href="(dicionario_de_dados_agregados_por_setores_censitarios_[^"]+\.xlsx)"', html)
    if dic:
        baixar(base + dic[0], pasta / ("ibge_censo2022_" + dic[0]), "Dicionário de dados dos agregados", "IBGE")
    baixar(base + "malha_com_atributos/bairros/gpkg/UF/RS/RS_bairros_CD2022.gpkg",
           pasta / "ibge_censo2022_malha_bairros_RS_com_atributos.gpkg",
           "Malha de bairros do RS com atributos do Censo 2022 (GeoPackage)", "IBGE", timeout=900)
    # extrato de Porto Alegre do arquivo básico
    basico = next(pasta.glob("ibge_censo2022_Agregados_por_bairros_basico_*.zip"), None)
    if basico:
        with zipfile.ZipFile(basico) as zf:
            nome = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
            texto = zf.read(nome).decode("latin-1")
        saida = pasta / "ibge_censo2022_bairros_porto_alegre_basico_extrato.csv"
        rd = csv.reader(io.StringIO(texto), delimiter=";")
        cab = next(rd)
        i_mun = cab.index("CD_MUN")
        linhas = [row for row in rd if len(row) > i_mun and row[i_mun] == "4314902"]
        with open(saida, "w", encoding="utf-8", newline="") as g:
            wr = csv.writer(g, delimiter=";")
            wr.writerow(cab)
            wr.writerows(linhas)
        print(f"  extrato Porto Alegre (básico): {len(linhas)} bairros")
        LOG.append({"arquivo": str(saida.relative_to(ANEXOS)), "descricao": f"Extrato: {len(linhas)} bairros de Porto Alegre (CD_MUN 4314902) do arquivo básico, UTF-8",
                    "fonte": "derivado do IBGE", "url": "(derivado)", "coletado_em": HOJE})


# ----------------------------------------------------------------- 09 OSM
def bloco_osm():
    pasta = ANEXOS / "09_openstreetmap_overpass"
    consulta = """
[out:json][timeout:180];
area["name"="Porto Alegre"]["admin_level"="8"]["boundary"="administrative"]->.a;
(
  nwr["amenity"~"^(school|kindergarten|college|university|hospital|clinic|doctors|social_facility|shelter|fire_station|police|community_centre)$"](area.a);
  nwr["emergency"="assembly_point"](area.a);
);
out tags center;
""".strip()
    dados = urllib.parse.urlencode({"data": consulta}).encode()
    saida = pasta / "osm_porto_alegre_equipamentos_escolas_saude_abrigos.json"
    baixar("https://overpass-api.de/api/interpreter", saida,
           "Escolas, unidades de saúde, equipamentos sociais e de emergência em Porto Alegre (tags + centroide)",
           "OpenStreetMap contributors (ODbL) via Overpass API", timeout=300, dados=dados)
    (pasta / "osm_consulta_overpass.txt").write_text(consulta + "\n", encoding="utf-8")
    if saida.exists():
        try:
            n = len(json.loads(saida.read_text(encoding="utf-8"))["elements"])
            print(f"  OSM: {n} elementos")
        except Exception as e:  # noqa: BLE001
            print(f"  OSM: resposta inválida ({e})")


# ------------------------------------------------------------- README
def bloco_readme():
    linhas = ["# Anexos da Fase 1 — dados brutos das fontes levantadas", "",
              f"Gerado por `scripts/baixar_anexos_fase1.py` em {datetime.now():%d/%m/%Y %H:%M}. "
              "Arquivos marcados como derivados foram produzidos a partir dos brutos pelo mesmo script.", "",
              "| Arquivo | Conteúdo | Fonte | URL | Coletado em | Tamanho |", "|---|---|---|---|---|---|"]
    vistos = set()
    for item in LOG:
        if item["arquivo"] in vistos:
            continue
        vistos.add(item["arquivo"])
        p = ANEXOS / item["arquivo"]
        tam = f"{p.stat().st_size/1e6:.1f} MB" if p.exists() else "—"
        linhas.append(f"| `{item['arquivo']}` | {item['descricao']} | {item['fonte']} | {item['url']} | {item['coletado_em']} | {tam} |")
    linhas += ["", "## Arquivos grandes (fora do git)", "",
               "Estes arquivos passam do limite do GitHub ou do tamanho recomendado, estão em "
               "`relatorios/anexos/.gitignore` e só são baixados com `python3 scripts/baixar_anexos_fase1.py --grandes`:", ""]
    linhas += [f"- `{g}`" for g in GRANDES]
    (ANEXOS / ".gitignore").write_text("# gerado por scripts/baixar_anexos_fase1.py\n" + "\n".join(GRANDES) + "\n", encoding="utf-8")
    (ANEXOS / "README.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"  README com {len(vistos)} arquivos")


BLOCOS = {"inct": bloco_inct, "ana": bloco_ana, "dmae": bloco_dmae, "zenodo": bloco_zenodo,
          "atlas": bloco_atlas, "datapoa": bloco_datapoa, "observapoa": bloco_observapoa,
          "ibge": bloco_ibge, "osm": bloco_osm}

if __name__ == "__main__":
    pedidos = [a for a in sys.argv[1:] if a not in ("readme", "--grandes")] or list(BLOCOS)
    ANEXOS.mkdir(parents=True, exist_ok=True)
    for nome in pedidos:
        print(f"\n=== {nome} ===")
        try:
            BLOCOS[nome]()
        except Exception as e:  # noqa: BLE001
            print(f"  ERRO no bloco {nome}: {e!r}")
    if pedidos == list(BLOCOS) or "readme" in sys.argv[1:]:
        print("\n=== readme ===")
        bloco_readme()
