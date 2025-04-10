import os
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple
from openai import OpenAI
import cmakeast
from docx import Document

def load_config() -> Dict:
    config = {
        "llm_api": {
            "url": os.getenv("LLM_API_URL"),
            "api_key": os.getenv("LLM_API_KEY")
        }
    }
    
    # Try loading from config.yaml as fallback
    try:
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                yaml_config = yaml.safe_load(f)
                # Only use yaml values if environment variables are not set
                if not config["llm_api"]["url"]:
                    config["llm_api"]["url"] = yaml_config["llm_api"]["url"]
                if not config["llm_api"]["api_key"]:
                    config["llm_api"]["api_key"] = yaml_config["llm_api"]["api_key"]
    except Exception as e:
        print(f"Warning: Could not load config.yaml: {e}")
    
    # Validate config
    if not config["llm_api"]["url"] or not config["llm_api"]["api_key"]:
        raise ValueError("LLM API URL and API key must be provided either through environment variables (LLM_API_URL, LLM_API_KEY) or config.yaml")
    
    return config

config = load_config()
openai = OpenAI(
    base_url=config["llm_api"]["url"],
    api_key=config["llm_api"]["api_key"]
)

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

def generate_bazel_target(target: Dict) -> str:
    """Generate Bazel target configuration for a single target"""
    rule = "cc_library" if target['type'] == "static_library" else "cc_binary"
    parts = []
    parts.append(f"{rule}(")
    parts.append(f"    name = \"{target['name']}\",")
    parts.append(f"    srcs = {target['sources']},")
    if target["include_dirs"]:
        parts.append(f"    includes = {target['include_dirs']},")
    parts.append(f"    deps = {target['deps']},")
    parts.append(")")
    return "\n".join(parts)

def generate_bazel_build(ir: Dict) -> str:
    return "\n\n".join(generate_bazel_target(target) for target in ir["targets"])

def structure_docs_by_topic(documents: List[str]) -> Dict[str, str]:
    """Group documentation by topics to provide more focused context"""
    topics = {
        "build": [],
        "deployment": [], 
        "testing": []
    }
    
    for doc in documents:
        if any(word in doc.lower() for word in ["build", "compile", "bazel"]):
            topics["build"].append(doc)
        if any(word in doc.lower() for word in ["deploy", "release"]):
            topics["deployment"].append(doc)
        if any(word in doc.lower() for word in ["test", "check"]):
            topics["testing"].append(doc)
            
    return {k: "\n\n".join(v) for k,v in topics.items()}

def validate_bazel_config(build_content: str) -> Tuple[bool, str]:
    """Validate generated Bazel build file"""
    required_patterns = [
        r"cc_(library|binary)",
        r"name\s*=",
        r"srcs\s*="
    ]
    
    for pattern in required_patterns:
        if not re.search(pattern, build_content):
            return False, f"Missing required pattern: {pattern}"
            
    return True, ""

def postprocess_config(config: Dict) -> Dict:
    """Clean up and normalize generated config"""
    if "build" not in config:
        config["build"] = {}
    if "tool" not in config["build"]:
        config["build"]["tool"] = "bazel"
    return config

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
    docs = load_rag_docs(doc_path)
    structured_docs = structure_docs_by_topic(docs.split("\n\n"))
    
    # Use relevant section based on query keywords
    context = structured_docs["build"]  
    
    prompt = f"""
    Based on this BUILD documentation:
    {context}

    Question: {context_query}
    
    Generate YAML configuration following the structure:
    build:
      tool: bazel 
      targets: [list of targets]
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
    
    is_valid, error = validate_bazel_config(build_txt)
    if not is_valid:
        print(f"Warning: Generated BUILD file may be invalid: {error}")
        
    (component_path / "BUILD.bazel").write_text(build_txt)

    asgard_config = generate_asgard_config(asgard_doc_path, component_path.name)
    asgard_config = postprocess_config(asgard_config)
    (component_path / "config.yaml").write_text(yaml.dump(asgard_config))

    print("Миграция завершена. Проверьте BUILD.bazel и config.yaml.")

def migrate_from_paths(component_path: str, asgard_doc_path: str) -> Tuple[bool, str]:
    try:
        migrate_component(Path(component_path), Path(asgard_doc_path))
        return True, "Миграция успешно завершена"
    except Exception as e:
        return False, f"Ошибка при миграции: {str(e)}"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("component_path", type=str, help="Путь к папке компонента")
    parser.add_argument("asgard_doc_path", type=str, help="Путь к документации Asgard")
    args = parser.parse_args()

    success, message = migrate_from_paths(args.component_path, args.asgard_doc_path)
    print(message)