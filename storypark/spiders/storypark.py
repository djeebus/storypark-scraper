import json
import logging
import os.path
import re

from scrapy import Spider
from scrapy.http import Request, Response

from storypark.items import StoryparkItem


emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)


class StoryPark(Spider):
    name = 'storypark'

    def __init__(self, root_path: str, **kwargs):
        super().__init__(**kwargs)

        self.root_path = root_path

    async def start(self):
        yield Request(
            'https://app.storypark.com/api/v3/users/me',
            cookies={
                '_session_id': os.environ["STORYPARK_SESSION_ID"],
            },
        )

    def parse(self, response: Response, **kwargs):  # parses the users/me endpoint
        body = json.loads(response.body)

        for child in body['user']['children']:
            child_id = child['id']
            yield Request(
                f'https://app.storypark.com/api/v3/children/{child_id}/stories'
                f'?sort_by=updated_at&story_type=all',
                callback=self._parse_stories,
                cookies=response.request.cookies,
                meta={'child_id': child_id},
            )

    def _parse_stories(self, response: Response):
        body = json.loads(response.body)

        next_page_token = body.get('next_page_token')

        for story in body['stories']:
            date = story['date']  # "2025-07-11"
            title = story['title']
            dir_name = f'{date} - {title}'
            for index, media in enumerate(story['media']):
                media_type = media['type']
                if media_type not in ('image', 'video'):
                    self.log(f'unknown media type: {media_type}', level=logging.WARNING)
                    continue

                content_type = media['content_type']
                file_ext = file_exts.get(content_type)
                if not file_ext:
                    self.log(f'unknonwn content type: {content_type}', level=logging.WARNING)
                    continue

                media_url = media['original_url']
                file_name = f'{str(index).zfill(2)}{file_ext}'
                filename = os.path.join(self.root_path, dir_name, file_name)
                filename = emoji_pattern.sub(r'', filename)
                if os.path.exists(filename):
                    self.log(f'{filename} already exists, skipping')
                    continue

                yield Request(
                    url=media_url,
                    callback=self._download_item,
                    meta={'filename': filename},
                    cookies=response.request.cookies,
                )

        if next_page_token:
            child_id = response.meta['child_id']
            yield Request(
                f'https://app.storypark.com/api/v3/children/{child_id}/stories'
                f'?sort_by=updated_at&story_type=all&page_token={next_page_token}',
                callback=self._parse_stories,
                cookies=response.request.cookies,
                meta=response.meta,
            )

    def _download_item(self, response: Response):
        filename = response.meta['filename']
        dirname = os.path.dirname(filename)
        os.makedirs(dirname, exist_ok=True)

        self.log('saving %s' % filename)
        with open(filename, 'wb') as local:
            local.write(response.body)

        return StoryparkItem(
            image_url=response.url,
            filename=filename,
        )

file_exts = {
    'image/jpeg': '.jpg',
    'video/mp4': '.mp4',
}
