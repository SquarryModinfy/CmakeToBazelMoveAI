import os
import yaml
from pathlib import Path
from typing import Dict
from openai import OpenAI
import cmakeast
from docx import Document

openai = OpenAI(base_url=os.getenv("LLM_API_URL"), api_key=os.getenv("LLM_API_KEY"))

def parse_cmake(file_path: Path) -> Dict:
    with file_path.open() as f:
        cmake_code = f.read()

    ast = cmakeast.parse(cmake_code)
    ir = {"targets": []}

    for stmt in ast:
        if stmt.command == "add_library" or stmt.command == "add_executable":
            target_type = "static_library" if stmt.command == "add_library" else "binary"
            name = stmt.args[0].value
            sources = [arg.value for arg in stmt.args[1:]]
            ir["targets"].append({
                "name": name,
                "type": target_type,
                "sources": sources,
                "include_dirs": [],  # Будут дополнены ниже
                "deps": []
            })
        elif stmt.command == "include_directories":
            dirs = [arg.value for arg in stmt.args]
            for target in ir["targets"]:
                target["include_dirs"].extend(dirs)
        elif stmt.command == "target_link_libraries":
            target_name = stmt.args[0].value
            deps = [arg.value for arg in stmt.args[1:]]
            for target in ir["targets"]:
                if target["name"] == target_name:
                    target["deps"].extend(deps)
    return ir

def generate_bazel_build(ir: Dict) -> str:
    build_file = ""
    for target in ir["targets"]:
        rule = "cc_library" if target['type'] == "static_library" else "cc_binary"
        build_file += f"{rule}(\n"
        build_file += f"    name = \"{target['name']}\",\n"
        build_file += f"    srcs = {target['sources']},\n"
        if target["include_dirs"]:
            build_file += f"    includes = {target['include_dirs']},\n"
        build_file += f"    deps = {target['deps']},\n"
        build_file += ")\n\n"
    return build_file

def load_rag_docs(doc_path: Path) -> str:
    documents = []
    for f in doc_path.rglob("*"):
        if f.suffix == ".md" or f.suffix == ".txt":
            documents.append(f.read_text())
        elif f.suffix == ".docx":
            doc = Document(f)
            documents.append("\n".join([p.text for p in doc.paragraphs]))
    return "\n\n".join(documents)

def query_ci_config(doc_path: Path, context_query: str) -> str:
    context = load_rag_docs(doc_path)
    prompt = f"""
    На основе следующей документации:
    {context}

    Ответь на вопрос: {context_query}
    """
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def generate_asgard_config(doc_path: Path, component_name: str) -> Dict:
    answer = query_ci_config(doc_path, f"Как должен выглядеть config.yaml для компонента {component_name}, если он собирается через Bazel?")
    try:
        return yaml.safe_load(answer)
    except Exception:
        return {"error": "Не удалось распарсить ответ как YAML", "raw": answer}

def migrate_component(component_path: Path, asgard_doc_path: Path):
    ir = parse_cmake(component_path / "CMakeLists.txt")
    build_txt = generate_bazel_build(ir)
    (component_path / "BUILD.bazel").write_text(build_txt)

    asgard_config = generate_asgard_config(asgard_doc_path, component_path.name)
    (component_path / "config.yaml").write_text(yaml.dump(asgard_config))

    print("Миграция завершена. Проверьте BUILD.bazel и config.yaml.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("component_path", type=str, help="Путь к папке компонента")
    parser.add_argument("asgard_doc_path", type=str, help="Путь к документации Asgard")
    args = parser.parse_args()

    migrate_component(Path(args.component_path), Path(args.asgard_doc_path))
    print("Миграция завершена.")