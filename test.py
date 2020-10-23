from unittest import TestCase

from mru import mru_cache


class MRUCacheTestCase(TestCase):
    def test_correct_cache(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        data = 'data'
        result = func(data)
        self.assertEqual(result, func(data))
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

    def test_misses_and_hits(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 0)
        func(1)
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 1)
        func(1)
        self.assertEqual(func.cache.hits, 1)
        # self.assertEqual(func.cache.fast_hits, 1)
        self.assertEqual(func.cache.misses, 1)

    def test_args_and_kwargs_caching(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        func(1, (), [], a=2, b={}, c='string')
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 1)

        func(1, (), [], a=2, b={}, c='string')
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

    def test_args_position(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        func(1, 2, 3)
        func(3, 1, 2)
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 2)

    def test_kwargs_position(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        func(a=1, b=2)
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 1)
        func(b=2, a=1)
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

    def test_pass_dict(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        func({})
        func({})
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

        func({'key': {'key': {(1, 0): 'value'}}})
        func({'key': {'key': {(1, 0): 'value'}}})
        self.assertEqual(func.cache.hits, 2)
        self.assertEqual(func.cache.misses, 2)

    def test_pass_list(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        func([])
        func([])
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

        func([[[1, 2], 3], 4])
        func([[[1, 2], 3], 4])
        self.assertEqual(func.cache.hits, 2)
        self.assertEqual(func.cache.misses, 2)

    def test_pass_object(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        obj = object()
        func(obj)
        func(obj)
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

    def test_pass_different_object(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        func(object())
        func(object())
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 2)

    def test_pass_function(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        def f(): pass
        func(f)
        func(f)
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

    def test_pass_lambda(self):
        @mru_cache
        def func(*args, **kwargs):
            return args, kwargs

        f = lambda x: x
        func(f)
        func(f)
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)
        func(lambda x: x)  # Будет создан новый объект лямбда функции
        self.assertEqual(func.cache.misses, 2)

    def test_discarding(self):
        @mru_cache(size=2)
        def func(*args, **kwargs):
            return args, kwargs

        func(1)
        func(2)
        func(3)  # Выталкивает из кэша элемент "2"
        func(2)  # Не удаётся найти в кэше
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 4)

    def test_discarding_2(self):
        @mru_cache(size=2)
        def func(*args, **kwargs):
            return args, kwargs

        # Заполняем кэш
        func(1)
        func(2)
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 2)

        func(1)  # Уже есть в кэше
        # После вызова становится последним используемым и при заполнении кэша будет удалён
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 2)

        func(3)  # Выталкивает из кэша элемент "1"
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 3)

        func(1)  # Не удаётся найти в кэше
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 4)

    def test_caching_none_value(self):
        @mru_cache
        def func():
            return None

        func()
        self.assertEqual(func.cache.hits, 0)
        self.assertEqual(func.cache.misses, 1)
        func()
        self.assertEqual(func.cache.hits, 1)
        self.assertEqual(func.cache.misses, 1)

    def test_disable_cache_if_size_invalid(self):
        @mru_cache(size=0)
        def func():
            return None

        self.assertFalse(hasattr(func, 'cache'))

        @mru_cache(size='string')
        def func():
            return None

        self.assertFalse(hasattr(func, 'cache'))

    def test_many_functions(self):
        @mru_cache
        def func1(): pass

        @mru_cache
        def func2(): pass

        self.assertEqual(func1.cache.hits, 0)
        self.assertEqual(func1.cache.misses, 0)
        self.assertEqual(func2.cache.hits, 0)
        self.assertEqual(func2.cache.misses, 0)

        func1()
        self.assertEqual(func1.cache.hits, 0)
        self.assertEqual(func1.cache.misses, 1)
        self.assertEqual(func2.cache.hits, 0)
        self.assertEqual(func2.cache.misses, 0)

        func1()
        self.assertEqual(func1.cache.hits, 1)
        self.assertEqual(func1.cache.misses, 1)
        self.assertEqual(func2.cache.hits, 0)
        self.assertEqual(func2.cache.misses, 0)

        func2()
        self.assertEqual(func1.cache.hits, 1)
        self.assertEqual(func1.cache.misses, 1)
        self.assertEqual(func2.cache.hits, 0)
        self.assertEqual(func2.cache.misses, 1)

        func2()
        self.assertEqual(func1.cache.hits, 1)
        self.assertEqual(func1.cache.misses, 1)
        self.assertEqual(func2.cache.hits, 1)
        self.assertEqual(func2.cache.misses, 1)

    def test_fast_getting_cached_value(self):
        @mru_cache(optimization=True)
        def func(*args, **kwargs):
            return args, kwargs

        self.assertEqual(func.cache.fast_hits, 0)

        func(1)
        func(1)
        self.assertEqual(func.cache.fast_hits, 1)

        func({1: {2: {3: {}}}})
        func({1: {2: {3: {}}}})
        self.assertEqual(func.cache.fast_hits, 2)

        func([1, [2, [3]]])
        func([1, [2, [3]]])
        self.assertEqual(func.cache.fast_hits, 3)

        def f(): pass
        func(f)
        func(f)
        # Функцию не получится сериализовать через pickle
        # Поэтому поиск её значения идёт через полный перебор
        self.assertEqual(func.cache.fast_hits, 3)

        func(object())
        func(object())
        # Все объекты класса object сериализуются в одно и то же значение
        # Но они не равны друг другу, поэтому происходит поиск полным перебором
        self.assertEqual(func.cache.fast_hits, 3)
