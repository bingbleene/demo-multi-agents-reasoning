"""
Response blending logic for combining agent responses.
"""

import logging
from colorama import Fore, Style
from config.openai_client import client
from config.agent_config import get_shared_system_message
from config.config import OPENAI_MODEL


def blend_responses(agent_responses, user_prompt):
    """Combines multiple agent responses into a single optimal response."""
    combined_prompt = (
        "Vui lòng kết hợp những phản hồi này thành một câu trả lời tối ưu duy nhất.\n"
        f"Câu hỏi: '{user_prompt}'\n"
        "Các phản hồi:\n"
        + "\n\n".join(f"Phản hồi từ {name}:\n{response}" 
                      for name, response in agent_responses)
        + "\n\nCung cấp một phản hồi được kết hợp ngắn gọn, chính xác. "
        + "QUAN TRỌNG: Trả lời plain text, KHÔNG SỬ DỤNG Markdown, KHÔNG có dấu #, *, **, [, ], v.v."
    )

    try:
        shared_system = get_shared_system_message()
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": shared_system},
                {"role": "user", "content": combined_prompt}
            ]
        )

        blended_reply = response.choices[0].message.content.strip()

        usage = getattr(response, 'usage', None)
        if usage:
            total_tokens = getattr(usage, 'total_tokens', 0)

        return blended_reply
    except Exception as e:
        logging.error(f"Error blending responses: {e}")
        return "Đã xảy ra lỗi trong quá trình kết hợp phản hồi."
