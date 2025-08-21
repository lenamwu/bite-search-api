# Recipe Search API

A FastAPI service that provides Google Custom Search functionality specifically for recipes with image validation and rating extraction.

## Features

- 🔍 **Google Custom Search Integration** - Search for recipes across multiple recipe sites
- 🖼️ **Image Validation** - Validates images through weserv.nl proxy
- ⭐ **Rating Extraction** - Extracts ratings from search snippets
- 🏷️ **Source Identification** - Clean domain names for recipe sources
- ⚡ **Fast Response** - Optimized for quick search results

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Get Google API credentials:**
   - Google API Key: https://console.cloud.google.com/apis/credentials
   - Custom Search Engine ID: https://cse.google.com/cse/

3. **Run the server:**
```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## API Usage

### Search Endpoint

**GET** `/search`

**Query Parameters:**
- `q` (required): Search query (e.g., "chocolate chip cookies")
- `key` (required): Your Google API key
- `cx` (required): Your Google Custom Search Engine ID
- `num` (optional): Number of results (1-10, default: 10)

**Example Request:**
```
GET /search?q=banana%20bread&key=YOUR_API_KEY&cx=c2e6aaeeec3e34278&num=5
```

**Example Response:**
```json
{
  "results": [
    {
      "title": "Best Banana Bread Recipe",
      "url": "https://www.allrecipes.com/recipe/17066/janets-rich-banana-bread/",
      "image": "https://www.allrecipes.com/thmb/...",
      "source": "allrecipes.com",
      "rating": 4.7,
      "snippet": "This banana bread recipe creates the most delicious, moist loaf with loads of banana flavor. Why compromise the banana flavor? Friends and family love my recipe and say it's by far the best! It tastes wonderful and is so easy to make."
    }
  ],
  "total_results": 1250000,
  "search_time": "0.45"
}
```

### Other Endpoints

- **GET** `/` - API information and examples
- **GET** `/health` - Health check
- **GET** `/docs` - Interactive API documentation

## Integration with FlutterFlow

Use this API as your search endpoint in FlutterFlow:

1. **API Base URL:** `http://your-server:8001`
2. **Endpoint:** `/search`
3. **Method:** GET
4. **Query Parameters:**
   - `q`: `{search_variable}`
   - `key`: `{your_google_api_key}`
   - `cx`: `c2e6aaeeec3e34278`
   - `num`: `10`

## Response Fields

- `title`: Recipe title from Google search
- `url`: Direct URL to the recipe page
- `image`: Google image URL (validated through weserv.nl)
- `source`: Clean domain name (e.g., "allrecipes.com")
- `rating`: Extracted rating (0-5 scale) if available
- `snippet`: Recipe description from search results

## Supported Recipe Sites

Your Custom Search Engine should include:
- allrecipes.com
- food.com
- thetableofspice.com
- foodnetwork.co.uk
- (Add more as needed)

## Architecture

This search API works perfectly with your existing scraper API:

1. **Search API** (this project) - Fast recipe discovery
2. **Scraper API** (bite-scraper-api) - Detailed recipe extraction when user saves

## Deployment

The API runs on port 8001 by default to avoid conflicts with your scraper API (port 8000).

For production deployment, consider:
- Environment variables for API keys
- Rate limiting
- Caching for popular searches
- Load balancing
