import requests
from bs4 import BeautifulSoup
import re
import json

def parse_grades():
    url = "https://faq8.ru/read.php?2,16555"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    message_body = soup.find('div', class_='message-body')
    text = message_body.get_text(strip=False)

    data = []
    current_group = None

    for line in [l.strip() for l in text.split('\n') if l.strip()]:
        group_match = re.match(r'^(\d+[А-Яа-я]?):', line)
        if group_match:
            current_group = group_match.group(1)
            continue
        if not current_group:
            continue

        match = re.match(r'^(\d{3})\s*([2-5][+=\-]?):?\s*(.+)$', line, re.DOTALL)
        if match:
            data.append({
                "номер_зачётки": match.group(1),
                "группа": current_group,
                "оценка": match.group(2).strip(),
                "комментарий": match.group(3).strip()
            })
        else:
            special_match = re.match(r'^(\d{3})\s+(ндк?|н[\/\.]?д|недоп)\b', line, re.IGNORECASE)
            if special_match:
                data.append({
                    "номер_зачётки": special_match.group(1),
                    "группа": current_group,
                    "оценка": special_match.group(2).lower(),
                    "комментарий": ""
                })

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parse_grades()