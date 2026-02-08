
from intelligence.page_manager import PageManager, PageStatus

def test_fill_suggestion():
    pm = PageManager()
    
    # Simulate a page that is 69% filled
    status = PageStatus(
        needs_content=True,
        fill_percentage=69,
        current_page=1,
        suggestion="Test suggestion",
        issues=[]
    )
    
    target_fill = 95
    needed_fill = target_fill - status.fill_percentage
    bullet_suggestion = max(3, (needed_fill // 5))  # Logic from page_manager.py (before my potential change)
    
    print(f"Current Fill: {status.fill_percentage}%")
    print(f"Needed Fill: {needed_fill}%")
    print(f"Suggested Bullets to Add: {bullet_suggestion}")

    # Simulate logic from content_generator.py
    bullets_needed = 5
    try:
        # Extract number from suggestion string (mocking regex match)
        suggestion_text = f"Please add at least {bullet_suggestion} more..."
        import re
        match = re.search(r'at least (\d+)', suggestion_text)
        if match:
            bullets_needed = int(match.group(1)) + 2
    except:
        bullets_needed = 8
        
    print(f"Content Generator would request: {bullets_needed} bullets")

if __name__ == "__main__":
    test_fill_suggestion()
