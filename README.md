# benchpress

## Configurations
The base of a configuration is a directory. The name of the directory is also used as an identifier.
Within a directory live items. Items are basically targets, which can be built in different flavors.
The flavors can be indicated in two different ways. The first way is a globally specified "glob-flavor".
The glob-flavor is applied to every item in every directory. This serves the purpose of, e.g., building baseline
versions for all applications.
If a prefix is given for the items, then it is assumed that every item lives within its only sub-directory
of the form '''prefix_item'''. As such, the builder will descent into the sub directory and run the build command
there.

item = i
prefix = p
flavor = f