import math

def paginate_web_content(full_content, page_number, page_size) -> str:
    if not full_content:
        return "The url content is empty."
    
    total_length = len(full_content)
    total_pages = math.ceil(total_length / page_size)
    
    if page_number < 1 or page_number > total_pages:
        return f"Error: Page number {page_number} is out of range. Total pages: {total_pages}."
    
    start_index = (page_number - 1) * page_size
    end_index = min(start_index + page_size, total_length)
    current_content = full_content[start_index:end_index]
    
    end_notice = ""
    if page_number < total_pages:
        end_notice = (
        f"Content truncated.This is page {page_number} of {total_pages}.\n"
        f"To read the next page, please call this tool again with page_number={page_number + 1}.\n"
        f"Or you can set page_number to a specific page number to read that page directly."
        )
    else:
        end_notice = "This is the last page of the content."
    
    return_content = (
        f"TOTAL LENGTH: {total_length} characters\n"
        f"PAGE NUMBER: {page_number}/{total_pages}\n"
        f"CONTENT:\n"
        f"{current_content}\n"
        f"SYSTEM NOTICE: "
        f"{end_notice}\n"
    )
    return return_content