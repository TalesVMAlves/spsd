# SPSD — São Paulo's Settlement Dataset

Monta um dataset com uma linha por setor censitário (Censo 2022) da cidade de São Paulo,
para apoiar um modelo que identifica favelas em imagens de satélite. Cada setor recebe
identificação, latitude/longitude, rótulo de favela, features do Censo e o distrito.

O foco da atividade é **juntar dados de fontes diferentes**, cada uma com suas
peculiaridades (formato, sistema de coordenadas, sigilo, nomes de colunas), explicadas
ao longo do notebook `notebooks/comunidades_ibge.ipynb`.

## Como usar

Requer [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/comunidades_ibge.ipynb
```

Ou abra o notebook no VS Code/Jupyter com o kernel do `.venv`. Os arquivos são
baixados para `data/raw/` na primeira execução. Nas seguintes, o que já existe é pulado.
Para outro município, altere `UF`, `MUNICIPIO`, `PREFIXO_SAIDA` e `CRS_METRICO` (fuso UTM).

Para apontar imagens duplicadas (inclusive rotacionadas em 90°/180°/270°) em um diretório,
sem apagar nada: `uv run python scripts/check_duplicatas.py [diretorio]`
(sem argumento, usa `IMAGES_DIR`, definido no topo do script).

## Fontes

| fonte | formato | uso |
|---|---|---|
| [IBGE – Malha de setores censitários 2022](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/26565-malhasde-setores-censitarios-divisoes-intramunicipais.html) | GeoPackage | polígonos, identificação, população e domicílios |
| [IBGE – Favelas e Comunidades Urbanas 2022](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/tipologias-do-territorio/15788-favelas-e-comunidades-urbanas.html) | Shapefile em zip | polígonos das favelas (rótulo e máscaras) |
| [IBGE – Agregados por setores censitários](https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/) | CSV em zip | demografia, cor ou raça, alfabetização, renda, domicílios e entorno |
| [Prefeitura de São Paulo – GeoSampa](https://geosampa.prefeitura.sp.gov.br/) | GeoJSON via serviço [WFS](https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs?service=WFS&request=GetCapabilities) | 96 distritos municipais |

O significado dos códigos das variáveis (`V01006`, `v0001`...) vem dos dicionários do IBGE,
publicados nas mesmas pastas do FTP, e está anotado nos comentários do notebook.

## Saídas (`data/output/`)

| arquivo | conteúdo |
|---|---|
| `favelas_sao_paulo_2022.gpkg` | polígonos das favelas do município, para gerar máscaras na grade das imagens |
| `setores_sao_paulo_2022.gpkg` | uma linha por setor, com geometria (EPSG:4674) |
| `setores_sao_paulo_2022.csv` | a mesma tabela, sem geometria |
