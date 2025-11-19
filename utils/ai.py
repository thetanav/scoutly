import os
import google.generativeai as genai
from typing import List


# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


async def extract_search_keywords(user_prompt: str) -> List[str]:
    """Extract search keywords from user prompt using Gemini."""
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    prompt = f"""What are the main topics or subjects in this question that I should search for?

Question: "{user_prompt}"

Return just the key search terms, separated by commas. For example:
Question: "What are the health benefits of meditation?"
Answer: meditation benefits, health benefits meditation, mindfulness benefits

Question: "How does climate change affect polar bears?"
Answer: climate change polar bears, polar bear habitat, global warming arctic"""
    
    try:
        response = model.generate_content(prompt)
        keywords_text = response.text.strip()
        # Clean up and split
        keywords = []
        for line in keywords_text.split('\n'):
            if ',' in line or 'Answer:' in line:
                # Extract the answer part
                if 'Answer:' in line:
                    line = line.split('Answer:')[1].strip()
                parts = [p.strip() for p in line.split(',') if p.strip()]
                keywords.extend(parts)
                break
        
        # If no keywords found, try the whole text
        if not keywords:
            keywords = [k.strip() for k in keywords_text.split(',') if k.strip()]
        
        # Filter and clean
        final_keywords = []
        for k in keywords:
            k = k.strip('"').strip("'")
            if len(k) > 5 and not k.lower().startswith(('what', 'how', 'why')):
                final_keywords.append(k)
        
        return final_keywords[:4] if final_keywords else [' '.join(user_prompt.split()[2:6])]  # Skip question word and get next words
    except Exception as e:
        # Simple fallback: remove question words and take key phrases
        words = user_prompt.lower().replace('?', '').split()
        # Remove question words
        question_words = {'what', 'how', 'why', 'when', 'where', 'who', 'which', 'did', 'was', 'were', 'has', 'have', 'does', 'do', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'with', 'about', 'happened'}
        filtered_words = [w for w in words if w not in question_words and len(w) > 2]
        if len(filtered_words) >= 3:
            return [' '.join(filtered_words[:3]), ' '.join(filtered_words)]
        else:
            return [' '.join(filtered_words)]


async def ai_finder(folder_name: str, topic: str) -> str:
    """Extract important information related to the topic from all files in the folder using Gemini Flash 2.0 lite."""
    model = genai.GenerativeModel('gemini-2.5-flash')  # Using flash lite equivalent
    
    all_content = []
    for filename in os.listdir(folder_name):
        if filename.endswith('.txt'):
            filepath = os.path.join(folder_name, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                all_content.append(content)
    
    combined_content = " ".join(all_content)
    
    prompt = f"Extract and summarize the most important information related to '{topic}' from the following content. Keep it to about 200 words: {combined_content[:4000]}"  # Limit input
    
    try:
        response = model.generate_content(prompt)
        return response.text[:400]  # Limit to ~200 words
    except Exception as e:
        return f"AI finder failed: {str(e)}"


async def ai_main(important_info: str, user_prompt: str) -> str:
    """Respond to user based on important info and user prompt using Google Flash 2.5."""
    model = genai.GenerativeModel('gemini-2.5-flash')  # Using pro as equivalent to 2.5
    
    full_prompt = f"Based on this important information: {important_info}\n\nRespond to the user's question: {user_prompt}"
    
    try:
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"AI main failed: {str(e)}"