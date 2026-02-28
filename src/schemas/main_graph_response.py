from pydantic import BaseModel, Field


class MainGraphResponse(BaseModel):
    # 得到答案后的推理过程记录
    reasoning: str = Field(
        description="Your step-by-step thinking process. You can analyze the search results and formulate the answer here."
    )

    is_valid_final_answer: bool = Field(
        description="Based on your reasoning,could you ensure that the final answer is right? If you are not sure, please fill in 'False',else fill in 'True'."
    )

    reasoning_defects: str = Field(
        description="If the is_valid_final_answer is 'False', please analyze the defects in your reasoning and what information you are missing. If the is_valid_final_answer is 'True', please fill in 'None'."
    )

    final_answer: str = Field(
        description="The final concise answer in the EXACT language requested by the user. No extra words."
    )
    
    thinking_process_is_error: bool = Field(
        description="If the is_valid_final_answer is 'False', please judge whether the error is caused by wrong thinking process or wrong skills. If you think the thinking process is correct but the skill application is wrong, please fill in 'False'. If you think the thinking process itself has errors that lead to the wrong answer, please fill in 'True'."
    )
    
    
