#
# Completions for the qdk2 command
#

#
# Functions
#

function __fish_qdk2_using_command
  set cmd (commandline -opc)
  if [ (count $cmd) -gt 1 ]
    if [ $argv[1] = $cmd[2] ]
      return 0
    end
  end
  return 1
end

# All qdk2 commands
complete -c qdk2 -n '__fish_use_subcommand' -xa import --description "Create a new QPKG from the various source"
complete -c qdk2 -n '__fish_use_subcommand' -xa create --description "Create a new QPKG from the template"
complete -c qdk2 -n '__fish_use_subcommand' -xa build --description "Build a QPKG from a folder"
complete -c qdk2 -n '__fish_use_subcommand' -xa changelog --description "Tool for maintenance of the QNAP/changelog file in a source package"
complete -c qdk2 -n '__fish_use_subcommand' -xa extract --description "Extract QNAP App (.qpkg) or firmware image (.img)"
complete -c qdk2 -n '__fish_use_subcommand' -xa doctor --description "Check your system for problems"
complete -c qdk2 -n '__fish_use_subcommand' -xa version --description "Show the QDK2 version information"

#
# qdk2 import
#

#
# qdk2 create
#

#
# qdk2 build
#

#
# qdk2 changelog
#

#
# qdk2 extract
#

#
# qdk2 version
#
