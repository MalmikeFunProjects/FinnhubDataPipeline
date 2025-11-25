import threading

class Singleton(type):
    """
    A thread-safe metaclass that ensures only one instance of a class is created.
    """
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super(Singleton, cls).__call__(*args, **kwargs)
                cls._instances[cls] = instance
            elif args or kwargs:
                instance = cls._instances[cls]
                if hasattr(instance, "update") and callable(instance.update):
                    instance.update(*args, **kwargs)
            return cls._instances[cls]

    @classmethod
    def clear(cls):
        """
        Clear all singleton instances.
        """
        with cls._lock:
            cls._instances.clear()
