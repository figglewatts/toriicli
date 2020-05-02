from io import IOBase
from typing import Generator, Union

import boto3

from . import provider


class S3StorageProvider(provider.StorageProvider):
    """Storage provider for S3 bucket storage.

    Looks for credentials in environment variables 'AWS_ACCESS_KEY_ID' and
    'AWS_SECRET_ACCESS_KEY'.

    Attributes:
        region (str): The S3 region the bucket is in.
        endpoint (str): The endpoint URL of the S3 service.
        container (str): The S3 bucket we're using for storage.
    """
    def __init__(self, region: str, endpoint: str, container: str):
        self.container = container
        self.session = boto3.session.Session()
        self.client = self.session.client("s3",
                                          region_name=region,
                                          endpoint_url=endpoint)

    def store(self,
              data: Union[IOBase, str, bytes],
              key: str,
              acl: str = None) -> None:
        if issubclass(type(data), IOBase):
            self.client.upload_fileobj(data, self.container, key)
        elif type(data) == str:
            self.client.put_object(Body=data.encode("utf-8"),
                                   Bucket=self.container,
                                   Key=key)
        elif type(data) == bytes:
            self.client.put_object(Body=data, Bucket=self.container, Key=key)
        else:
            raise TypeError(f"invalid data type '{type(data)}'")

        if acl is not None:
            self.client.put_object_acl(Bucket=self.container, Key=key, ACL=acl)

    def retrieve(self, key: str, filename: str) -> None:
        self.client.download_file(self.container, key, filename)

    def ls(self) -> Generator[str, None, None]:
        objects = self.client.list_objects_v2(Bucket=self.container)
        yield from [obj["Key"] for obj in objects["Contents"]]