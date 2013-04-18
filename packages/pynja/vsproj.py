import os
import uuid
from . import io
from . import cpp


class VS2008:

    def _def_config(variantName, ninjaDir, targetName, proj):
        task = cpp.CppTask(proj, "dummy", "dummy.o", proj.projectDir)
        proj.set_cpp_compile_options(task)
        defines = ";".join(task.defines)
        includePaths = ";".join(task.includePaths)
        forceIncludes = task.usePCH if task.usePCH else ""
        config = \
r'''        <Configuration
            Name="{0}|Win32"
            OutputDirectory="$(ConfigurationName)"
            IntermediateDirectory="$(ConfigurationName)"
            ConfigurationType="0"
            >
            <Tool
                Name="VCNMakeTool"
                BuildCommandLine="SET VS_UNICODE_OUTPUT= &#x0D;&#x0A; SET NINJA_STATUS=[%%s/%%t - %%e] &#x0D;&#x0A; cd {1} &#x0D;&#x0A; ninja {2}"
                ReBuildCommandLine="SET VS_UNICODE_OUTPUT= &#x0D;&#x0A; SET NINJA_STATUS=[%%s/%t - %%e] &#x0D;&#x0A; cd {1} &#x0D;&#x0A; ninja -t clean {2} &#x0D;&#x0A; ninja {2}"
                CleanCommandLine="SET VS_UNICODE_OUTPUT= &#x0D;&#x0A; SET NINJA_STATUS=[%%s/%%t - %%e] &#x0D;&#x0A; cd {1} &#x0D;&#x0A; ninja -t clean"
                Output=""
                PreprocessorDefinitions="{3}"
                IncludeSearchPath="{4}"
                ForcedIncludes="{5}"
                AssemblySearchPath=""
                ForcedUsingAssemblies=""
                CompileAsManaged=""
            />
        </Configuration>
'''.format(variantName, ninjaDir, targetName, defines, includePaths, forceIncludes)
        return config

    def _def_files(sourceDir, relDir, strings):
        children = os.listdir(sourceDir)
        children.sort()
        for child in children:
            if child == "__pycache__":
                continue
            path = os.path.join(sourceDir, child)
            relPath = os.path.join(relDir, child)
            if os.path.isdir(path):
                strings.append('        <Filter Name="%s">\n' % (child))
                VS2008._def_files(path, relPath, strings)
                strings.append('        </Filter>\n')
            else:
                strings.append('        <File RelativePath="%s" />\n' % (path))


    def emit_vcproj(projectMan, projName, variants):
        firstProj = next(iter(variants.values()))
        vsProjPath = os.path.normpath(os.path.join(firstProj.builtDir, "..", projName + ".vcproj"))
        vsProjGuid = uuid.uuid5(uuid.NAMESPACE_DNS, projName)
        ninjaDir = os.path.dirname(projectMan.ninjaPath)
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
    TargetFrameworkVersion="196613" >
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
            strings.append(VS2008._def_config(variantName, ninjaDir, proj.outputPath, proj))
        strings.append(VS2008._def_config("all", ninjaDir, projName, firstProj))

        strings.append(
r'''    </Configurations>
    <Files>
''')
        VS2008._def_files(proj.projectDir, ".\\", strings)
        strings.append(r'''    </Files>
</VisualStudioProject>
''')

        vsProjContents = "".join(strings)
        io.write_file_if_different(vsProjPath, vsProjContents)
        return (projName, vsProjGuid, vsProjPath)


    def emit_sln(vsProjList, vsSlnPath, variantNames):
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
        strings.append("        %s = %s\n" % ("all", "all"))

        strings.append(r'''    EndGlobalSection
    GlobalSection(SolutionProperties) = preSolution
        HideSolutionNode = FALSE
    EndGlobalSection
EndGlobal
''')

        vsSlnContents = "".join(strings)
        io.write_file_if_different(vsSlnPath, vsSlnContents)


def _emit_vsproj_2010(proj):
    raise Exception("VS2010 projects not implemented yet")



def emit_vs_projects(projectMan):
    """Extension method of ProjectMan, to write out VS projects"""
    if projectMan.emitVS2008Projects:
        vsProjList = []
        variantNames = set()
        for projName in sorted(projectMan._projects.keys()):
            variants = projectMan._projects[projName]
            for variant in variants:
                variantNames.add(variant.str)

            vsProjInfo = VS2008.emit_vcproj(projectMan, projName, variants)
            vsProjList.append(vsProjInfo)
        VS2008.emit_sln(vsProjList, os.path.join(os.path.dirname(projectMan.ninjaPath), "vs2008.sln"), variantNames)

