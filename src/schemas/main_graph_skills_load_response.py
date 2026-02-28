from pydantic import BaseModel, Field

class MainGraphSkillsLoadResponse(BaseModel):
    get_skills_reasoning: str = Field(
        description="Your step-by-step thinking process for selecting which skills to load. You can analyze the user's initial query and the skills overview to determine which skill is most relevant to solving the riddle. Keep your analysis concise (1-2 sentences) and focused solely on skill selection."
    )
    loaded_skill_content: str = Field(
        description="The detailed content of the skill you loaded, including the step-by-step tactical workflow defined in that specific skill. This will become your primary operating system for solving the riddle, so make sure to include all the rules and guidelines specified in the loaded skill."
    )