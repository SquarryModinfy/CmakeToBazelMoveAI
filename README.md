# CMake to Bazel AI Migrator

Этот инструмент автоматически мигрирует сборку CMake-компонента в Bazel и адаптирует конфигурацию CI под кастомную систему. Использует собственную LLM (через OpenAI API) и поддерживает документацию в формате .md, .txt, .docx.

## Возможности
 - Парсинг CMakeLists.txt с использованием AST
 - Генерация BUILD.bazel на основе промежуточного представления (IR)
 - Чтение документации кастомного CI и генерация config.yaml с помощью LLM
 - Поддержка RAG-подхода (Retrieval-Augmented Generation)

## Установка
```bash
pip install -r requirements.txt
```

## Конфигурация
API можно настроить одним из двух способов:

1. Через переменные окружения (рекомендуется):
```bash
export LLM_API_URL=https://your-llm-api.com/v1
export LLM_API_KEY=your-token
```

2. Через config.yaml (если переменные окружения не установлены):
```yaml
llm_api:
  url: "http://your-api-url"
  api_key: "your-api-key"
```

## Использование
```bash
python migrator.py ./path/to/component ./path/to/ci/docs
```

Параметры:
- component_path: Папка с CMakeLists.txt
- asgard_doc_path: Папка с документацией .md, .txt, .docx

В результате создаются:
- BUILD.bazel — Bazel сборка
- config.yaml — конфигурация для CI

## Требования
```txt
openai
pyyaml
cmake-ast
python-docx
```

## Пример
```bash
python migrator.py ./components/libfoo ./ci_docs/
```

## Результат:
- ./components/libfoo/BUILD.bazel
- ./components/libfoo/config.yaml

## TODO
 - Поддержка target_include_directories и target_compile_options
 - Поддержка внешних зависимостей через WORKSPACE
 - Dry-run через bazel build и валидация