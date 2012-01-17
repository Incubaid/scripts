=======================
Jenkins Utility Scripts
=======================

create_jobs.py
==============
This script can be used in a Hudson_/Jenkins_ `Continuous Integration`_ setup
to automatically create jobs whenever a new feature- or version-branch is
created in a project Git_ repository.

The script can be used from within the CI server (using periodical builds), so
no external tools are required.

The script depends on an ElementTree implementation and the Autojenkins_
package (which you could install in a VirtualEnv_ environment).

For every project you want to track, create a CI job called
"*_projectname-template*" (e.g. "*_baardskeerder-template*"), with correct VCS
configuration and including all required build steps. This project should be
*disabled* (check the *Disable Build* box).

Once this template is created, the script should be executed periodically
(using a CI job, a cron system,...). Here's how to call it::

    python create_jobs.py projectname git://myserver/projectname.git

When not executing as a CI job, you should also pass the URL of your CI
service using the *--address* argument. If the CI service requires
authentication, use *-u* and *-p* to pass a valid username and password.

Call the script multiple times if you want to track multiple projects.

The created jobs will be called "*projectname-branchname*". The script will
list the branches available on the Git server, and create jobs based on the
project template for every branch with no corresponding job.

.. tip::
    It's possible to select projects to be displayed in a view (one of the tabs
    displayed on the homepage of your CI service) using regular expressions.
    Consider creating a view for every project, using "*.\ *projectname.\ **" as
    regex to select jobs to be included in the view.

TODO
----
A potential improvement to te script would be to list all existing jobs on the
CI server matching the template name pattern, retrieve the Git repository URI
configured in this template, and use this to list remote branches. This way a
single execution of the script would create jobs for all tracked projects.

.. _Hudson: http://hudson-ci.org
.. _Jenkins: http://jenkins-ci.org
.. _Continuous Integration: http://en.wikipedia.org/wiki/Continuous_integration
.. _Git: http://git-scm.com
.. _Autojenkins: http://pypi.python.org/pypi/autojenkins
.. _VirtualEnv: http://pypi.python.org/pypi/virtualenv
