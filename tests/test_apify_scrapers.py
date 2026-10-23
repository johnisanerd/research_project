from ingestion.sources.apify_scrapers import ApifyScraperManager


PAGES = [
    {
        "page_number": 1,
        "search_parameters": {"q": "RAG", "hl": "en", "max_pages": 2},
        "news_results": [
            {
                "position": 1,
                "title": "Retrieval-augmented generation moves into production",
                "link": "https://example.com/rag-production",
                "source": "Example News",
                "snippet": "Teams are shipping RAG pipelines.",
                "date": "3 hours ago",
                "published_at": "2026-10-22 14:05:00 UTC",
                "thumbnail": "https://example.com/rag.jpg",
            },
            {
                "position": 2,
                "title": "Vector databases add hybrid search",
                "link": "https://example.com/hybrid-search",
                "source": "Example Daily",
                "date": "1 day ago",
                "published_at": "2026-10-21 09:00:00 UTC",
            },
        ],
    },
    {
        "page_number": 2,
        "search_parameters": {"q": "RAG", "hl": "en", "max_pages": 2},
        "news_results": [
            {
                "position": 3,
                "title": "Evaluating RAG answers",
                "link": "https://example.com/rag-evals",
                "source": "Example Weekly",
                "snippet": "A look at answer-quality metrics.",
                "date": "2 days ago",
                "published_at": "2026-10-20 18:30:00 UTC",
            }
        ],
    },
]


class FakeActor:
    def __init__(self, run_inputs):
        self.run_inputs = run_inputs

    def call(self, run_input=None, timeout_secs=None):
        self.run_inputs.append(run_input)
        return {"defaultDatasetId": "dataset-1"}


class FakeDataset:
    def __init__(self, pages):
        self.pages = pages

    def iterate_items(self):
        yield from self.pages


class FakeApifyClient:
    def __init__(self, pages):
        self.pages = pages
        self.actor_ids = []
        self.run_inputs = []

    def actor(self, actor_id):
        self.actor_ids.append(actor_id)
        return FakeActor(self.run_inputs)

    def dataset(self, dataset_id):
        assert dataset_id == "dataset-1"
        return FakeDataset(self.pages)


def build_manager(pages):
    manager = ApifyScraperManager()
    manager.client = FakeApifyClient(pages)
    return manager


def test_google_news_actor_maps_input_and_page_items():
    manager = build_manager(PAGES)

    results = manager._run_google_news_actor("RAG", 20)

    assert manager.client.actor_ids == ["johnvc/GoogleNewsAPI"]
    assert manager.client.run_inputs == [{"q": "RAG", "hl": "en", "max_pages": 2}]
    assert [item["url"] for item in results] == [
        "https://example.com/rag-production",
        "https://example.com/hybrid-search",
        "https://example.com/rag-evals",
    ]
    assert results[0] == {
        "title": "Retrieval-augmented generation moves into production",
        "content": "Teams are shipping RAG pipelines.",
        "authors": ["Example News"],
        "publication_date": "2026-10-22",
        "url": "https://example.com/rag-production",
        "source_type": "apify_google_news",
        "metadata": {
            "source_name": "Example News",
            "image_url": "https://example.com/rag.jpg",
            "query": "RAG",
        },
    }
    assert results[1]["content"] == ""
    assert results[1]["metadata"]["image_url"] == ""


def test_google_news_actor_caps_results_per_query():
    manager = build_manager(PAGES)

    results = manager._run_google_news_actor("RAG", 2)

    assert manager.client.run_inputs == [{"q": "RAG", "hl": "en", "max_pages": 1}]
    assert len(results) == 2
