import c4d
import time
from inspect import signature
from functools import wraps
from typing import Any, Callable
import cProfile
import functools
import inspect
import io
import pstats
import typing

_C4D_VERSION: int = c4d.GetC4DVersion()

def StatusClear():
    if _C4D_VERSION >= 2025000:
        c4d.gui.StatusClear()
    else:
        c4d.StatusClear()

def StatusSetText(text: str):
    if _C4D_VERSION >= 2025000:
        c4d.gui.StatusSetText(text)
    else:
        c4d.StatusSetText(text)

def StatusSetSpin():
    if _C4D_VERSION >= 2025000:
        c4d.gui.StatusSetSpin()
    else:
        c4d.StatusSetSpin()

def StatusSetBar(percent: float, auto_clear: bool = True):
    if _C4D_VERSION >= 2025000:
        c4d.gui.StatusSetBar(percent)
    else:
        c4d.StatusSetBar(percent)

    if auto_clear and percent >= 100:
        StatusClear()

###  ==========  Decorators  ==========  ###
def Retry(count: int = 3, delay: float = 1, withOutput: bool = True) -> Callable:
    """
    Attempt to call a function, if it fails, try again with a specified delay.

    Args:
        retry (int, optional): The max amount of retries you want for the function call. Defaults to 3.
        delay (float, optional): The delay (in seconds) between each function retry. Defaults to 1.

    **Example**

    .. code-block:: python
    
        @Retry(retries=3, delay=1, withOutput=True)
        def foo():
            ...
    """
    
    if count < 1 or delay <= 0:
        raise ValueError("Retries and delay must be greater than 0.")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for i in range(count):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if withOutput: print(f"Retry: {func.__name__} {i} times")
                    if i == count:
                        break
                    else:
                        time.sleep(delay)
        return wrapper
    return decorator

def Statusbar(msg: str, spin: bool=False) -> Callable:
    """A decorator for indicating a computationally expensive process in the *Cinema4D* status bar. 

    Will set the status bar text to the argument ``msg`` and start the spinning gadget in the status bar before the function/method is being called and then clear out the status bar after the scope of the function/method has been left.

    Note:
        This decorator performs *GUI* operations and therefor is bound by the threading limitations of *Cinema4D*. It should not be used on objects that are called in a threaded context.

    Args:
        msg (``any``): The message to be displayed in the status bar while the decorated function/method is running. Will be cast into a string with ``str()``.

    Returns:
        ``any``: The return value of the decorated function/method.

    **Example**
        Indicating the execution of an expensive method. Using `statusbar` as a class decorator will work analogously.

        .. code-block:: python
            
            @Statusbar("This might take a while ...")
            def some_expensive_method(self, *args, **kwargs):
                pass
    """
    def decorator(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs):
            if c4d.threading.GeIsMainThread():
                StatusSetText(str(msg))
                if spin:
                    StatusSetSpin()
                try:
                    result = func(*args, **kwargs)
                except:
                    result = False
                StatusClear()
                return result
            return False
        return wrapper
    return decorator

