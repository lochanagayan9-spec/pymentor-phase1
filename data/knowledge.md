# PyMentor Knowledge Base: Core Python Code Understanding & Diagnostics

## Domain Scope Overview
This knowledge base defines the authoritative domain knowledge for PyMentor.
PyMentor is strictly restricted to the domain of Python code understanding, syntax, standard library, execution mechanics, error diagnosis, and idiomatic practices (PEP 8).

---

## Section 1: Python Data Model, Memory & Object Identity

### 1.1 Objects and Name Binding
In Python, variables are not memory containers that hold values; they are names bound to objects.
- Assignment (a = [1, 2, 3]) binds the name a to a list object in the heap.
- Multiple names can bind to the same object: b = a. Both a and b reference the identical object.
- Every object in Python has three fundamental traits:
  1. Identity: The object's memory address, obtained with id(obj). Cannot change once created.
  2. Type: What kinds of values the object can hold and what operations it supports (type(obj)). Cannot change once created.
  3. Value: The data stored in the object. May be mutable or immutable.

### 1.2 Equality (==) vs Identity (is)
- a == b: Calls a.__eq__(b). Evaluates whether two objects have equal values/contents.
- a is b: Compares id(a) == id(b). Evaluates whether both references point to the exact same physical memory location.
- Rule: Always use is when comparing to singletons like None, True, or False (e.g., if val is None:). Never use is to compare numbers or strings, because small integer caching (-5 to 256) and string interning are CPython implementation details and not guaranteed language semantics.

### 1.3 Mutability vs Immutability
- Immutable Types: int, float, complex, bool, str, tuple, frozenset, bytes.
  - Once allocated, their contents cannot be modified in place.
  - Operations like s = s + ' extra' allocate an entirely new string object and rebind the variable s.
- Mutable Types: list, dict, set, bytearray.
  - In-place modifications (e.g., list.append(), dict.update()) alter the existing object without changing its identity (id()).
  - If multiple variables reference the same mutable object, mutations through one variable are visible through all of them.

### 1.4 Shallow vs Deep Copy
- Shallow Copy (copy.copy(x) or x.copy() or list(x)):
  - Constructs a new compound object and inserts references to the objects found in the original.
  - Nested mutable objects are NOT duplicated; changes to nested elements affect both copies.
- Deep Copy (copy.deepcopy(x)):
  - Constructs a new compound object and recursively inserts copies of the objects found in the original.

---

## Section 2: Core Data Structures & Time Complexities

### 2.1 Lists (list)
- Implemented in CPython as contiguous dynamic arrays of object pointers.
- Index lookup lst[i]: O(1)
- Append lst.append(x): O(1) amortized
- Pop from end lst.pop(): O(1)
- Insert/delete at beginning lst.insert(0, x) or lst.pop(0): O(n) because all subsequent pointers must be shifted.
- In-place sorting lst.sort(): Uses Timsort, O(n log n) worst-case time, stable.

### 2.2 Tuples (tuple)
- Immutable sequences. Once created, length and item pointers are fixed.
- Hashable if and only if all contained elements are also hashable.
- Memory efficient: smaller memory overhead than lists due to absence of dynamic resizing buffers.

