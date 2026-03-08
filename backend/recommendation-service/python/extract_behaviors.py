#!/usr/bin/env python3
"""Extract user_behaviors INSERT statements from SQL and write to JSON."""

import json
import re
from pathlib import Path

SQL_PATH = Path(r'd:\code\market\backend\data\orders_and_behaviors.sql')
OUTPUT_PATH = Path(r'd:\code\market\backend\recommendation-service\python\data\behaviors.json')

# Pattern for (user_id, product_id, 'behavior_type', 'created_at')
TUPLE_PATTERN = re.compile(r"\(\s*(\d+)\s*,\s*(\d+)\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*\)")

def main():
    content = SQL_PATH.read_text(encoding='utf-8')
    
    start = content.find("INSERT INTO user_behaviors (user_id, product_id, behavior_type, created_at) VALUES")
    if start == -1:
        raise ValueError("user_behaviors INSERT not found")
    
    end_match = re.search(r'\nINSERT INTO \w+', content[start + 50:])
    end = start + end_match.start() if end_match else len(content)
    section = content[start:end]
    
    section = re.sub(r'--[^\n]*', ' ', section)
    
    behaviors = []
    for match in TUPLE_PATTERN.finditer(section):
        user_id, product_id, behavior_type, created_at = match.groups()
        behaviors.append({
            "userId": int(user_id),
            "productId": int(product_id),
            "behaviorType": behavior_type,
            "createdAt": created_at,
        })
    
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(behaviors, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Wrote {len(behaviors)} behaviors to {OUTPUT_PATH}")

if __name__ == '__main__':
    main()

