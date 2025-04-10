# CMake to Bazel AI Migrator

Этот инструмент автоматически мигрирует сборку CMake-компонента в Bazel и адаптирует конфигурацию CI под кастомную систему. Использует собственную LLM (через OpenAI API) и поддерживает документацию в формате .md, .txt, .docx.

## Возможности
 - Парсинг CMakeLists.txt с использованием AST

 - Генерация BUILD.bazel на основе промежуточного представления (IR)

 - Чтение документации Asgard и генерация config.yaml с помощью LLM

 - Поддержка RAG-подхода (Retrieval-Augmented Generation)

## Установка
```bash
pip install -r requirements.txt
```

Создай .env или задай переменные окружения:

```bash
export LLM_API_URL=https://your-llm-api.com/v1
export LLM_API_KEY=your-token
```

## Использование
```bash
python migrator.py ./path/to/component ./path/to/asgard/docs
component_path: Папка с CMakeLists.txt

asgard_doc_path: Папка с документацией .md, .txt, .docx
```
В результате создаются:

BUILD.bazel — Bazel сборка

config.yaml — конфигурация для CI

## Требования
```txt
openai
pyyaml
cmake-ast
python-docx
```

## Пример
```bash
python migrator.py ./components/libfoo ./asgard_docs/
```
## Результат:

./components/libfoo/BUILD.bazel

./components/libfoo/config.yaml

## TODO
 Поддержка target_include_directories и target_compile_options

 Поддержка внешних зависимостей через WORKSPACE

 Dry-run через bazel build и валидация