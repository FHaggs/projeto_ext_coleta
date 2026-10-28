# Cronograma e pontuação

Projeto Extensionista · INCT SiMAI — Dashboard de Enchentes em Porto Alegre.
100 pontos em 5 etapas. Fontes: `Enunciado.pdf` e quadro de cronograma da disciplina.

## Distribuição dos pontos

| Fase 1 | Fase 2 | Fase 3 | Versão final | Apresentação |
|:---:|:---:|:---:|:---:|:---:|
| 10 | 20 | 20 | 20 | 30 |

50 dos 100 pontos vêm das Fases 1 a 3; deixar tudo para a última semana não basta para passar.

## Etapas

| Data | Etapa | O que entregar | Pts |
|---|---|---|:---:|
| **28/10 (qua)** | Fase 1 · em aula, com o grupo | `relatorios/base_dados.pdf`: bases sobre enchentes no RS (origem, conteúdo, recorte espacial e temporal, formato, forma de coleta, licença, ligação com os dados do INCT), escolha justificada das bases da Tela 2 e a pergunta que ela responde. Repositório criado com README e membros | 10 |
| **09/11 (seg)** | Fase 2 · em aula, com o grupo | Scripts de coleta das bases externas; JSON do INCT em formato longo e limpo; `relatorios/limpeza_dados.pdf`; notebook de EDA com 6 a 10 gráficos comentados (Tela 1 e Tela 2); wireframe das duas telas | 20 |
| **16/11 (seg)** | Fase 3 · em aula, com o grupo | Protótipo do dashboard publicado com as duas telas funcionando; `relatorios/dashboard.pdf` (objetivo de cada tela, visualizações e por quê, como usar, limitações) | 20 |
| **24/11 (ter), até 23h59** | Versão final · entrega no repositório | Dashboard final publicado; `relatorios/dashboard.pdf` atualizado com o que mudou desde a Fase 3. Contam os commits feitos até o prazo | 20 |
| **25/11 (qua) ou 30/11 (seg)** | Apresentação · banca com o INCT SiMAI (data sorteada) | Pitch de 10 min com demonstração ao vivo, seguido de perguntas da banca | 30 |

> Divergência entre as fontes: o enunciado descreve a Fase 3 como "dashboard em desenvolvimento, ainda que sem acabamento"; o quadro diz "publicado com as duas telas funcionando". Planejar pelo mais exigente (as duas telas já no ar em 16/11) e confirmar com a professora.

## Regras de avaliação

- **Acompanhamento em aula:** as Fases 1, 2 e 3 são avaliadas em conversa com cada grupo. Aluno ausente perde pontos na nota individual daquela fase, mesmo que o grupo tenha entregado.
- **Fórum do Moodle:** a cada fase, registrar o que cada integrante fez, até o início da aula de acompanhamento. Quem não tem contribuição registrada tem desconto individual.
- **Fase não entregue vale zero** e deve ser entregue junto com a próxima; sem ela, a próxima não é corrigida.
- **Atraso nas fases:** quem não tiver nada para mostrar na aula pode entregar em até 48 h, perdendo 30% da nota da fase; depois disso, zero.
- **Segunda chance:** as Fases 1 e 2 podem ser reentregues uma vez até 24/11, valendo no máximo 80% dos pontos.
- **Versão final:** commits feitos em até 48 h após 24/11 23h59 valem com desconto de 30%; depois disso não são considerados. Vale para qualquer commit posterior ao prazo, inclusive depois da apresentação.
- **Nota individual** = nota da equipe × fator de participação (0,5 a 1,0), definido por presença nos acompanhamentos, registros no Moodle, histórico de commits e avaliação entre pares.

## Plano de trabalho

### Fase 1 — até 28/10
- [ ] Fechar a equipe e criar o repositório (professora como colaboradora, README com membros)
- [ ] Explorar a ferramenta atual do INCT e anotar o que funciona e o que atrapalha
- [ ] Levantar bases sobre enchentes no RS e escolher a da Tela 2 (uma obtida por código)
- [ ] Definir a pergunta da Tela 2 e como ela se liga à Tela 1
- [ ] Escrever `relatorios/base_dados.pdf`
- [ ] Registro de contribuições no fórum do Moodle

### Fase 2 — 29/10 a 09/11
- [ ] Scripts de coleta das bases externas (respeitando `robots.txt`; dados brutos guardados em `dados/originais/`)
- [ ] Carregar `data.json` em formato longo (shape esperado: 6674 × 7)
- [ ] Caçar inconsistências (monotonicidade dos prédios afetados, `percentage` e `affected_population`, bairros e níveis faltando ou fora de ordem) e documentar cada uma: onde, por que é problema, decisão e justificativa
- [ ] Exportar JSON limpo em `dados/processados/`
- [ ] Notebook de EDA com 6 a 10 gráficos comentados
- [ ] Wireframes das duas telas
- [ ] Escrever `relatorios/limpeza_dados.pdf`
- [ ] Registro no Moodle

### Fase 3 — 10/11 a 16/11
- [ ] Tela 1: slider 3,0–10,0 m (passo 0,1), indicadores, gráfico por bairro, curva com marca de 5,35 m, ranking e aviso de limitações
- [ ] Tela 2: 3+ visualizações, 1+ filtro, 1+ visualização ligada à Tela 1, fonte com link e data de coleta
- [ ] Publicar (Streamlit Community Cloud ou Hugging Face Spaces)
- [ ] Escrever `relatorios/dashboard.pdf`
- [ ] Registro no Moodle

### Versão final — 17/11 a 24/11
- [ ] Corrigir o que a professora apontou na Fase 3
- [ ] Mapa de bairros (opcional, diferencial) com malha do ObservaPOA
- [ ] Aviso de que os números são estimativas de simulação; linguagem e cores sem sensacionalismo
- [ ] README: equipe, link do dashboard, como rodar; `requirements.txt` reprodutível
- [ ] Registro de uso de IA e citação de todas as fontes
- [ ] Atualizar `relatorios/dashboard.pdf`
- [ ] Último commit antes de 24/11 23h59

### Apresentação — 25/11 ou 30/11
- [ ] Roteiro de 10 min e demonstração ao vivo ensaiada
- [ ] Preparar respostas para perguntas da banca
- [ ] Avaliação entre pares