def CheckArgType(**type_annotations) -> Callable:
    """A decorator for check the args to debug. 

    **Example**
        Indicating the execution of an expensive method. Using `statusbar` as a class decorator will work analogously.

        .. code-block:: python
            
            @CheckArgType(data = int)
            def some_expensive_method(self, data: int = 5):
                pass
    """
    def decorator(func):
        sig = signature(func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            for param_name, value in bound_args.arguments.items():
                if param_name in type_annotations:
                    expected_type = type_annotations[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(f"Prameter {param_name} should be {expected_type.__name__} type, but got{type(value).__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def CheckArgCallback(*param_specs) -> Callable:
    """A decorator for check the args to debug. 
    
    param_specs: tuple(name, validator, transformer)

    **Example**
        Indicating the execution of an expensive method. Using `statusbar` as a class decorator will work analogously.

        .. code-block:: python
            
            @CheckArgCallback(
                ('age', lambda x: x >= 0, lambda x: int(x)),
                ('name', lambda x: len(x) > 0, str.title)
            )
            def register(name, age):
                print(f"{name}, {age}")
    """

    def decorator(func):
        sig = signature(func)
        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # dict
            args_dict = bound_args.arguments
            
            for spec in param_specs:
                if len(spec) < 2:
                    continue
                    
                param_name = spec[0]
                validator = spec[1] if len(spec) > 1 else None
                transformer = spec[2] if len(spec) > 2 else None
                
                if param_name not in args_dict:
                    continue
                    
                original_value = args_dict[param_name]
                
                try:
                    if validator is not None:
                        if not validator(original_value):
                            raise ValueError(f"Arg: {param_name} validator failed")
                    
                    # transform
                    if transformer is not None:
                        args_dict[param_name] = transformer(original_value)
                        
                except Exception as e:
                    raise ValueError(f"Arg: {param_name} progress failed: {str(e)}") from e
            
            # rebind
            new_args = []
            new_kwargs = {}
            
            for name, param in sig.parameters.items():
                if name in args_dict:
                    if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                        if len(new_args) <= param.default:
                            new_args.append(args_dict[name])
                    else:
                        new_kwargs[name] = args_dict[name]
            
            return func(*new_args, **new_kwargs)
            
        return wrapper
    return decorator



###  ==========  mxutils Decorators  ==========  ###
# copy from Maxon mxutils module, in case used in old version
# I had modified some of them for more customlized usage

T = typing.TypeVar('T', bound=typing.Callable[..., typing.Any])  #: Type description for a callable.
ID_TIMEIT_LOOKUP: str = "_boghma_mxutils_timeit_lookup"  #: The attribute name for the in-call protection mechanism.

def TIMEIT(enabled: bool, showDigits: int = 5, showArgs: bool = False, showResult: bool = False, 
           useProfiler: bool = False, inCallProtection: bool = False) -> typing.Callable[[T], T]:
    """Decorates a function call with a timing or profiling report printed to the console.

    Meant for debugging and profiling purposes only. The decorator can be enabled or disabled by passing a boolean flag
    to the decorator. When enabled, the decorator will print a report to the console after the function call has finished.

    .. warning::
    
        This decorator will have an impact on the performance of the decorated function (timing = low impact, 
        profiling = high impact). It is not recommended to use this decorator in production code.

    :param enabled: Whether the decorator should be enabled. Setting this to `False` will result in the decorated 
        function being passed through without any modifications, disabling all measurements and almost all overhead of
        the decorator. You should pass here some debug flag you defined, e.g., `IS_DEBUG`.
    :type enabled: bool
    :param showDigits: The number of digits to round timing measurements to. Only applies when `useProfiler` is `False`. 
        Defaults to `5`.
    :type showDigits: int, optional
    :param showArgs: Whether the arguments of the function call should be printed. Defaults to `False`.
    :type showArgs: bool, optional
    :param showResult: Whether the result of the function call should be printed. Defaults to `False`.
    :type showResult: bool, optional
    :param useProfiler: Whether the function should be profiled instead of timed. Defaults to `False`.
    :type useProfiler: bool, optional
    :param inCallProtection: If to mute inner calls of a recursive call chain of the decorated function. This feature
        is not thread-safe as it decorates the function or class instance object with a dictionary to keep track of 
        the call state. Defaults to `False`.
    :type inCallProtection: bool, optional


    :Example:

    .. code-block:: python

        import math
        import mxutils

        IS_DEBUG: bool = True

        # We define a recursive function and decorate it with the default timeit decorator.
        @mxutils.TIMEIT(IS_DEBUG)
        def factorial(n: int) -> int:
            return 1 if n == 0 else n * factorial(n - 1)

        # We call the function and see the time measurements. Because the function is recursive, we 
        # see the a report for each call in the recursion chain.
        factorial(3)
        # --------------------------------------------------------------------------------
        # TIMEIT: Ran 'factorial()' in 0.0 sec
        # --------------------------------------------------------------------------------
        # TIMEIT: Ran 'factorial()' in 6e-05 sec
        # --------------------------------------------------------------------------------
        # TIMEIT: Ran 'factorial()' in 0.00011 sec
        # --------------------------------------------------------------------------------
        # TIMEIT: Ran 'factorial()' in 0.00013 sec

        # We redefine the function but this time enable in-call protection. We also enable seeing 
        # the arguments and result of a function call.
        @mxutils.TIMEIT(IS_DEBUG, showArgs=True, showResult=True, inCallProtection=True)
        def factorial(n: int) -> int:
            return 1 if n == 0 else n * factorial(n - 1)

        # Now we call the function again. This time we only see the the timing for the outmost
        # call of the recursion chain.
        factorial(10)
        # --------------------------------------------------------------------------------
        # TIMEIT: Ran 'factorial((10,), {}) -> 3628800' in 1e-05 sec

        # And finally a more complex example where we decorate class methods and use full profiling.
        class Processor: 
            # The arguments we pass to the timeit decorator in this class.
            TIMEIT_KWARGS: dict[str, typing.Any] = {
                "enabled": IS_DEBUG, "showArgs": True, 
                "showResult": True, "inCallProtection": True, 
                "useProfiler": True
            }

            def __init__(self, n: int) -> None:
                self.recursive(n)
                self.iterative(n)

            @mxutils.TIMEIT(**TIMEIT_KWARGS)
            def recursive(self, n: int) -> int:
                return 1 if n == 0 else n * self.recursive(n - 1)

            @mxutils.TIMEIT(**TIMEIT_KWARGS)
            def iterative(self, n: int) -> int:
                x: int = n
                for i in range(int(n * 1000)):
                    x += math.sqrt(x)
                    x *= math.sin(i)
                return x
            
        p: Processor = Processor(50)

        # The output will look something like this. For the recursive call we mostly see the overhead
        # of the decorator. Profiling recursive functions in this manner that are not very expensive 
        # (execute in the microsecond range) is not very useful.

        # --------------------------------------------------------------------------------
        # TIMEIT: Ran 'recursive((<__main__.Processor object at 0x7fd18c0696a0>, 50), {}) -> 
        #     30414093201713378043612608166064768844377641568960512000000000000' with 302 function 
        #     calls (203 primitive calls) in 0.000 seconds
        #
        #     Ordered by: cumulative time
        #
        #     ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        #       51/1    0.000    0.000    0.000    0.000 scriptmanager:476(recursive)
        #       50/1    0.000    0.000    0.000    0.000 scriptmanager:401(wrapper)
        #         50    0.000    0.000    0.000    0.000 /Applications/Maxon Cinema 4D 2024.4.0/...
        #         50    0.000    0.000    0.000    0.000 {built-in method builtins.isinstance}
        #         50    0.000    0.000    0.000    0.000 {built-in method builtins.getattr}
        #         50    0.000    0.000    0.000    0.000 {method 'get' of 'dict' objects}
        #         1     0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
        # --------------------------------------------------------------------------------
        # TIMEIT: Ran 'iterative((<__main__.Processor object at 0x7fd18c0696a0>, 50), {}) -> -0.0' with 
        #     100002 function calls in 0.037 seconds
        #
        #    Ordered by: cumulative time
        #
        #     ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        #          1    0.025    0.025    0.037    0.037 scriptmanager:480(iterative)
        #      50000    0.007    0.000    0.007    0.000 {built-in method math.sin}
        #      50000    0.005    0.000    0.005    0.000 {built-in method math.sqrt}
        #          1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
    """
    def decorator(obj: T | typing.Type[typing.Any]) -> T | typing.Type[typing.Any]:
        if not enabled:
            return obj
        
        @functools.wraps(obj)
        def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            """Realizes a wrapper that measures the time a function or method takes to execute.
            """
            # Figure out the object which owns the call, either a function object or a class instance, and get the lookup
            # dictionary for the in-call protection mechanism.
            host: object = args[0] if inspect.ismethod(obj) else wrapper
            lookup: dict[str, bool] = getattr(host, ID_TIMEIT_LOOKUP, None)

            # If in-call protection is enabled, check if the function is already being called and if so, pass it through,
            # otherwise mark the function as being called. We store the flag over the function name as we would otherwise
            # mute all decorated methods of a class instance when one of them is being called.
            if (inCallProtection) and (lookup is not None) and (lookup.get(obj.__name__, False)):
                return obj(*args, **kwargs)

            if inCallProtection:
                lookup = {} if lookup is None else lookup
                lookup[obj.__name__] = True
            
            # Setup the measuring, call the function, unwind the measuring, and print the report.
            measure: float | cProfile.Profile = time.perf_counter() if not useProfiler else cProfile.Profile()
            if useProfiler:
                measure.enable()
  
            result: typing.Any = obj(*args, **kwargs)
            report: str
            if useProfiler:
                measure.disable()
                builder: io.StringIO = io.StringIO()
                pstats.Stats(measure, stream=builder).sort_stats("cumulative").print_stats()
                report = f"with {builder.getvalue().strip()}"
            else:
                report = f"in {round(time.perf_counter() - measure, showDigits)} sec"

            argStr: str = f"{args}, {kwargs}" if showArgs else ""
            resStr: str = f" -> {result}" if showResult else ""

            print(f"{'-' * 80}\nTIMEIT: Ran '{obj.__name__}({argStr}){resStr}' {report}")

            # Mark the call chain as finished.
            if inCallProtection:
                lookup[obj.__name__] = False
                setattr(host, ID_TIMEIT_LOOKUP, lookup)

            return result

        # Set the lookup dictionary for the in-call protection mechanism for (static) functions.
        if inCallProtection:
            setattr(wrapper, ID_TIMEIT_LOOKUP, {})

        return wrapper
    return decorator

def GetMemoryAddress(obj: Any) -> str:
    """Returns the native Python formatting memory address string for `#obj`.

    Can be useful when implementing the `__str__` or `__repr__` method of an object while wanting to
    maintain how Python naturally prints objects.

    :param obj: The object for which to get the memory address string.
    :type obj: any
    :return: The memory address string.
    :rtype: str

    :Example:

    .. code-block:: python

        import mxutils

        class Foo:
            def __init__(self, x: int) -> None:
                self.x = x

            def __str__(self) -> str:
                return (f"{self.__class__.__qualname__} (x={self.x}) "
                        f"object at {mxutils.GetMemoryAddress(self)}")
        
        f: Foo = Foo(42)
        print(f)

        # Output:
        
        # Foo (x=42) object at 0x00000139A3198540
    """
    return "0x" + f"{id(obj):016x}".upper()

def REPORT(character: str = "-", characterCount: int = 100, withOutput: bool = True) -> typing.Callable[[T], T]:
    """Decorates a function call by printing the function name, a horizontal bar below it, and an
    empty line after the function finished.

    Can be useful when debugging functions which print to the console.

    :param character: The character(s) out of which the bar is composed. Defaults to `-`.
    :type character: int, optional
    :param characterCount: How often `character` is repeated. Defaults to `100`.
    :type characterCount: int, optional

    :Example:

    .. code-block:: python

        import c4d
        import mxutils

        # We decorate a function with the default arguments.
        @mxutils.REPORT
        def foo(msg: str) -> None:
            return 42

        class Bar:
            # We decorate a method with a custom horizontal bar.
            @mxutils.REPORT("=", 50)
            def baz (self, msg: str) -> None:
                print(f"{msg = }")

        # Now we invoke the function and method.
        bar: Bar = Bar()

        foo("Hello World!")
        bar.baz("Bob's your uncle!")

        # Output:

        # Running 'foo':
        # ---------------------------------------------------------------------------------------...
        # res = 42
        #
        # Running 'Bar.baz (object at 0x0000020BEE9B57A0)':
        # ==================================================
        # msg = "Bob's your uncle!"
    """
    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> any:
            # inspect.ismethod won't work here, as the method is not yet called.
            isMethod: bool = len(args) > 0 and hasattr(args[0], '__class__') and hasattr(args[0], func.__name__) 
            name: str = (f"{args[0].__class__.__qualname__}.{func.__name__} (object at "
                         f"{GetMemoryAddress(args[0])})"
                         if isMethod else 
                         func.__name__)
            print(f"Running '{name}':\n{character * characterCount}")
            res: any = func(*args, **kwargs)
            if withOutput:
                print(f"Return : {res = }")
            return res
        
        return wrapper
    return decorator
