# 🤖 Agente AIOS — Sistema de Orquestração de Agentes IA

Sistema completo de orquestração de agentes IA com memória centralizada, integração com Claude API, e arquitetura modular escalável.

---

## 🎯 O Que É AIOS?

**AIOS** = **AI Orchestration System** — Uma plataforma que orquestra múltiplos agentes especializados para resolver tarefas complexas de forma colaborativa.

```
Seu Prompt
    ↓
Router (direciona para agentes corretos)
    ↓
├─ @dev (implementação de código)
├─ @qa (testes e qualidade)
├─ @architect (design de sistema)
├─ @pm (product management)
├─ @po (product owner)
├─ @sm (scrum master)
├─ @analyst (pesquisa)
├─ @data-engineer (banco de dados)
├─ @ux-design-expert (UX/UI)
└─ @devops (CI/CD, git push)
    ↓
Resultado
```

---

## ✨ Capacidades Principais

### 🧠 **10 Agentes Especializados**

| Agente | Persona | Especialidade |
|--------|---------|---------------|
| **@dev** | Dex | Implementação de código, desenvolvimento |
| **@qa** | Quinn | Testes, qualidade, QA gate |
| **@architect** | Aria | Arquitetura de sistema, design técnico |
| **@pm** | Morgan | Product management, estratégia |
| **@po** | Pax | Product owner, stories, epics |
| **@sm** | River | Scrum master, planejamento |
| **@analyst** | Alex | Pesquisa, análise, investigação |
| **@data-engineer** | Dara | Banco de dados, schema design |
| **@ux-design-expert** | Uma | UX/UI design, experiência do usuário |
| **@devops** | Gage | CI/CD, git operations (EXCLUSIVO) |

### 🛠️ **1534+ Skills Integradas**

Ferramentas especializadas ativadas com `/skill-name`:

```
/deep-research            → Pesquisa profunda
/code-reviewer            → Revisão de código
/security-audit           → Auditoria de segurança
/database-designer        → Design de schema
/api-design               → Design de APIs
/tdd-guide                → Test-Driven Development
/skill-forge              → Criar nova skill
... e mais 1527 skills!
```

### 👥 **12 Squads Coordenados**

Equipes de especialistas para tarefas complexas:

```
advisory-board, brand-squad, c-level-squad, copy-squad, 
cybersecurity, data-squad, design-squad, hormozi-squad, 
movement, storytelling, traffic-masters, ... e mais
```

### 💾 **Memória Centralizada**

Sistema único de memória compartilhado por todos os projetos:

```python
from memoria_init import memoria

# SALVAR (SQLite local, instantâneo)
memoria.save('decisoes', 'dec-001', {
    'titulo': 'Escolher Next.js',
    'racional': 'Melhor DX',
})

# CARREGAR
dec = memoria.load('decisoes', 'dec-001')

# LISTAR
todas = memoria.list('decisoes')

# STATS
stats = memoria.stats()  # Total, Synced, Pendentes
```

**Características:**
- ✅ **SQLite Local** — offline-first, instantâneo
- ⚡ **MongoDB Sync** — automático em background
- 🔒 **Persistência** — dados compartilhados entre projetos
- 📊 **35 Repositórios** — como referência

---

## 🏗️ Arquitetura

```
AIOS Framework
├── agents/              (10 agentes especializados)
├── core/                (engine central de orquestração)
├── memory/              (sistema de memória inteligente)
├── knowledge/           (base de conhecimento)
├── reasoning/           (engine de raciocínio)
├── skills/              (1534+ skills)
├── planning/            (planejamento automático)
├── evaluation/          (avaliação de performance)
└── ... (25+ módulos especializados)
```

---

## 🚀 Como Usar

### 1️⃣ Novo Projeto? (2 Passos)

```bash
# PASSO 1: Copiar CLAUDE.md
cp CLAUDE.md seu-novo-projeto/

# PASSO 2: Rodar init-projeto.py
python init-projeto.py seu-novo-projeto/
```

**Resultado:** Projeto pronto com memória centralizada ativa! ✅

### 2️⃣ Em Seu Código

```python
from memoria_init import memoria
from datetime import datetime

# SALVAR DECISÃO
memoria.save('decisoes', 'dec-meu-projeto', {
    'titulo': 'Decisão técnica',
    'escolha': 'Next.js',
    'racional': 'Melhor DX',
    'timestamp': datetime.utcnow().isoformat(),
})

# USAR AGENTE
# @dev implemente a feature XYZ
# Claude Code carrega @dev do AIOS e executa!

# USAR SKILL
# /security-audit no código
# Claude Code ativa skill e faz auditoria!
```

### 3️⃣ Fluxo de Desenvolvimento (Story-Driven)

```
@sm *create-story 
    ↓
@po *validate 
    ↓
@dev *develop 
    ↓
@qa *qa-gate 
    ↓
@devops *push
```

