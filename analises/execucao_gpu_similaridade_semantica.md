# Execução na GPU — 16/09/2026

Os três experimentos disponíveis foram reexecutados na **NVIDIA GeForce GTX 1060
3 GB**, usando CUDA de fato. Um produto matricial em `cuda:0` foi conferido contra
CPU antes dos modelos; os manifestos registram GPU, revisão, precisão e pico de
memória. O notebook executado é `Investigacao_Similaridade_GPU.ipynb`.

## Ambiente

- Ambiente isolado `.venv-gpu`, Python 3.12.14, PyTorch 2.7.1+cu118, CUDA 11.8.
- Driver observado: NVIDIA 582.66; capacidade da GPU: 6.1 (Pascal).
- Transformers 5.17.0, SentenceTransformers 6.0.1, NumPy 2.5.3 e scikit-learn 1.9.1.
- O ambiente `.venv` original, os artefatos CPU e os notebooks anteriores foram preservados.
- Lote de inferência 1; `--low-vram` alterna E5/NLI entre RAM e GPU.
- E5 e NLI em float32, mantendo pesos, prefixos, perguntas, segmentação e limiares.

CUDA 11.8 foi escolhido para preservar suporte à arquitetura Pascal, seguindo as
[versões oficiais do PyTorch](https://pytorch.org/get-started/previous-versions/)
e a [nota oficial sobre suporte às arquiteturas](https://dev-discuss.pytorch.org/t/cuda-toolkit-version-and-architecture-support-update-maxwell-and-pascal-architecture-support-removed-in-cuda-12-8-and-12-9-builds/3128).
O pacote foi obtido do índice oficial e seu SHA-256 conferido:
`80855ec840b7b06372ff43535d01393a8ec101842618d1f9ed629572b52aed71`.

O download inicial por pip não progrediu; a transferência retomável com curl
terminou e a instalação local passou em `pip check`. Uma checagem auxiliar de
processos foi temporariamente rejeitada pela revisão automática por limite de
uso; isso não impediu a instalação e execução posteriores autorizadas.

## Resultados e comparação

| Experimento | CPU anterior | GPU | Comparação das decisões |
|---|---:|---:|---|
| Diagnóstico E5, B0/B2/margem e calibrações | 6,33 s | 3,36 s | 696/696 idênticas |
| Documento 6x1, 70 perguntas e duas segmentações | 238,39 s | 41,07 s | 70/70 idênticas em cada segmentação |
| Templates e recuperação controlada | 16,23 s | 14,58 s | 8/8 expectativas NLI satisfeitas e decisões idênticas |

Os hashes das entradas e revisões dos modelos coincidem nas três comparações.
A maior diferença de escore do diagnóstico foi `8,50e-7`. No documento, as
probabilidades NLI diferiram no máximo `2,05e-5` na segmentação inicial e
`5,08e-5` na alternativa; isso não mudou estados nem conjuntos de evidências.

Os tempos incluem carregamento dos modelos, exceto o diagnóstico, cujo cronômetro
inicia depois de carregar o encoder. Mudaram também Python/PyTorch e o tamanho
dos lotes: esta comparação não isola um efeito causal exclusivo do hardware.
O tempo documental observado caiu aproximadamente 5,8 vezes.

O piloto documental manteve 49 itens incertos, 14 contrários, 6 favoráveis e
1 conflito. Mudanças de espaços, duplicação e ordem da agregação permaneceram
invariantes em 70/70; duas segmentações ainda divergem em 16/70. A GPU não resolve
essa fragilidade metodológica. Não se estima acurácia documental sem gabarito.

No experimento documental, o pico de alocação PyTorch foi 1.213.801.472 bytes
(1,21 GB) e o pico reservado 1.256.194.048 bytes (1,26 GB). Esses números são
do processo PyTorch, não da memória total da placa incluindo Windows/outros apps.

## Validação e artefatos

- **15 testes aprovados** no ambiente GPU, sem falhas/erros/skips. Incluem
  alternância RAM/GPU por fixture, além dos testes metodológicos anteriores.
- CUDA real validado separadamente pelo teste matricial e pelos três experimentos.
- `pip check`: nenhuma dependência quebrada.
- Notebook GPU: seis células de leitura/análise executadas e saídas persistidas.
- Rastreabilidade: R1–R8 em `investigacao/METODOLOGIA.md`; a gestão de VRAM é
  uma adaptação de engenharia ligada à reprodução (R4), não um método novo.

Resultados em `analises/execucoes/`:

- `diagnostico_e5_gpu_20260916/`
- `documento_6x1_gpu_20260916/`
- `controlados_gpu_20260916/`
- `comparacao_cpu_gpu_20260916.json`
- `gpu_ambiente_20260916.json`
- `gpu_requirements_20260916.txt`
- `validacao_testes_gpu_20260916.json`

## Reprodução

```powershell
.venv-gpu/Scripts/python.exe -m investigacao diagnostic --device cuda --batch-size 1 --low-vram --output analises/execucoes/diagnostico_gpu_novo
.venv-gpu/Scripts/python.exe -m investigacao documents --device cuda --batch-size 1 --low-vram --text 'content/Escala 6x1.txt' --output analises/execucoes/documento_gpu_novo --top-k 3
.venv-gpu/Scripts/python.exe -m investigacao.controlados --device cuda --batch-size 1 --low-vram --output analises/execucoes/controlados_gpu_novo
.venv-gpu/Scripts/python.exe -m unittest discover -s tests -v
```

Para reconstruir o ambiente em Python 3.12, instalar
`investigacao/requirements-gpu.txt`. Para reler as execuções nomeadas desta sessão:

```powershell
.venv-gpu/Scripts/python.exe -m investigacao.comparar_hardware
.venv-gpu/Scripts/python.exe -m investigacao.relatorio --gpu
```

O treinamento externo continua dependendo dos textos/autoria do corpus, e a
comparação Sabiá das saídas verificadas já descritas no relatório anterior. A GPU
não supre esses dados; `--low-vram` suporta inferência e não promete viabilizar
treinamento completo na placa de 3 GB.
