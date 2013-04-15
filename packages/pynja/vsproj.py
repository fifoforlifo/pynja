import os
import uuid
from . import io


def _def_config(variantName, ninjaDir, targetName):
    config = \
r'''        <Configuration
            Name="{0}|Win32"
            OutputDirectory="$(ConfigurationName)"
            IntermediateDirectory="$(ConfigurationName)"
            >
            <Tool
                Name="VCNMakeTool"
                BuildCommandLine="cd {1} &#x0D;&#x0A; ninja {2}"
                ReBuildCommandLine="cd {1} &#x0D;&#x0A; ninja -t clean {2} &#x0D;&#x0A; ninja {2}"
                CleanCommandLine="cd {1} &#x0D;&#x0A; ninja -t clean"
                Output=""
                PreprocessorDefinitions=""
                IncludeSearchPath=""
                ForcedIncludes=""
                AssemblySearchPath=""
                ForcedUsingAssemblies=""
                CompileAsManaged=""
            />
        </Configuration>
'''.format(variantName, ninjaDir, targetName)
    return config

def _def_files(sourceDir, relDir, strings):
    children = os.listdir(sourceDir)
    for child in children:
        if child == "__pycache__":
            continue
        path = os.path.join(sourceDir, child)
        relPath = os.path.join(relDir, child)
        if os.path.isdir(path):
            strings.append('        <Filter Name="%s">\n' % (child))
            _def_files(path, relPath, strings)
            strings.append('        </Filter>\n')
        else:
            strings.append('        <File RelativePath="%s" />\n' % (relPath))


def emit_vsproj_2008(projMan, projName, variants):
    firstProj = next(iter(variants.values()))
    vsProjPath = os.path.normpath(os.path.join(firstProj.builtDir, "..", projName + ".vcproj"))
    vsProjGuid = uuid.uuid5(uuid.NAMESPACE_DNS, projName)
    ninjaDir = os.path.dirname(projMan.ninjaPath)
    strings = []

    # create a sorted list of variantNames, so that the output is deterministic
    variantNames = []
    sortedVariants = []
    for variant in variants.keys():
        sortedVariants.append(variant)
        variantNames.append(variant.str)
    variantNames.sort()

    strings.append(r'''<?xml version="1.0" encoding="Windows-1252"?>
<VisualStudioProject
    ProjectType="Visual C++"
    Version="9.00"
    Name="%s"
    ProjectGUID="{%s}"
    Keyword="MakeFileProj"
    >
    <Platforms>
''' % (projName, vsProjGuid))

    strings.append(r'''        <Platform Name="%s" />%s''' % ("Win32", "\n"))

    strings.append(r'''    </Platforms>
    <ToolFiles>
    </ToolFiles>
    <Configurations>
''')

    for i, variantName in enumerate(variantNames):
        proj = variants[sortedVariants[i]]
        strings.append(_def_config(variantName, ninjaDir, proj.outputPath))
    strings.append(_def_config("all", ninjaDir, projName))

    strings.append(
r'''    </Configurations>
    <Files>
''')
    _def_files(proj.projectDir, ".\\", strings)
    strings.append(r'''    </Files>
</VisualStudioProject>
''')

    vsProjContents = "".join(strings)
    io.write_file_if_different(vsProjPath, vsProjContents)
    return (projName, vsProjGuid, vsProjPath)

def emit_vssln_2008(vsProjList, vsSlnPath, variantNames):
    strings = []
    strings.append("\nMicrosoft Visual Studio Solution File, Format Version 10.00\n")
    for vsProjInfo in vsProjList:
        (projName, vsProjGuid, vsProjPath) = vsProjInfo
        strings.append(r'''Project("{%s}") = "%s", "%s", "{1FB0236A-3B8A-4C00-92F7-9722DBFEA2DB}"%s'''
                       % (vsProjGuid, projName, vsProjPath, "\n"))
        strings.append("EndProject\n")
    strings.append(r'''Global
    GlobalSection(SolutionConfigurationPlatforms) = preSolution
''')
    for variantName in sorted(variantNames):
        strings.append("        %s = %s\n" % (variantName, variantName))

    strings.append(r'''    EndGlobalSection
    GlobalSection(SolutionProperties) = preSolution
        HideSolutionNode = FALSE
    EndGlobalSection
EndGlobal
''')

    vsSlnContents = "".join(strings)
    io.write_file_if_different(vsSlnPath, vsSlnContents)


def emit_vsproj_2010(proj):
    raise Exception("VS2010 projects not implemented yet")