---

## 📊 Fluxo de Dados

```
Seu Projeto
    ↓
from memoria_init import memoria
    ↓
memoria.save('decisoes', 'dec-001', {...})
    ↓
SQLite Local (AGORA ✅)
    ↓
Worker Thread (background)
    ↓
MongoDB (a cada 5 min ⚡)
    ↓
Outro Projeto
    ↓
memoria.load('decisoes', 'dec-001')  ← ✅ ENCONTRA!
```

**Resultado:** Memória compartilhada entre TODOS os projetos! 🎯

---

## 🎓 Documentação

| Arquivo | Descrição |
|---------|-----------|
| **DOIS-PASSOS.md** | Como inicializar novo projeto (2 passos!) |
| **O-QUE-CLAUDE-MD-FAZ.md** | Poder do CLAUDE.md explicado |
| **COMO_USAR.md** | Guia de referência rápida |
| **RESUMO-COMPLETO.md** | Documentação detalhada e completa |
| **MEMORIA-GUIA.md** | Exemplos de uso da memória |

---

## ⚙️ Tecnologias

- **Claude API** — Integração com Claude para IA
- **Python 3.10+** — Linguagem principal
- **SQLite** — Banco de dados local (memória)
- **MongoDB** — Cloud sync automático
- **LangChain/LangGraph** — Orquestração de agentes
- **FastAPI** — API REST
- **Pydantic** — Validação de dados

---

## 📦 Requisitos

```bash
Python 3.10+
pip install -r requirements.txt

Dependências principais:
- anthropic          (Claude API)
- langgraph          (Orquestração)
- pymongo            (MongoDB)
- pydantic           (Validação)
- langfuse           (Observabilidade)
```

---

## 🔧 Instalação

```bash
# Clone o repositório
git clone https://github.com/Yuri-Fernando/OmniMind_AI_OS.git
cd OmniMind_AI_OS

# Instale dependências
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Adicione suas chaves (ANTHROPIC_API_KEY, MONGO_URI, etc)

# Rode um agente
python main.py
```

---

## 💡 Exemplos

### Exemplo 1: Guardar Decisão Técnica

```python
from memoria_init import memoria

memoria.save('decisoes', 'dec-auth-2026', {
    'titulo': 'Estratégia de Autenticação',
    'opcoes': ['JWT', 'OAuth2', 'Session'],
    'escolhido': 'JWT + Refresh Token',
    'racional': ['Stateless', 'Escalável', 'Compatível mobile'],
})
```

### Exemplo 2: Usar Agente Especializado

```
Você escreve no prompt:
"@architect revise minha decisão de banco de dados"

Claude Code:
1. Carrega persona de @architect (Aria) do AIOS
2. Consulta memória (decisoes passadas)
3. Dá feedback especializado
```

### Exemplo 3: Ativar Skill

```
Você escreve no prompt:
"/security-audit no código de pagamento"

Claude Code:
1. Carrega skill /security-audit
2. Analisa código
3. Gera relatório de segurança
```

---

## 🔐 Segurança

- ✅ `.env` com credenciais (gitignored)
- ✅ SQLite local (seu computador)
- ✅ MongoDB com autenticação
- ✅ Sem keys hardcoded
- ✅ Supabase pronto para backup

---

## 📈 Roadmap

- [ ] Implementação de Supabase sync
- [ ] WebUI para visualizar memória
- [ ] Dashboard de agentes
- [ ] Exportar relatórios
- [ ] Integração com git (commits → eventos)
- [ ] IA baseada em histórico de decisões
- [ ] Mobile app

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Crie uma issue descrevendo a mudança
2. Faça um fork do repositório
3. Crie uma branch: `git checkout -b feature/sua-feature`
4. Commit: `git commit -m 'feat: descrição'`
5. Push: `git push origin feature/sua-feature`
6. Abra um Pull Request

---

## 📝 Licença

MIT License — veja LICENSE para detalhes

---

## 🎉 Status

```
✅ Sistema operacional completo
✅ 10 agentes especializados
✅ 1534+ skills integradas
✅ 12 squads coordenados
✅ Memória centralizada (SQLite + MongoDB)
✅ Documentação completa
✅ Pronto para produção
```

---

## 🔗 Links Importantes

- **GitHub:** https://github.com/Yuri-Fernando/OmniMind_AI_OS
- **Documentação:** Veja pasta `/docs`
- **Exemplos:** Veja pasta `/examples`
- **Notebooks:** Veja pasta `/notebooks`

---

## 💬 Suporte

Para dúvidas ou sugestões:
- Abra uma issue no GitHub
- Consulte a documentação em `/docs`
- Veja os exemplos em `/examples`

---

**Criado com ❤️ usando Claude API e AIOS Framework**

---

**Status:** ✅ Production Ready  
**Última atualização:** 2026-04-02  
**Versão:** 1.0.0
