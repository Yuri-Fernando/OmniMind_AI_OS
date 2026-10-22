# PRD — Engineering Intake API

## Contexto
Times de engenharia submetem documentos técnicos (desenhos DXF, PDFs, imagens)
para processamento assíncrono. Precisamos de uma API pequena e segura que
receba o documento, registre um job e permita consultar o status.

## Objetivo
Entregar o primeiro incremento da API de intake: submissão e consulta de jobs.
O processamento em si (OCR/parsing) está fora deste incremento — o job nasce
em `QUEUED` e nenhum conteúdo é inventado.

## Funcionalidades
1. `POST /v1/documents` recebe JSON com `filename`, `content` (texto), `idempotency_key`
   e `metadata` opcional. Responde `202` com `job_id` e `status`. O conteúdo é
   gravado em um diretório de armazenamento isolado, um subdiretório por job.
2. `GET /v1/jobs/{job_id}` devolve o status (`QUEUED`, `RUNNING`, `COMPLETED` ou
   `FAILED`), o nome do arquivo e os eventos do job. Job inexistente: `404`.
3. Idempotência: repetir a mesma `idempotency_key` com o mesmo conteúdo (mesmo
   SHA-256) dentro da janela configurada devolve o `job_id` original. Mesma
   chave com conteúdo diferente: `409`.
4. Payload inválido (campo ausente, tipo errado, extensão não suportada) devolve
   `422` sem criar job nem gravar arquivo.
5. Nenhum acesso fora do diretório de armazenamento: nomes com `/`, `\`, `..`
   ou caminho absoluto são recusados com `422`. Sem chamadas externas.
6. Todo job guarda eventos (com `error_code` quando houver) em SQLite.

## Extensões aceitas
`.dxf`, `.pdf`, `.png`, `.tif`, `.tiff`, `.txt`.

## Métricas de sucesso
Testes de aceitação verdes; nenhuma escrita fora do diretório de armazenamento.
