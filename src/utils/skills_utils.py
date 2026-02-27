import os
import re
from typing import Dict

_SKILLS_CACHE = {}
_SKILLS_OVERVIEW_CACHE = ""

# 获得单个技能的内容
def _parse_skillsmd_file(file_path: str) -> dict:
    
    # 得到技能内容
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', content, re.DOTALL)
    
    if match:
        front_matter = match.group(1)
        body = match.group(2).strip()
        name = re.search(r'^name:\s*(.*)$', front_matter, re.MULTILINE)
        description = re.search(r'^description:\s*(.*)$', front_matter, re.MULTILINE)
        
        return {
            "name": name.group(1).strip() if name else os.path.basename(file_path),
            "description": description.group(1).strip() if description else "",
            "content": body
        }
    
    return {
        "name": os.path.basename(file_path),
        "description": "",
        "content": content.strip()
    }

def init_skills_cache(skills_dir: str = "./src/skills") -> None:
    global _SKILLS_CACHE, _SKILLS_OVERVIEW_CACHE
    
    if not os.path.exists(skills_dir):
        print(f"Skills directory '{skills_dir}' does not exist.")
        return
    
    skills_list = []
    
    # 遍历技能目录，解析每个技能文件并缓存
    for root, _, files in os.walk(skills_dir):
        # 遍历当前目录下的所有文件
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, skills_dir).replace("\\", "/")
                parsed_data = _parse_skillsmd_file(file_path)
                _SKILLS_CACHE[rel_path] = parsed_data
                
                current_skill = f"path: '{rel_path}', name: {parsed_data['name']}, description: {parsed_data['description']}"
                skills_list.append(current_skill)
    
    _SKILLS_OVERVIEW_CACHE = f"Skills List: {len(skills_list)}\n" + "\n".join(skills_list)
    
def get_skills_overview() -> str:
    if not _SKILLS_OVERVIEW_CACHE:
        init_skills_cache()  # 如果缓存为空，尝试初始化
    
    if not _SKILLS_OVERVIEW_CACHE:
        return "Skills are none."
    return _SKILLS_OVERVIEW_CACHE

def get_skill_prompt(skill_path: str) -> str:
    if not _SKILLS_CACHE:
        init_skills_cache()  # 如果缓存为空，尝试初始化
    
    if skill_path in _SKILLS_CACHE:
        return _SKILLS_CACHE[skill_path]["content"]
    else:
        return f"Skill '{skill_path}' not found."

if __name__ == "__main__":
    init_skills_cache()
    print(get_skills_overview())
    print(get_skill_prompt("通用兜底类/基础事实问答.md"))
                