import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import re


async def scrape_wordle_answer():
    """
    Scrape the Wordle answer from Lifehacker using Playwright.
    Dynamically constructs the URL based on today's date.
    """
    # Get today's date and construct the URL
    today = datetime.now()
    month_name = today.strftime("%B").lower()
    day = today.day
    year = today.year
    
    url = f"https://lifehacker.com/entertainment/wordle-nyt-hint-today-{month_name}-{day}-{year}"
    
    print(f"Scraping: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to the page (don't wait for full load, just DOM)
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            
            # Wait for the article content to load
            await page.wait_for_selector("article", timeout=10000)
            
            # Find all paragraphs in the article
            paragraphs = await page.locator("article p").all()
            
            answer = None
            
            # Search dynamically for the paragraph containing "Ready? Today's word is"
            for para in paragraphs:
                text = await para.text_content().upper()
                if "TODAY" in text and "WORD IS" in text:
                    print(f"Found: {text}")
                    # Extract the word using regex
                    match = re.search(r"WORD IS\s+(\w+)\W*", text, re.IGNORECASE)
                    if match:
                        answer = match.group(1).upper()
                        break
            
            if answer:
                print(f"✓ Answer: {answer}")
                return answer
            else:
                print("✗ Could not find the answer in any paragraph")
                # Print all paragraph texts for debugging
                print("\nAll paragraphs found:")
                for i, para in enumerate(paragraphs):
                    text = await para.text_content()
                    if text.strip():
                        print(f"{i}: {text[:100]}...")
                return None
                
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            await browser.close()


def get_wordle_answer():
    """Synchronous wrapper to get the Wordle answer."""
    answer = asyncio.run(scrape_wordle_answer())
    return answer


if __name__ == "__main__":
    answer = get_wordle_answer()
    if answer:
        print(f"\nToday's Wordle answer: {answer}")
