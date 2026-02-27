import asyncio
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.utils.skills_utils import get_skill_prompt

class load_skill_args(BaseModel):
    skill_path: str = Field(
        ...,
        description="The relative path to the skill file within the skills directory. Example: '通用兜底类/基础事实问答.md'"
    )

@tool('load_skill', args_schema=load_skill_args)
def load_skill(skill_path: str) -> str:
    """
    Load the content of a specific skill file.
    
    WHEN TO USE:
    - When you need to use a specific skill that has been defined in the skills directory.
    - The skill_path must be valid and correspond to an existing skill file.
    
    CONSTRAINT:
    - The skill_path should be relative to the skills directory and use forward slashes. Example: '通用兜底类/基础事实问答.md'
    """
    return get_skill_prompt(skill_path)


if __name__ == "__main__":
    
    from src.utils.skills_utils import init_skills_cache
    
    init_skills_cache()  # 初始化技能缓存
    
    skill_content = load_skill.invoke({
        "skill_path": "通用兜底类/基础事实问答.md"
    })
    
    print(skill_content)