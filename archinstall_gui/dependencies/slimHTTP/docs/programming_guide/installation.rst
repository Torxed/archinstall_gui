Installation
============

.. note:: These instructions apply to slimHTTP |version|.

slimHTTP is a pure python library, so no special steps are required for
installation. You can install it in a variety of ways described below though for your convenience.

Using `pip`
-----------

.. code-block:: sh

    pip install slimHTTP

Clone using `git`
-----------------

.. code-block:: sh

    git clone https://github.com/Torxed/slimHTTP.git

But most likely you'll want to `submodule <https://git-scm.com/book/en/v2/Git-Tools-Submodules>`_ this in a project.
To do that, I would recommend not following master as it's actively developed.
Any release/tag should be good enough for production.

.. code-block:: sh

    cd project/dependencies
    git submodule add -b v1.0 https://github.com/Torxed/slimHTTP.git

Which would follow the stable release branch of `v1.0` where tests *should* be done before release.

Manually unpacking source
-------------------------

The source code archives *(including git)* include examples. Archives are
`available on Github <https://github.com/Torxed/slimHTTP/releases/>`_:

.. code-block:: sh

    unzip slimHTTP-x.x.x.zip
    cd slimHTTP-x.x.x
    python examples/http_server.py