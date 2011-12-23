#!/bin/bash

# Quick hack to rewrite an existing Git repository after a licensing decission
# was made
#
# The script adds a COPYING file in the root of every revision, and adds a
# license header to all OCaml and C source files.
# This assumes files had no existing license header, otherwise it would be
# duplicated.
#
# It's a quick hack which (in a slightly modified version) did the job for
# Baardskeerder, YMMV. There are most likely more
# flexible/complex/foolproof/useful scripts available on the web.
#
# Execution
# =========
# For safety reasons, always perform these actions in a new clone of the
# existing repository (better safe than sorry).
#
# Make sure to alter the script according to your needs (you'll at least need to
# change the value of 'BASE').
#
# To rewrite every commit in a tree, execute the following command:
#
# $ git filter-branch --tree-filter "bash /path/to/fix_licenses.sh" HEAD
#
# Assuming you were in the 'master' branch, the 'master' ref will now point to a
# completely different tree and history. You'll need to use 'git push -f' to be
# able to publish the tree, make sure you know the implications of this action,
# and it's OK to do so.
#
# In case things go wrong, the original ref is backed up as
# original/refs/heads/master (or something alike, depending on your branchname).
# You can use this ref to fix your repository in case something goes terribly
# wrong. You'll need to remove this ref to be able to run the tree rewriting
# again afterwards.
#
# More info: git filter-branch --help

BASE=/path/to/files

# Add COPYING to the root of every tree
cp $BASE/lgpl-3.0.txt COPYING
git add COPYING

for f in `find src | grep '\.mli*$'`; do
    mv $f $f.old
    cat $BASE/header-ml.txt > $f
    cat $f.old >> $f
    rm $f.old
done

for f in `find src | grep '\.[ch]$'`; do
    mv $f $f.old
    cat $BASE/header-c.txt > $f
    cat $f.old >> $f
    rm $f.old
done
