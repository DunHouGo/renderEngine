from Renderer import decorators
import time

@decorators.TIMEIT(True)
def test_time():
    time.sleep(2)
    
@decorators.Retry()
def test_retry():
    raise RuntimeError("Can not work.")

@decorators.CheckArgType(name=str)
def test_arg_type(name: str = 'Bob', age: int = 42):
    print(f"{name} aged {age}")

def is_int(arg: any) -> bool:
    return isinstance(arg, int)

@decorators.CheckArgCallback(('a', lambda x: x >= 0, lambda x: int(x)),
                             ('b', lambda x: isinstance(x, (int, float)), lambda x: int(x)-1))
def test_arg_callback(a: int = 1, b: int = 2.0):
    print(f"{a} : {type(a)}, {b} : {type(b)}")
    
if __name__ == '__main__':
    test_time()
    test_retry()
    test_arg_type()
    test_arg_callback()
    