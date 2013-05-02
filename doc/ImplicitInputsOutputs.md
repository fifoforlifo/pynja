# Implicit Inputs and Outputs in a DAG-Based Build

(c) Avinash Baliga - 2013/May/01

This document describes how a DAG-based build system can handle implicit outputs,
and how to implement this when using the ninja build system.


## The Problem

In any build system, we can categorize the input and output files of each command as follows:

1.  Explicit inputs: Known a priori.  For example, a C source file.
2.  Explicit outputs: Known a prior.  For example, an object file.
3.  Implicit inputs: Only knownable once the command is executable.  For example, C header files.
4.  Implicit outputs: Only knowable once the command is executable.  For example, the list of files produced after unzipping a file.

A DAG-based build system can handle explicit inputs and outputs naturally.

Implicit inputs usually require some special support or trickery.  This usually suffices for ensuring that
a single command's outputs stay up-to-date on incremental builds.  However, manual dependency
annotations are usually required whenever an implicit input is generated as part of the build.

Implicit outputs are a different beast.  A normal build DAG requires all outputs to be declared
in advance, prevent implicit outputs from being directly representable.  A 'representative explicit output'
or 'guard file' is often used as a place-holder for implicit outputs, and manual dependency
annotations are required for all consumers.  The guard file correctly sequences dependencies, but
it has one drawback: if any implicit output file is erased, but the guard file remains, then an incremental
build is unable to detect it -- leaving the build in an invalid state.


## Fixing Implicit Outputs in Incremental Builds

### Implicit Input/Output Duality

Assuming the list of implicit outputs is knowable upon executing a command, it's possible
to create a DAG construct that perfectly updates on incremental builds.  The key is to create
two commands: a 'clean' command and an 'incremental' command.

Example pseudo-code:

    # define a command function
    def unzip_command():
        system("unzip foo.zip -d out > tempfile")
        convert_unzip_output_to_file_list("tempfile", "foo.zip.list")
        unlink("tempfile")

    # clean unzip
    build:
        inputs  = foo.zip
        outputs = foo.zip.list
        command_script:
            unzip_command()

    # incremental unzip
    build:
        inputs  = foo.zip.list
        depfile = foo.zip.d
        outputs = foo.zip.fanin
        command_script:
            if not all_deps_exist("foo.zip.list"):
                unzip_command()
            create_dep_file("foo.zip.fanin", "foo.zip.list") > foo.zip.d
            touch foo.zip.fanin

    # dependent build command
    build:
        inputs  = foo.zip.fanin
        outputs = out/test.log
        command_script:
            chdir("out")
            system("test ./stuff > test.log")


What does this do when building all?
-   On a clean build:
    -   foo.zip.list is out-of-date
        -   invoke unzip_command()
            -   in this example, "out/stuff" is created
        -   foo.zip.list now contains names of all files that were unzipped
    -   foo.zip.fanin is out-of-date
        -   all deps exist, so skip re-running the unzip_command_script()
        -   convert the implicit-output list file to a deps file
        -   foo.zip.fanin is created
    -   test.log is out-of-date
        -   execute the test executable
        -   out/test.log is produced
-   Without touching the file-system, perform incremental build:
    -   all files remain up-to-date
-   Delete "out/stuff", perform incremental build.
    -   foo.zip.list is newer than foo.zip; skip it
    -   foo.zip.fanin is newer than foo.zip.list; HOWEVER -- the deps file
        states that foo.zip.fanin depends on "out/stuff".  Since "out/stuff"
        doesn't exist, the command is invoked.
        -   all deps do NOT exist, so invoke unzip_command()
            -   "out/stuff" is re-created
        -   deps file re-created
        -   foo.zip.fanin re-created
    -   test.log is out-of-date; re-run the test
-   Without touching the file-system, perform incremental build:
    -   foo.zip.list is newer than foo.zip; skip it
    -   foo.zip.fanin is newer than foo.zip.list and "out/stuff"; skip it
    -   out/test.log is newer than foo.zip.fanin; skip it
    =>  all files remain up-to-date

Notice when "out/stuff" was deleted, the 'incremental build command' made sure to
perform all build steps in the same exact order as they would occur in a clean build.

Another requirement for this technique to work, is that a build command must be invoked
even if only implicit inputs are missing.  This is a policy that a build engine need not
support, but fortunately ninja does support it.

In pynja, java compilation is kept up-to-date using this construct.


### Possibility for 'native' ninja support.

Ninja could support the above construct natively in a generic way, saving build generators
from having to write the commands and scripts from replicating this.

The required changes to ninja would be:
-   A rule would support additional special keys, such as:
    -   impout_list : the 'list' file for the clean node
    -   fanin_file  : the 'fanin' file for the incremental node
-   ninja would automatically create two build nodes for a build command whose
    rule specified the implicit-output special keys.
-   ninja would implement the generic logic in the 'incremental' node.


## Implicit Inputs without manual annotations

Can be done if:
(a) A failed command outputs a deps file.
(b) The build engine re-adjusts the dependency graph based on the failed command's deps file.
    -   If a newly discovered dependency needs to be generated by some other command,
        then that other command will (eventually) be enqueued to execute first.
    -   Otherwise, it's a build error, because there's no way to create the missing file.
(c) When the newly discovered dependencies are resolved, the failed command will be retried.

For a graph of N commands, the runtime remains O(N) and the worst case performance is O(2*N).

The benefit is that the build scripts (or meta-build scripts) are much more human-maintainable.
There is no longer a burden on build script authors to understand cross-module dependencies
for things like generated headers; the build figures it out for you.

The retry penalty will also tend to affect the performance of incremental builds less, since
full dependency information is available.


For reference, here's an old blog post of mine that explains some more details.  The post refers
to an old toy build system I wrote called QRBuild, where this idea was put into practice.

http://qrbuild.blogspot.com/2011/05/types-of-inputs-and-outputs-explicit.html

