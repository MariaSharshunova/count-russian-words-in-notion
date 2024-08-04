import requests
import re
import os

API_KEY = os.getenv("NOTION_API_KEY")

def get_block_content(session: requests.Session, block_id: str):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    all_results = []
    next_cursor = None
    
    while True:
        params = {'page_size': 100}
        if next_cursor:
            params['start_cursor'] = next_cursor
            
        response = session.get(url, params=params)
        
        if response.status_code == 200:
            result = response.json()
            all_results.extend(result.get('results', []))
            
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break  # No more pages to fetch
        else:
            print(f"Error: {response.status_code}, {response.text}")
            break
    
    return {'results': all_results}

def count_russian_words(text: str) -> int:
    russian_words = re.findall(r'\b[а-яА-ЯёЁ]+\b', text)
    return len(russian_words)

def extract_text_and_count_paragraphs(session: requests.session, blocks: dict):
    text_content = ""
    paragraph_count = 0
    
    for block in blocks.get('results', []):
        if block['type'] == 'paragraph' and 'paragraph' in block:
            paragraph_count += 1
            for text_part in block['paragraph'].get('rich_text', []):
                if 'text' in text_part and 'content' in text_part['text']:
                    text_content += text_part['text']['content'] + " "
        elif block['type'] == 'child_page':
            child_page_content = get_block_content(session, block['id'])
            if child_page_content:
                child_text, child_paragraphs = extract_text_and_count_paragraphs(session, child_page_content)
                text_content += child_text
                paragraph_count += child_paragraphs
        elif block.get('has_children'):
            child_blocks = get_block_content(session, block['id'])
            if child_blocks:
                extracted_text, child_paragraphs = extract_text_and_count_paragraphs(session, child_blocks)
                text_content += extracted_text
                paragraph_count += child_paragraphs

    return text_content, paragraph_count

def main():
    if not API_KEY:
        raise Exception("Please set the NOTION_API_KEY environment variable")
    
    session = requests.Session()
    session.headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    page_id = os.getenv("PAGE_ID", "256d931ed96f4b2fb7ed12619a41f45e")
    page_content = get_block_content(session, page_id)
    
    if page_content:
        print(f"Total blocks fetched: {len(page_content.get('results', []))}")
        text_content, _ = extract_text_and_count_paragraphs(session, page_content)
        russian_word_count = count_russian_words(text_content)
        print(f"Number of Russian words: {russian_word_count}")
        print(f"Total difference for second half of 07/07/24: {russian_word_count - 7155}")
        
    else:
        print("Failed to retrieve page content")

if __name__ == "__main__":
    main()
