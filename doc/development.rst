Developer information
=====================

Publishing the documentation
----------------------------

The documentation is built using `Sphinx`_ and published on github. In order to make the publishing process as easy as possible, we have included a shell script ``./commit-doc-tree.sh`` which automatically builds the documentation and creates a commit in a dedicated branch containing only the relevant data.

In order to use the script, we need to add the documentation repository (`github.com/xdapy/xdapy.github.com`_) to our local *xdapy* repository::

    $ git remote add github-docs git@github.com:xdapy/xdapy.github.com.git
    $ git checkout --track -b gh-pages github-docs/master

It is important to understand that we use a different name for our local branch. (For obvious reasons, we cannot not use the name `master`.) Next, we should ensure that we automatically push to the correct branch::

    $ git config remote.github-docs.push gh-pages:master

If we skip this step, we have to remember to always say ``git push github-docs gh-pages:master`` when pushing.

Now we are ready to run the script::

    $ ./commit-doc-tree.sh --commit

(If we leave out the ``--commit`` option, the script does a dry run and only builds the documentation without committing it.)

If all goes well, we get the following message::

    88afc9f DOC: Sphinx generated doc from master-001-g2d6557b
    Committing succeeded. Now push to your remote repository:
    git push github-docs gh-pages:master

Therefore, all that is left to do is::

    git push github-docs gh-pages:master

(Or simply ``git push``, if we set the config option correctly.)

.. _Sphinx: http://sphinx.pocoo.org/
.. _github.com/xdapy/xdapy.github.com: https://github.com/xdapy/xdapy.github.com


Commit Markers
--------------

Commits should be marked. Declare both functionality and area.

Functionality Markers
+++++++++++++++++++++

:``BF`` or ``FIX``: bug fix
:``RF``: refactoring
:``NF``: new feature
:``ENH``: enhancement of an existing feature/facility
:``BW``: addresses backward-compatibility
:``OPT``: optimization
:``BK``: breaks something and/or tests fail
:``FO``: code formatting (adding spaces etc.)
:``PL``: making pylint happier

Code Area Markers
+++++++++++++++++

:``DOC``: documentation
:``UT``: unit tests
:``BLD``: build-system, setup.py
:``GIT``: repository mods, e.g. .gitconfig .gitattributes

Example
+++++++

``DOC/ENH: add initial README.md``


