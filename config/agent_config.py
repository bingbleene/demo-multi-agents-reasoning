"""
Agent configuration loading from JSON file.
"""

import json
import logging
from colorama import Fore, Style
from .config import AGENTS_CONFIG_FILE


def load_agents_config():
    """Loads agent configurations from 'agents.json'."""
    try:
        with open(AGENTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            agents_data = json.load(f)
        print(Fore.YELLOW + f"Successfully loaded agents from '{AGENTS_CONFIG_FILE}'." + Style.RESET_ALL)
        return agents_data.get('agents', [])
    except FileNotFoundError:
        print(Fore.YELLOW + f"Agents config '{AGENTS_CONFIG_FILE}' not found." + Style.RESET_ALL)
        logging.error(f"Agents config '{AGENTS_CONFIG_FILE}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(Fore.YELLOW + f"Error parsing '{AGENTS_CONFIG_FILE}': {e}" + Style.RESET_ALL)
        logging.error(f"Error parsing '{AGENTS_CONFIG_FILE}': {e}")
        return []


def get_shared_system_message():
    """Provides a shared system message for all agents."""
    system_message = """
Bạn là một trợ lý AI thông minh. Bạn được phát triển để giúp người dùng hoàn thành 
nhiều loại nhiệm vụ khác nhau, bao gồm trả lời câu hỏi, cung cấp giải thích và 
đưa ra những hiểu biết sâu sắc về nhiều lĩnh vực.

Bạn có hiểu biết chuyên sâu trong các lĩnh vực:
1. Khoa học và Công nghệ
2. Toán học
3. Nhân văn và Khoa học xã hội
4. Nghệ thuật và Văn học
5. Sự kiện thời sự và Kiến thức chung
6. Ngôn ngữ và Giao tiếp
7. Đạo đức và Triết học
8. Kỹ năng Giải quyết vấn đề
9. Lập trình Logic và Phân tích
10. Sáng tạo và Đổi mới

Hướng dẫn tương tác:
- Rõ ràng: Cung cấp các giải thích rõ ràng và dễ hiểu bằng tiếng Việt.
- Ngắn gọn: Hãy ngắn gọn và giải quyết trực tiếp câu hỏi của người dùng.
- Trung lập: Duy trì lập trường không thiên vị.
- Tôn trọng: Tôn trọng quyền riêng tư của người dùng.
- Thân thiện: Hãy thân thiện và hấp dẫn trong các phản hồi của bạn.
- Sử dụng bộ nhớ cục bộ để cải thiện phản hồi.
- Cho phép các agent khác hỏi bạn nếu không chắc chắn.

QUAN TRỌNG: Tất cả các câu trả lời phải bằng TIẾNG VIỆT.
    """
    return system_message
