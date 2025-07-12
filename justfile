pull-content:
    #!/usr/bin/env bash
    SCRAPY_PROJECT=storypark poetry run scrapy crawl \
      --loglevel INFO \
      storypark \
      -a root_path=./archive
