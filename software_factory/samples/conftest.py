# Os arquivos test_*.py dentro de samples/ são insumos da fábrica (golden tests,
# repo-semente e respostas roteirizadas), não testes deste repositório.
# Eles rodam só dentro dos worktrees isolados, pelo runner externo.
collect_ignore_glob = ["*"]
