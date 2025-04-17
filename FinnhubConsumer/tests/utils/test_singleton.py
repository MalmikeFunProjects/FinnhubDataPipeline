import pytest
import threading
from app.utils.singleton import Singleton


class SingletonTestClass(metaclass=Singleton):
    def __init__(self, value=0):
        self.value = value

    def update(self, value=0):
        self.value = value


class TestSingleton:
    def setup_method(self):
        Singleton.clear()

    def test_single_instance_created(self):
        obj1 = SingletonTestClass(1)
        obj2 = SingletonTestClass(2)

        assert obj1 is obj2
        # Since second call uses `update`, value should be updated to 2
        assert obj1.value == 2
        assert obj2.value == 2

    def test_update_called_on_reuse(self):
        obj1 = SingletonTestClass(5)
        obj2 = SingletonTestClass(value=10)

        assert obj1 is obj2
        assert obj1.value == 10

    def test_clear_singleton_instances(self):
        obj1 = SingletonTestClass(3)
        Singleton.clear()
        obj2 = SingletonTestClass(7)

        assert obj1 is not obj2
        assert obj2.value == 7

    def test_singleton_is_thread_safe(self):
        instances = []

        def create_instance(val):
            inst = SingletonTestClass(val)
            instances.append(inst)

        threads = [threading.Thread(target=create_instance, args=(i,)) for i in range(10)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert all(inst is instances[0] for inst in instances)
