import redis
from django.conf import settings
from loguru import logger


class RedisUtils:
    
    def __init__(self):
        self.redis_instance = redis.StrictRedis.from_url(
            settings.CACHES['default']['LOCATION'])
        logger.info("Redis instance created")


    def save(self, key, value, expiry=None):
        try:
            if expiry:
                self.redis_instance.set(key, value, ex=expiry)
                logger.debug(f"Saved key {key} with expiry {expiry}")
            else:
                self.redis_instance.set(key, value)
                logger.debug(f"Saved key {key} without expiry")
        except redis.RedisError as e:
            logger.error(f"Error saving key {key}: {e}")


    def get(self, key):
        try:
            value = self.redis_instance.get(key)
            logger.debug(f"Retrieved key {key} with value {value}")
            return value
        except redis.RedisError as e:
            logger.error(f"Error retrieving key {key}: {e}")
            return None
        

    def delete(self, key):
        try:
            result = self.redis_instance.delete(key)
            logger.debug(f"Deleted key {key}")
            return result
        except redis.RedisError as e:
            logger.error(f"Error deleting key {key}: {e}")
            return 0
        

    def hset(self, name, key, value):
        try:
            self.redis_instance.hset(name, key, value)
            logger.debug(
                f"Set hash field {key} in hash {name} with value {value}")
        except redis.RedisError as e:
            logger.error(f"Error setting hash field {key} in hash {name}: {e}")


    def hget(self, name, key):
        try:
            value = self.redis_instance.hget(name, key)
            logger.debug(
                f"Retrieved hash field {key} from hash {name} with value {value}")
            return value
        except redis.RedisError as e:
            logger.error(
                f"Error retrieving hash field {key} from hash {name}: {e}")
            return None
        

    def hgetall(self, name):
        try:
            result = self.redis_instance.hgetall(name)
            logger.debug(f"Retrieved all fields from hash {name}")
            return result
        except redis.RedisError as e:
            logger.error(f"Error retrieving all fields from hash {name}: {e}")
            return {}
        

    def hdel(self, name, key):
        try:
            result = self.redis_instance.hdel(name, key)
            logger.debug(f"Deleted hash field {key} from hash {name}")
            return result
        except redis.RedisError as e:
            logger.error(
                f"Error deleting hash field {key} from hash {name}: {e}")
            return 0