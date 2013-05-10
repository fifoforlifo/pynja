# pynja

(c) Avinash Baliga / 2013

pynja is a cross-platform meta-build system written in Python that produces [Ninja Build files](http://martine.github.com/ninja/).

## Overview

With pynja, you get to define a python class for each library or program you want to build.
Then instantiate that class for each *variant* you wish to build in order to define real file targets.
-   Need to vary your library builds over multiple compiler toolchains and architectures?  Make that part of your variant.
-   Need to vary your library builds over the C runtime linkage?  Make that part of your variant.
-   Want multiple debug/develop/profile/release/etc. configurations?  Make that part of the variant.
You get the idea.

All of your target variants will be instanced in one huge build graph.  This makes it easy to reference
all your multi-arch components in your 'install' rules or unit-tests.

There are built in abstractions for C/C++ compilation.  Every common compiler option is represented as a
class field, which can be overridden at multiple stages.
-   Set global compile flags on a per-variant basis in common code.
-   Then override per-project flags at the project level.
-   And finally, override per-file (or file-list) flags.
And all this is possible without messing with CFLAGS strings, or doing string or regex replacement.

Everything is written in regular Python, and you can run any Python code from your own build scripts.
Python also has terrific editing and debugging tools, which means with pynja you can actually develop
and debug your build like the rest of your software.

It's also easy to add support for other tools and languages.  For example, there's rudimentary support for
Java and Protobuf generation.

Pynja also generates Visual Studio projects for code browsing and convenience.


## The Manual

It's a work-in-progress, located [here](https://github.com/fifoforlifo/pynja/tree/master/doc/manual).

## Simple example

```python
# liba0.py
import pynja
import repo

@pynja.project
class a0(repo.cpp.CppProject):
    def emit(self):
        sources = [a0_one.cpp a0_two.cpp]
        with self.cpp_compile(sources) as tasks: pass
        with self.make_static_lib("a0") as task: pass

# prog.py
import os
import pynja
import repo

@pynja.project
class a0(repo.cpp.CppProject):
    def emit(self):
        sources = [prog_one.cpp prog_two.cpp]

        a0 = self.projectMan.get_project('a0', self.variant)

        with self.cpp_compile(sources) as tasks:
            for task in tasks:
                task.includePaths.append(os.path.join(a0.projectDir, "include"))
        self.add_input_lib(libA0.libraryPath)
        with self.make_executable("prog") as task: pass
```


## Why another build system?

Because the ones out there are *still* not good enough!

