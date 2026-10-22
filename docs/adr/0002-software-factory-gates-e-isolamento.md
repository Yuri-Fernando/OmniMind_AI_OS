# ADR 0002 — Gates determinísticos, isolamento e limites da Software Factory

- **Status:** aceito (2026-10-20)

## Decisões

1. **O orquestrador não é LLM.** Estados, transições, aprovações, budgets e gates G0–G7 são código
   Python com testes. Nenhuma "confiança" informada por modelo libera um gate.
2. **Aprovação vinculada a hash.** `approvals.json` guarda o SHA-256 do artefato aprovado (spec,
   tasks, PR). Editar o artefato depois expira a aprovação (`APPROVAL_EXPIRED:*`).
3. **Golden tests escritos antes do código.** Todo requisito MUST precisa apontar para um teste golden
   existente (checado por AST no G2). O caminho `golden_tests/` é protegido: o implementer não escreve
   nele; o runner copia os golden tests para o worktree só durante a verificação e os remove depois.
4. **Runner externo é o único juiz.** `claimed_tests_passed` do implementer é registrado e comparado
   (`false_test_claims`), nunca usado como evidência. O veredito vem do JUnit XML do pytest.
5. **Worktree por tarefa.** Branch `agent/{run_id}/{task_id}` a partir da branch de integração do run;
   integração por `merge --no-ff` sequencial na ordem topológica. A `main` nunca é tocada; não existe
   push, merge na `main` nem deploy no código.
6. **Escrita só em `owned_paths`.** Checado duas vezes: no conteúdo proposto (normalização, traversal,
   caminho protegido, segredo, sintaxe) e no `git status` real do worktree.
7. **Comandos vindos do LLM nunca são executados.** São classificados (`DESTRUCTIVE`,
   `NOT_ALLOWLISTED`, `ALLOWED`) e registrados; comando destrutivo encerra o run em `REJECTED`.
8. **Retrabalho limitado.** Falha em G4/G5/G6 volta para `IMPLEMENTING` com feedback até
   `1 + max_rework_attempts` tentativas; depois, estado terminal.
9. **SHA-base fixado.** Se a `main` do repositório-alvo andar depois do input manifest, o run falha
   com `STALE_BASE` antes de qualquer escrita.

## Limites conhecidos (honestos)

- **Rede no runner é bloqueada em melhor esforço** (proxy para `127.0.0.1:9`, ambiente sem variáveis
  com KEY/TOKEN/SECRET, autoload de plugins do pytest desligado). Não é sandbox de sistema operacional:
  um código malicioso com socket cru ainda alcançaria a rede. Para código não confiável de verdade,
  rodar o runner em container sem rede (`--network none`) e usuário não root — não implementado aqui.
- Paralelismo é validado (camadas sem colisão de `owned_paths`), mas a execução é sequencial.
- O `ClaudeProvider` foi testado só com cliente falso; execução real depende de chave válida e fica
  em suíte opt-in.
