Só 7 módulos são críticos para o sistema rodar.
core/
agents/
rag/
tools/
memory/
planning/
notebooks/main.ipynb

Fluxo mínimo:
User
 │
 ▼
Planner Agent
 │
 ▼
Router
 │
 ├── RAG Agent
 ├── Tool Agent
 └── Executor
 │
 ▼
Reflection
 │
 ▼
Final Answer

📦 O que vai concentrar 80% da lógica
core/agent_runtime.py
core/orchestration_graph.py
agents/planner_agent.py
agents/rag_agent.py
agents/tool_agent.py
planning/task_decomposer.py
memory/memory_manager.py
tools/tool_registry.py
arena/agent_arena.py

AI Agent OS
│
├── Runtime
├── Agents
├── Knowledge
├── Tools
├── Memory
├── Planning
├── Cognition
├── Evaluation
├── Observability
└── Research Lab (arena)



Phase 1 - MVP Agent ✅
agents/ → main_agent.py, planner_agent.py, tool_agent.py, rag_agent.py, executor_agent.py, reflection_agent.py
rag/ → embeddings.py, retriever.py, chunking.py, load_docs.py
core/ → agent_runtime.py, orchestration_graph.py, state_manager.py, config.py
notebooks/ → main.ipynb, teste.ipynb (notebook execution)

Itens de documentação e setup:
requirements.txt, .env, readme.md, Arquitetura Cognitiva de Agentes.md, funcionamento.md → suporte ao MVP

Phase 2 - Intelligence ⚠
guardrails/ → prompt_injection_detector.py, content_filter.py → proteção de prompts
memory/ → short_term_memory.py, vector_memory.py, long_term_memory.py, memory_manager.py → memória semântica, histórico, perfil do usuário
self_improvement/ → prompt_optimizer.py, self_reflection.py, failure_analysis.py → reflexão e auto-healing
skills/ e planning/ → task_decomposer.py, autonomous_planner.py, goal_manager.py → decomposição de tarefas, seleção de skills

Phase 3 - Platform ⚠
collaboration/ → multi_agent_router.py, agent_registry.py, communication_protocol.py → multi-agent orchestration e roteamento
tools/ → tool_registry.py, tool_loader.py, auto_tool_discovery.py, weather_api.py, calculator.py → tool ecosystem
observability/ → langfuse_tracing.py, tracing.py, logging.py, telemetry.py → logs e monitoramento
infra/ → dockerfile, config.py, env_config.py → deploy e configuração

Phase 4 - Research Lab ⬜
evaluation/ → ragas_eval.py, deepeval_tests.py, benchmark_llm.py, agent_metrics.py, auto_eval_pipeline.py → avaliação automática
arena/ → agent_arena.py, tasks_dataset.py, arena_runner.py, leaderboard.py → simulação multi-agent e benchmarking
learnig/ → feedback_loop.py, reinforcement_learning.py, experience_buffer.py → aprendizado contínuo

Extras / Complementares
voice/ → stt_whisper.py, tts_elevenlabs.py, speech_to_text.py, text_to_speech.py → interface multimodal (voz)
knowledge/, knowledge_graph/ → document_ingestion.py, embeddings.py, retriever.py, vector_store.py, entity_extractor.py, graph_builder.py → RAG e KG
cognition/, reasoning/, simulation/ → world_model.py, belief_state.py, chain_of_thought.py, reasoning_engine.py → arquitetura cognitiva, raciocínio e simulação

                        