import os
import uuid
from . import io
from . import cpp


def _is_source_file(filename):
    return filename.endswith(".c") or filename.endswith(".cpp") or filename.endswith(".cxx")


class VS2008:

    def _def_config(variantName, ninjaDir, targetName, proj):
        defines = ""
        includePaths = ""
        forceIncludes = ""
        if proj:
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


    def _emit_vcproj(projectMan, projName, variants):
        firstProj = next(iter(variants.values()))
        vsProjPath = os.path.normpath(os.path.join(firstProj.builtDir, "..", projName + ".vcproj"))
        vsProjGuid = uuid.uuid5(uuid.NAMESPACE_DNS, projName)
        ninjaDir = os.path.dirname(projectMan.ninjaPath)
        strings = []

        # create a sorted list of variants by name, so that the output is deterministic
        sortedVariants = sorted(variants.keys(), key = lambda variant: variant.str)

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

        for variant in sortedVariants:
            proj = variants[variant]
            strings.append(VS2008._def_config(variant.str, ninjaDir, proj.outputPath, proj))
        strings.append(VS2008._def_config("all", ninjaDir, projName, None))

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


    def _emit_sln(vsProjList, vsSlnPath, variantNames):
        strings = []
        strings.append("\nMicrosoft Visual Studio Solution File, Format Version 10.00\n")
        for vsProjInfo in vsProjList:
            (projName, vsProjGuid, vsProjPath) = vsProjInfo
            strings.append(r'''Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "%s", "%s", "{%s}"%s'''
                           % (projName, vsProjPath, vsProjGuid, "\n"))
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

    def emit_vs_projects(projectMan):
        """Extension method of ProjectMan, to write out VS projects"""
        vsProjList = []
        variantNames = set()
        for projName in sorted(projectMan._projects.keys()):
            variants = projectMan._projects[projName]
            for variant in variants:
                variantNames.add(variant.str)

            vsProjInfo = VS2008._emit_vcproj(projectMan, projName, variants)
            vsProjList.append(vsProjInfo)
        VS2008._emit_sln(vsProjList, os.path.join(os.path.dirname(projectMan.ninjaPath), "vs2008.sln"), variantNames)


class VS2010:

    def _def_project_configuration(strings, variantName):
        strings.append('    <ProjectConfiguration Include="%s|Win32">\n' % (variantName))
        strings.append('      <Configuration>%s</Configuration>\n' % (variantName))
        strings.append('      <Platform>Win32</Platform>\n')
        strings.append('    </ProjectConfiguration>\n')

    def _def_config_props(variantName, ninjaDir, targetName, proj):
        defines = ""
        includePaths = ""
        forceIncludes = ""
        if proj:
            task = cpp.CppTask(proj, "dummy", "dummy.o", proj.projectDir)
            proj.set_cpp_compile_options(task)
            defines = ";".join(task.defines)
            includePaths = ";".join(task.includePaths)
            forceIncludes = task.usePCH if task.usePCH else ""
        config = \
r'''  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='{0}|Win32'">
    <NMakeOutput>o</NMakeOutput>
    <NMakeBuildCommandLine>SET VS_UNICODE_OUTPUT=
SET NINJA_STATUS=[%%s/%%t - %%e]
cd {1}
ninja {2}
</NMakeBuildCommandLine>
    <NMakeCleanCommandLine>SET VS_UNICODE_OUTPUT=
SET NINJA_STATUS=[%%s/%%t - %%e]
cd {1}
ninja -t clean {2}
</NMakeCleanCommandLine>
    <NMakeReBuildCommandLine>SET VS_UNICODE_OUTPUT=
SET NINJA_STATUS=[%%s/%%t - %%e]
cd {1}
ninja -t clean {2}
ninja {2}
</NMakeReBuildCommandLine>
    <NMakePreprocessorDefinitions>{3}</NMakePreprocessorDefinitions>
    <NMakeIncludeSearchPath>{4}</NMakeIncludeSearchPath>
    <NMakeForcedIncludes>{5}</NMakeForcedIncludes>
  </PropertyGroup>
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
                VS2010._def_files(path, relPath, strings)
            else:
                if _is_source_file(child):
                    strings.append('    <ClCompile Include="%s" />\n' % (path))
                else:
                    strings.append('    <ClInclude Include="%s" />\n' % (path))

    def _emit_vcxproj(projectMan, projName, variants):
        firstProj = next(iter(variants.values()))
        vsProjPath = os.path.normpath(os.path.join(firstProj.builtDir, "..", projName + ".vcxproj"))
        vsProjGuid = uuid.uuid5(uuid.NAMESPACE_DNS, projName)
        ninjaDir = os.path.dirname(projectMan.ninjaPath)
        strings = []

        # create a sorted list of variants by name, so that the output is deterministic
        sortedVariants = sorted(variants.keys(), key = lambda variant: variant.str)

        strings.append(r'''<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" ToolsVersion="4.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup Label="ProjectConfigurations">
''')
        for variant in sortedVariants:
            VS2010._def_project_configuration(strings, variant.str)
        VS2010._def_project_configuration(strings, "all")
        strings.append(
r'''  </ItemGroup>
  <PropertyGroup Label="Globals">
    <ProjectGuid>{%s}</ProjectGuid>
    <Keyword>MakeFileProj</Keyword>
    <ConfigurationType>Makefile</ConfigurationType>
    <PlatformToolset>v110</PlatformToolset>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />
''' % (vsProjGuid))

        for variant in sortedVariants:
            proj = variants[variant]
            strings.append(VS2010._def_config_props(variant.str, ninjaDir, proj.outputPath, proj))

        strings.append('  <ItemGroup>\n')
        VS2010._def_files(proj.projectDir, ".\\", strings)
        strings.append('  </ItemGroup>\n')
        strings.append('  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />\n')
        strings.append('</Project>\n')

        vsProjContents = "".join(strings)
        io.write_file_if_different(vsProjPath, vsProjContents)
        return (projName, vsProjGuid, vsProjPath)


    def _emit_sln(vsProjList, vsSlnPath, variantNames):
        strings = []
        strings.append("\nMicrosoft Visual Studio Solution File, Format Version 11.00\n")
        for vsProjInfo in vsProjList:
            (projName, vsProjGuid, vsProjPath) = vsProjInfo
            strings.append(r'''Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "%s", "%s", "{%s}"%s'''
                           % (projName, vsProjPath, vsProjGuid, "\n"))
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

    def emit_vs_projects(projectMan):
        """Extension method of ProjectMan, to write out VS projects"""
        vsProjList = []
        variantNames = set()
        for projName in sorted(projectMan._projects.keys()):
            variants = projectMan._projects[projName]
            for variant in variants:
                variantNames.add(variant.str)

            vsProjInfo = VS2010._emit_vcxproj(projectMan, projName, variants)
            vsProjList.append(vsProjInfo)
        VS2010._emit_sln(vsProjList, os.path.join(os.path.dirname(projectMan.ninjaPath), "vs2010.sln"), variantNames)
