#!/bin/sh

# Script to automatically generate documentation and commit this to the gh-pages
# branch.

DOCBRANCH=gh-pages
UPSTREAM=$(git config branch.$DOCBRANCH.remote)
UPSTREAM_BRANCH=$(git rev-parse --symbolic-full-name --abbrev-ref $DOCBRANCH@{u})
UPSTREAM_BRANCH_NAME=$(git config branch.$DOCBRANCH.merge)
UPSTREAM_BRANCH_NAME=${UPSTREAM_BRANCH_NAME##refs/heads/}
DOCDIRECTORY=build/html/


if [ "$1" != "--commit" ] ; then
  echo "Assuming no-commit mode. Use '${0} --commit' to commit."
  DRY_RUN=1
else
  DRY_RUN=0
fi


# check, if index is empty
if ! git diff-index --cached --quiet --ignore-submodules HEAD ; then
  echo "Fatal: cannot work with indexed files!"
  exit 1
fi

if ! git rev-parse $DOCBRANCH &> /dev/null ; then
  echo "Fatal: no local branch 'gh-pages exists!'"
  exit 2
fi

if [ -z $UPSTREAM ] ; then
  echo "Fatal: '$DOCBRANCH' does not have a remote branch!'"
  exit 3
fi

if [ $(git rev-parse $DOCBRANCH) != $(git rev-parse $UPSTREAM_BRANCH) ] ; then
  echo "Fatal: local branch '$DOCBRANCH' and "\
    "remote branch '$UPSTREAM_BRANCH' are out of sync!"
  echo "Please consider pushing to the remote repository (or delete some commits there)."
  echo "git push $UPSTREAM $DOCBRANCH:$UPSTREAM_BRANCH_NAME"
  exit 4
fi


# get the 'git describe' output
git_describe=$(git describe)

# make the documentation, hope it doesn't fail
echo "Generating doc from $git_describe"
make clean
if ! make html; then
  echo "Fatal: 'make'ing the docs failed cannot commit!"
  exit 5
fi

if [ $DRY_RUN -eq 1 ] ; then
  exit 0
fi

# Add a .nojekyll file
# This prevents the GitHub jekyll website generator from running
touch $DOCDIRECTORY".nojekyll"

# Adding the doc files to the index
git add -f $DOCDIRECTORY

# writing a tree using the current index
tree=$(git write-tree --prefix=build/html/)

# we’ll have a commit
commit=$(echo "DOC: Sphinx generated doc from $git_describe" | git commit-tree $tree -p $DOCBRANCH)

# move the branch to the commit we made, i.e. one up
git update-ref refs/heads/$DOCBRANCH $commit

# clean index
git reset HEAD

# try to checkout what we’ve done – does not matter much, if it fails
# it is purely informative
git checkout $DOCBRANCH

# print the commit message
git log -1 --oneline

echo "Committing succeeded. Now push to your remote repository:"
echo "git push $UPSTREAM $DOCBRANCH:$UPSTREAM_BRANCH_NAME"



