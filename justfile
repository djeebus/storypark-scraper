pull-content LOG_LEVEL="INFO":
    #!/usr/bin/env bash
    SCRAPY_PROJECT=storypark poetry run scrapy crawl \
      --loglevel {{ LOG_LEVEL }} \
      storypark \
      -a root_path=./archive
