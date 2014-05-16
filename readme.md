# pynja

(c) Avinash Baliga / 2013

pynja is a cross-platform meta-build system written in Python that produces
[Ninja Build files](http://martine.github.com/ninja/).

You can find
[the manual here](http://fifoforlifo.github.io/pynja/).

## Overview

### Variant-Based Builds

With pynja, you define a python class for each library or program you want to build.
Then instantiate that class for each *variant* you wish to build in order to define real file targets.
-   Need to vary your library builds over multiple compiler toolchains and architectures?  Make that part of your variant.
-   Need to vary your library builds over the C runtime linkage?  Make that part of your variant.
-   Want multiple debug/develop/profile/release/etc. configurations?  Make that part of the variant.

You get the idea.

An example of a variant string is `windows-msvc11-x86-dbg-dcrt`.  pynja converts that string into
an object that you can use to make decisions, such as which compiler flags to use.  You define the
variant types, and may define multiple variant types to use within one build.

All of your targets across all variants will be instanced in one huge build graph.  This makes it
easy to reference all your multi-arch components in your 'install' rules or unit-tests.

### Cross-Plat C++ Compilation

So far, the supported C++ toolchains are `gcc`, `msvc`, `clang`, `nvcc`.

There are built in abstractions for C/C++ compilation.  Each common compiler option is represented as a
class field, which can be overridden at multiple stages.
-   Set global compile flags on a per-variant basis in common code.
-   Override per-project flags at the project level.
-   Override per-file (or file-list) flags.
-   Define or call helper functions at any stage.

And all without messing with monolithic CFLAGS strings.

Multiple C++ toolchains can be used in a single build.  Simply point the toolchain objects
at the right installation path, and the build will figure out how to invoke the compiler correctly.
No need to tweak your environment (variables) externally to the build.

Precompiled Headers (PCH) are fully supported on all toolchains.  More than one PCH per project
is fully supported.  PCH chaining (creating one PCH from another) also works.

### Other Stuff

Everything is written in regular Python, and you can call any Python code from your own build scripts.
Python has terrific editing and debugging tools, which means with pynja you can actually develop
and debug your build like the rest of your software.

It's easy to add support for other tools and languages.  For example, there's support for
Java and Protobuf generation.

pynja can generate Visual Studio projects for code browsing.


## Simple example

```python
# a0.py
import pynja
import repo

@pynja.project
class a0(repo.cpp.CppProject):
    def emit(proj):
        sources = [a0_one.cpp a0_two.cpp]
        proj.cpp_compile(sources)

        proj.make_static_lib("a0")

# prog.py
import os
import pynja
import repo

@pynja.project
class prog(repo.cpp.CppProject):
    def emit(proj):
        sources = [prog_one.cpp prog_two.cpp]

        # add link-time dependency
        libA0 = self.add_cpplib_dependency('a0', 'sta')

        self.includePaths.append(os.path.join(repo.rootPaths.a0, "include"))

        with self.cpp_compile_ex(sources) as tasks:
            for task in tasks:
                task.includePaths.append(os.path.join(libA0.builtDir, "generated"))

        self.make_executable("prog")
```