### 2.3 Dictionaries (dict)
- Implemented as hash tables. In Python 3.6+, dictionaries preserve insertion order.
- Average time complexity: O(1) for lookup (d[key]), insertion (d[key] = val), and deletion (del d[key]).
- Worst-case time complexity: O(n) during rare hash collisions.
- Requirement for keys: Must be hashable (must implement __hash__() and __eq__(), and the hash value must never change during the object's lifetime). Lists, sets, and unhashable dicts cannot be keys.

### 2.4 Sets (set)
- Implemented as hash tables containing only keys without values.
- Average time complexity: O(1) for membership testing (x in my_set), addition (my_set.add(x)), and removal (my_set.remove(x)).
- Set operations: Union s1 | s2, Intersection s1 & s2, Difference s1 - s2, Symmetric Difference s1 ^ s2.

### 2.5 Standard Library Collections (collections)
- deque: Doubly linked list of blocks; provides O(1) appends and pops from both left and right (appendleft, popleft).
- defaultdict: Subclass of dict that invokes a factory function when a missing key is accessed, avoiding KeyError.
- Counter: Dict subclass for counting hashable objects.
- OrderedDict: Explicit ordered dictionary (retains utility for reordering operations like move_to_end).

---

## Section 3: Scope Resolution, Functions & Closures

### 3.1 LEGB Scope Resolution Rule
When a variable name is referenced, Python searches four scopes sequentially:
1. L (Local): Names defined within the current executing function or lambda.
2. E (Enclosing): Names defined in the local scope of any enclosing/outer functions (from inner to outer).
3. G (Global): Names defined at the top level of the current module or declared global.
4. B (Built-in): Names built into Python (len, range, print, int, etc.).
If not found in any of these four, Python raises a NameError.

### 3.2 Modifying Outer Scopes: global and nonlocal
- Simply assigning x = 10 inside a function creates a Local variable x, shadowing any outer x.
- global x: Informs Python that references and assignments to x bind to the module-level global x.
- nonlocal x: Informs Python that assignments to x bind to the nearest enclosing (non-global) function scope.

### 3.3 Closures
A closure occurs when an inner function retains access to variables in its enclosing scope even after the outer function has completed execution.
Example:
def make_multiplier(factor):
    def multiplier(number):
        return number * factor
    return multiplier

double = make_multiplier(2)
print(double(5))  # Output: 10

### 3.4 Decorators
A decorator is a callable that takes another function as input and returns a replacement callable.
- The @decorator syntax is syntactic sugar for func = decorator(func).
- Always use functools.wraps(func) on the inner wrapper to preserve the original function's __name__, __doc__, and signature.

---

## Section 4: Generators, Iterators & Memory Mechanics

### 4.1 The Iterator Protocol
- Iterable: An object defining __iter__() which returns an iterator (e.g. list, dict, str).
- Iterator: An object defining __next__() (returns next item or raises StopIteration) and __iter__() (returns self).
- The for item in iterable loop calls iter(iterable), then calls next() repeatedly until StopIteration is raised.

### 4.2 Generators and Lazy Evaluation
- Any function containing the yield statement is a generator function.
- When called, it does not execute the body immediately; it returns a generator iterator object.
- Each call to next() executes code until the next yield statement, yielding the value and freezing execution state.
- Memory advantage: Enables streaming gigabytes of data with O(1) memory footprint rather than allocating entire collections in RAM.

---

## Section 5: Object-Oriented Python & Dunder Methods

### 5.1 Object Lifecycle: __new__ vs __init__
- __new__(cls, *args, **kwargs): Static method responsible for allocating and returning a new instance of cls. Rarely overridden except in singletons, immutable subclasses (like subclassing int or tuple), or metaclasses.
- __init__(self, *args, **kwargs): Instance method responsible for initializing the freshly created object. Returns None.

### 5.2 Representation: __repr__ vs __str__
- __repr__(self): Goal is to be unambiguous, detailed, and if possible, match valid Python code that could recreate the object (e.g., Point(x=1, y=2)). Used by debuggers and REPL.
- __str__(self): Goal is to be readable and human-friendly (e.g., 'Point at (1, 2)'). Used by print() and str(). If __str__ is not defined, Python falls back to __repr__.

### 5.3 Method Resolution Order (MRO) & super()
- Python uses C3 Linearization to resolve attribute and method lookups in multiple inheritance.
- Inspect an object's MRO using ClassName.__mro__ or ClassName.mro().
- super() does not simply call the immediate parent; it calls the next class in the MRO chain, ensuring cooperative multiple inheritance without diamond problem bugs.

### 5.4 Data Classes (@dataclass)
Introduced in Python 3.7 (from dataclasses import dataclass). Automatically generates boilerplate methods: __init__, __repr__, __eq__, and optionally __lt__, __hash__ (via frozen=True).

---

## Section 6: Context Managers & Resource Management

### 6.1 The Context Manager Protocol
Guarantees cleanup of external resources (file descriptors, sockets, database transactions, locks) even if unhandled exceptions occur.
- Requires two dunder methods:
  - __enter__(self): Runs before entering the block; return value binds to the as <var> clause.
  - __exit__(self, exc_type, exc_val, exc_tb): Runs after exiting the block. If it returns True, it suppresses any raised exception; returning False or None propagates the exception.

### 6.2 contextlib.contextmanager
Allows creating context managers using a generator with a single yield enclosed in a try...finally block.

---

## Section 7: Error Diagnosis & Exception Hierarchy

### 7.1 Python Exception Hierarchy
BaseException
├── SystemExit
├── KeyboardInterrupt
└── Exception  <-- Catch this for regular application errors!
    ├── ArithmeticError (ZeroDivisionError, OverflowError)
    ├── LookupError (IndexError, KeyError)
    ├── AttributeError
    ├── TypeError
    ├── ValueError
    ├── NameError (UnboundLocalError)
    └── OSError (FileNotFoundError, PermissionError)

- Rule: Never do bare except: or except BaseException:, because it intercepts KeyboardInterrupt (Ctrl+C) and SystemExit. Always catch except Exception: or specific subclasses.

### 7.2 Diagnosing Common Tracebacks
- TypeError: Occurs when an operation or function is applied to an object of inappropriate type (e.g. '2' + 2), or wrong number of arguments passed.
- IndexError: Attempting to access a sequence with an integer index outside [-len, len - 1].
- KeyError: Attempting to access a dictionary key that does not exist. (Fix: use dict.get(key, default) or defaultdict).
- AttributeError: Attempting to access a nonexistent attribute or method on an object (often caused by a variable unexpectedly being None).
- UnboundLocalError: A local variable is read before it has been assigned within that function. Caused by assigning to a variable anywhere in the function, which marks it local for the whole scope.

---

## Section 8: Classic Python Traps & Gotchas

### Trap 1: The Mutable Default Argument Bug
Problematic Code:
def add_item(item, basket=[]):
    basket.append(item)
    return basket

Why it happens: Default parameter values are evaluated once, when the function definition is executed at module load time, NOT each time the function is called. The identical list object is reused across all calls.
Correct Idiom:
def add_item(item, basket=None):
    if basket is None:
        basket = []
    basket.append(item)
    return basket

### Trap 2: Late Binding in Closures
Problematic Code:
multipliers = [lambda x: x * i for i in range(4)]
[m(2) for m in multipliers]  # Output: [6, 6, 6, 6], NOT [0, 2, 4, 6]!

Why it happens: Python closures look up variables by reference when the inner function is executed, not when it is created. When m(2) runs, the loop has already finished and i is 3.
Correct Idiom: Bind i at definition time using a default argument:
multipliers = [lambda x, i=i: x * i for i in range(4)]

### Trap 3: Modifying a Collection While Iterating
Problematic Code:
numbers = [1, 2, 3, 4, 5]
for n in numbers:
    if n % 2 == 0:
        numbers.remove(n)  # Skips elements because indices shift dynamically!

Correct Idiom: Create a new filtered list using a comprehension:
numbers = [n for n in numbers if n % 2 != 0]
