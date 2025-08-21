from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import requests
import asyncio
import aiohttp
from typing import Optional, List
import re

app = FastAPI(title="Recipe Search API", description="Google Custom Search API for recipes with validation")

class SearchResult(BaseModel):
    title: str
    url: str
    image: str
    source: str
    snippet: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_results: int
    search_time: str

# Headers for web requests
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

async def validate_image_url(image_url: str) -> bool:
    """Test if an image URL is accessible through the weserv.nl proxy"""
    if not image_url:
        return False
    
    # Test the image URL through your proxy service
    proxy_url = f"https://images.weserv.nl/?url={image_url}"
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            async with session.head(proxy_url) as response:
                # Check if the response is successful and is an image
                if response.status == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    return content_type.startswith('image/')
                return False
    except Exception:
        return False


def get_domain_name(url: str) -> str:
    """Extract clean domain name from URL"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return "unknown"

@app.get("/search", response_model=SearchResponse)
async def search_recipes(
    q: str = Query(..., description="Search query"),
    key: str = Query(..., description="Google API key"),
    cx: str = Query(..., description="Google Custom Search Engine ID"),
    num: int = Query(10, description="Number of results", ge=1, le=10)
):
    """
    Search for recipes using Google Custom Search API
    
    Returns validated results with images, ratings, and source information
    """
    
    # Google Custom Search API endpoint
    search_url = "https://www.googleapis.com/customsearch/v1"
    
    # Search parameters
    params = {
        "key": key,
        "cx": cx,
        "q": q,
        "num": min(num, 10),  # Google API limit
        "searchType": "image",  # Get image results
        "safe": "active",
        "fields": "items(title,link,snippet,image,displayLink),searchInformation(searchTime,totalResults)"
    }
    
    try:
        # Make the Google Custom Search request
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Google Search API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
    
    # Extract search results
    items = data.get("items", [])
    search_info = data.get("searchInformation", {})
    
    if not items:
        return SearchResponse(
            results=[],
            total_results=0,
            search_time=search_info.get("searchTime", "0")
        )
    
    # Process results with validation
    results = []
    validation_tasks = []
    
    for item in items:
        # Extract basic information
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        display_link = item.get("displayLink", "")
        
        # Get the recipe URL from image context
        image_info = item.get("image", {})
        recipe_url = image_info.get("contextLink", "")
        google_image = item.get("link", "")  # This is the Google image URL
        
        if not recipe_url or not google_image:
            continue
        
        # Get clean domain name
        source = get_domain_name(recipe_url)
        
        # Create result object
        result = SearchResult(
            title=title,
            url=recipe_url,
            image=google_image,
            source=source,
            snippet=snippet
        )
        
        results.append(result)
        
        # Add image validation task
        validation_tasks.append(validate_image_url(google_image))
    
    # Validate all images in parallel - only keep results with working images
    try:
        validation_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Filter results - ONLY keep results with validated working images
        validated_results = []
        for result, is_valid in zip(results, validation_results):
            # Only keep result if image validation explicitly passed
            if is_valid is True:
                validated_results.append(result)
        
        results = validated_results
        
    except Exception:
        # If validation completely fails, return all results as fallback
        pass
    
    return SearchResponse(
        results=results,
        total_results=int(search_info.get("totalResults", len(results))),
        search_time=str(search_info.get("searchTime", "0"))
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Recipe Search API"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Recipe Search API",
        "description": "Google Custom Search API for recipes with validation",
        "endpoints": {
            "search": "/search?q={query}&key={api_key}&cx={search_engine_id}&num={results}",
            "health": "/health",
            "docs": "/docs"
        },
        "example": "/search?q=chocolate%20chip%20cookies&key=YOUR_API_KEY&cx=YOUR_CX&num=10"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
