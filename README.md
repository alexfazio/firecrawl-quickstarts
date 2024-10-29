# Firecrawl Quickstarts

Firecrawl Quickstarts is a collection of projects designed to help developers quickly get started with building applications using the Firecrawl API. Each quickstart provides a foundation that you can easily build upon and customize for your specific needs.

## Getting Started

To use these quickstarts, you'll need a Firecrawl API key. If you don't have one yet, you can sign up for free at [firecrawl.dev](https://firecrawl.dev).

## Available Quickstarts

### Firecrawl Web Crawling with OpenAI and Anthropic

This quickstart introduces how to integrate Firecrawl with OpenAI's Anthropic models to search and extract information based on specific user objectives. Learn to map a website, identify relevant pages, and retrieve content aligned with the objective. Ideal for targeted information gathering.

[Go to Firecrawl Web Crawling with OpenAI and Anthropic](./claude_researcher_with_map)

### Integrating OpenAI o1 Models with Firecrawl

Explore how to enhance the Firecrawl web crawling process with OpenAI’s o1 reasoning models. This quickstart guides you in using these advanced models to generate search parameters, map sites, and validate extracted content, enhancing the precision and relevance of data extraction.

[Go to Integrating OpenAI o1 Models with Firecrawl](./crawl_and_extract_with_openai_o1)

### Building a Web Crawler with Grok-2 and Firecrawl

Combine Grok-2’s AI-powered understanding with Firecrawl’s search to create an intelligent web crawler. This quickstart demonstrates building a targeted crawler that finds and processes structured data on web pages, with output in JSON format for seamless data handling.

[Go to Building a Web Crawler with Grok-2 and Firecrawl](./crawl_and_extract_with_xai_grok)

### Firecrawl Map Endpoint Quickstart

Learn how to use Firecrawl's Map endpoint to create comprehensive sitemaps from single URLs. This quickstart is perfect for efficiently gathering website structures, enabling tasks such as content mapping, SEO analysis, and scalable web data extraction.

[Go to Firecrawl Map Endpoint Quickstart](./firecrawl_map_endpoint_tutorial)

### Job Board Scraping with Firecrawl and OpenAI

Automate job listing extraction and analysis with Firecrawl and OpenAI’s Structured Outputs. This quickstart demonstrates scraping job boards, extracting structured job details, and matching listings to a user’s resume with schema-compliant outputs for reliable data processing.

[Go to Job Board Scraping with Firecrawl and OpenAI](./job_scraping_tutorial)

### Firecrawl LLM Extract Tutorial

Learn how to use Firecrawl’s LLM-powered data extraction features. This quickstart covers extracting structured data from web pages, with options for schema-defined and prompt-only extraction, making it adaptable for diverse data formats and applications.

[Go to Firecrawl LLM Extract Tutorial](./llm_extract_tutorial)

## General Usage

Each quickstart project comes with its own README and setup instructions. Generally, you'll follow these steps:

1. **Clone this repository**

   ```bash
   git clone https://github.com/yourusername/firecrawl-quickstarts.git
   ```

2. **Navigate to the specific quickstart directory**

   ```bash
   cd firecrawl-quickstarts/web-scraping-quickstart
   ```

3. **Install the required dependencies**

   ```bash
   pip install -r requirements.txt  # For Python projects
   npm install                      # For Node.js projects
   ```

4. **Set up your Firecrawl API key as an environment variable**

   ```bash
   export FIRECRAWL_API_KEY=fc-YOUR_API_KEY
   ```

5. **Run the quickstart application**

   ```bash
   python app.py    # For Python projects
   node app.js      # For Node.js projects
   ```

## Explore Further

To deepen your understanding of working with Firecrawl and its API, check out these resources:

- [**Firecrawl Documentation**](https://docs.firecrawl.dev) - Comprehensive guides and API references
- [**Firecrawl SDKs**](https://docs.firecrawl.dev/sdks/overview) - Explore our SDKs for [Python](https://docs.firecrawl.dev/sdks/python), [Node.js](https://docs.firecrawl.dev/sdks/node), [Go](https://docs.firecrawl.dev/sdks/go), and [Rust](https://docs.firecrawl.dev/sdks/rust)
- [**LLM Framework Integrations**](https://docs.firecrawl.dev/integrations/overview) - Learn how to use Firecrawl with frameworks like LangChain and Llama Index
- [**Firecrawl API Reference**](https://docs.firecrawl.dev/api-reference/introduction) - Detailed API endpoints and parameters

## Contributing

We welcome contributions to the Firecrawl Quickstarts repository! If you have ideas for new quickstart projects or improvements to existing ones, please open an issue or submit a pull request.

## Community and Support

- Join our [Firecrawl Discord community](https://discord.com/invite/gSmWdAkdwd) for discussions and support
- Follow us on [Twitter](https://twitter.com/firecrawl_dev) and [LinkedIn](https://www.linkedin.com/company/104100957) for updates
- Check out the [Firecrawl Support Documentation](https://docs.firecrawl.dev) for additional help

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*It is the sole responsibility of the end users to respect websites' policies when scraping, searching, and crawling with Firecrawl. Users are advised to adhere to the applicable privacy policies and terms of use of the websites prior to initiating any scraping activities. By default, Firecrawl respects the directives specified in the websites' robots.txt files when crawling. By utilizing Firecrawl, you expressly agree to comply with these conditions.*

[↑ Back to Top ↑](#firecrawl-quickstarts)

## License

[MIT](https://opensource.org/licenses/MIT)

Copyright (c) 2024-present, Alex Fazio
